"""Kâğıthane işyeri: dikey 9:16 animatik (Wiro'suz, yalnız gerçek çekimler + kod grafikleri).

Kullanım: python3 render.py <work_dir> <out.mp4>
work_dir içinde: photos/, clean/, seg/<isim>/%04d.jpg, map/dark.png, map/center.txt
"""
import sys, os, glob, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

WORK, OUT = sys.argv[1], sys.argv[2]
W, H, FPS, DUR = 1080, 1920, 30, 30.0
NAVY = (12, 22, 40); YEL = (255, 196, 0); WHITE = (255, 255, 255); AMBER = (232, 140, 40); BLUE = (64, 132, 230)
FD = "/usr/share/fonts/opentype/inter/"
def F(w, s): return ImageFont.truetype(FD + {"black": "InterDisplay-Black.otf", "bold": "Inter-Bold.otf",
                                              "semi": "Inter-SemiBold.otf", "med": "Inter-Medium.otf"}[w], s)

# ---------- yardımcılar ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return x * x * (3 - 2 * x)
def eout(x): x = clamp(x); return 1 - (1 - x) ** 3
def lerp(a, b, t): return a + (b - a) * t

_img_cache = {}
def load(path, maxh=2600):
    if path not in _img_cache:
        im = Image.open(path).convert("RGB")
        if im.height > maxh: im = im.resize((round(im.width * maxh / im.height), maxh), Image.LANCZOS)
        im = ImageEnhance.Contrast(im).enhance(1.06); im = ImageEnhance.Color(im).enhance(1.08)
        _img_cache[path] = im
    return _img_cache[path]

def kenburns(im, c0, c1, t):
    """c = (cx, cy, h) normalize (0-1) merkez ve kırpma yüksekliği; 9:16 kırpma."""
    cx, cy, ch = [lerp(a, b, ease(t)) for a, b in zip(c0, c1)]
    hh = ch * im.height; ww = hh * 9 / 16
    x0 = clamp(cx * im.width - ww / 2, 0, im.width - ww); y0 = clamp(cy * im.height - hh / 2, 0, im.height - hh)
    return im.transform((W, H), Image.EXTENT, (x0, y0, x0 + ww, y0 + hh), Image.BILINEAR), (x0, y0, ww / W)

def gray_world(im, k=0.55):
    a = np.asarray(im).astype(np.float32); m = a.reshape(-1, 3).mean(0); g = m.mean()
    a = a * (1 + k * (g / m - 1)); a = (a - 128) * 1.07 + 132
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

_seg = {}
def seg(name, t, speed=1.0):
    if name not in _seg: _seg[name] = sorted(glob.glob(f"{WORK}/seg/{name}/*.jpg"))
    fr = _seg[name]; i = min(len(fr) - 1, int(t * FPS * speed))
    return gray_world(Image.open(fr[i]).convert("RGB"))

def text_w(d, s, f): b = d.textbbox((0, 0), s, font=f); return b[2] - b[0]

def pill(d, xy, s, f, fg=NAVY, bg=YEL, pad=(26, 14), anchor="l", alpha=1.0):
    x, y = xy; tw = text_w(d, s, f); asc, desc = f.getmetrics(); th = asc
    if anchor == "c": x -= (tw + 2 * pad[0]) / 2
    if anchor == "r": x -= tw + 2 * pad[0]
    box = (x, y, x + tw + 2 * pad[0], y + th + 2 * pad[1])
    bgc = bg + (int(255 * alpha),); fgc = fg + (int(255 * alpha),)
    d.rounded_rectangle(box, radius=(th + 2 * pad[1]) // 2, fill=bgc)
    d.text((x + pad[0], y + pad[1] - 2), s, font=f, fill=fgc)
    return box

def caption(d, lines, y, t_in, t, size=78, color=WHITE, hl=None):
    """Satır satır yukarı kayarak giren büyük altyazı. hl: sarı vurgulanacak kelimeler."""
    f = F("black", size)
    for i, ln in enumerate(lines):
        p = eout((t - t_in - i * 0.12) / 0.35)
        if p <= 0: continue
        a = int(255 * p); yy = y + i * (size + 14) + (1 - p) * 40
        x = (W - text_w(d, ln, f)) / 2
        for word in ln.split(" "):
            col = YEL if hl and word.strip(".,?").lower() in hl else color
            d.text((x, yy), word, font=f, fill=col + (a,), stroke_width=6, stroke_fill=(0, 0, 0, int(a * 0.85)))
            x += text_w(d, word + " ", f)

def label(d, xy, s, t_in, t, size=44, anchor="l"):
    p = eout((t - t_in) / 0.3)
    if p <= 0: return
    x, y = xy
    pill(d, (x, y + (1 - p) * 25), s, F("bold", size), anchor=anchor, alpha=p)

def pointer(d, pt, xy, s, t_in, t, anchor="l", size=40):
    p = eout((t - t_in) / 0.35)
    if p <= 0: return
    f = F("bold", size); x, y = xy; tw = text_w(d, s, f) + 52
    bx = x if anchor == "l" else (x - tw if anchor == "r" else x - tw / 2)
    cx, cy = bx + tw / 2, y + 34
    ex, ey = lerp(cx, pt[0], p), lerp(cy, pt[1], p)
    d.line((cx, cy, ex, ey), fill=YEL + (int(255 * p),), width=5)
    r = 13 * p; d.ellipse((pt[0] - r, pt[1] - r, pt[0] + r, pt[1] + r), fill=YEL + (255,), outline=NAVY + (255,), width=4)
    pill(d, (x, y), s, f, anchor=anchor, alpha=p)

def top_band(d, t):
    p = eout(t / 0.4)
    y = 120 - (1 - p) * 60
    b = pill(d, (60, y), "SATILIK", F("black", 46), alpha=p)
    d.text((b[2] + 22, y + 12), "KÂĞITHANE · KÖŞE BAŞI", font=F("bold", 44), fill=WHITE + (int(255 * p),),
           stroke_width=4, stroke_fill=(0, 0, 0, int(160 * p)))

def bottom_band(d, t, t_in=2.2):
    p = eout((t - t_in) / 0.4)
    if p <= 0: return
    y = 1480 + (1 - p) * 40; a = int(255 * p)
    d.rounded_rectangle((60, y, W - 60, y + 92), radius=46, fill=NAVY + (int(220 * p),))
    d.ellipse((76, y + 14, 140, y + 78), fill=YEL + (a,))
    # basit telefon ikonu
    d.rounded_rectangle((97, y + 28, 119, y + 64), radius=5, outline=NAVY + (a,), width=4)
    d.text((160, y + 22), "TEK YETKİLİ  ·  0 5XX XXX XX XX", font=F("bold", 42), fill=WHITE + (a,))

def vignette():
    v = Image.new("L", (W, H), 0); vd = ImageDraw.Draw(v)
    for i in range(0, 260, 4): vd.rectangle((0, i, W, i + 4), fill=int(150 * (1 - i / 260) ** 2))
    for i in range(0, 520, 4): vd.rectangle((0, H - i - 4, W, H - i), fill=int(170 * (1 - i / 520) ** 1.6))
    return v
VIG = vignette()
def darken_edges(im):
    black = Image.new("RGB", (W, H), (0, 0, 0)); return Image.composite(black, im, VIG)

# ---------- sahneler ----------
def sc_hook(t, T):  # 0-2.2 kepenk push-in (foto 7785, tabela silinmiş)
    im = load(f"{WORK}/clean/7785.jpg")
    fr, _ = kenburns(im, (0.20, 0.52, 0.98), (0.215, 0.60, 0.60), t / T)
    return fr, lambda d: caption(d, ["Kapısına kamyon", "yanaşan bir ofis?"], 760, 0.15, t, size=96, hl={"kamyon"})

# 7778 üzerinde satılık katların bandı (orijinal 4032x3024 koordinatı; 1400 ölçeğinde ölçülüp 2.88 ile çarpıldı)
BAND = [(468, 488), (600, 462), (672, 446), (790, 446), (860, 460), (1100, 528), (1100, 588), (830, 604), (610, 616), (470, 600)]
def sc_corner(t, T):  # bina köşesi + sarı kontur + giriş etiketleri
    im = load(f"{WORK}/clean/7778.jpg")
    fr, (x0, y0, s) = kenburns(im, (0.53, 0.50, 1.0), (0.53, 0.53, 0.86), t / T)
    k = im.width / 4032 * 2.88
    pts = [(((x * k) - x0) / s, ((y * k) - y0) / s) for x, y in BAND]
    sp = lambda x, y: (((x * k) - x0) / s, ((y * k) - y0) / s)
    def ov(d):
        p = ease((t - 0.25) / 0.9)
        if p > 0:
            n = len(pts); seglen = p * n
            path = [pts[0]]
            for i in range(int(seglen)):
                path.append(pts[(i + 1) % n])
            fi = seglen - int(seglen)
            if int(seglen) < n:
                a, b = pts[int(seglen) % n], pts[(int(seglen) + 1) % n]; path.append((lerp(a[0], b[0], fi), lerp(a[1], b[1], fi)))
            if p >= 1: d.polygon(pts, fill=YEL + (50,))
            d.line(path, fill=YEL + (255,), width=9, joint="curve")
        pointer(d, sp(520, 560), (70, 1180), "Alt sokak · kepenk → -1", 1.05, t)
        pointer(d, sp(940, 555), (W - 70, 1040), "Üst sokak · vitrin → zemin", 1.25, t, anchor="r")
        pointer(d, sp(672, 505), (W / 2, 470), "Köşe · cumbalı ofis", 1.45, t, anchor="c")
        caption(d, ["Köşe başı · 3 cephe"], 1320, 0.35, t, size=84, hl={"3"})
    return fr, ov

def iso(x, y, z, ox=540, oy=900, u=82):
    return (ox + (x - y) * u * 0.866, oy + (x + y) * u * 0.5 - z * u)

def sc_section(t, T):  # izometrik kesit
    bg = Image.new("RGB", (W, H), NAVY); d0 = ImageDraw.Draw(bg)
    for i in range(0, H, 6): d0.line((0, i, W, i), fill=(14 + i // 120, 26 + i // 110, 46 + i // 90))
    def ov(d):
        sep = 0.9 * ease((t - 0.9) / 0.6)
        def box(z0, h, top, left, right, p):
            if p <= 0: return
            h = h * eout(p); X, Y = 5.2, 3.6
            P = lambda x, y, z: iso(x, y, z + z0)
            al = int(255 * clamp(p * 2))
            d.polygon([P(0, Y, 0), P(X, Y, 0), P(X, Y, h), P(0, Y, h)], fill=left + (al,))
            d.polygon([P(X, 0, 0), P(X, Y, 0), P(X, Y, h), P(X, 0, h)], fill=right + (al,))
            d.polygon([P(0, 0, h), P(X, 0, h), P(X, Y, h), P(0, Y, h)], fill=top + (al,))
            for e in [(P(0, 0, h), P(X, 0, h)), (P(X, 0, h), P(X, Y, h)), (P(X, Y, h), P(0, Y, h)), (P(0, Y, h), P(0, 0, h)),
                      (P(X, Y, 0), P(X, Y, h)), (P(0, Y, 0), P(0, Y, h)), (P(X, 0, 0), P(X, 0, h))]:
                d.line(e, fill=(255, 255, 255, al // 2), width=3)
        box(-1.6, 1.5, (250, 178, 90), (196, 110, 30), (222, 132, 44), (t - 0.1) / 0.5)          # -1 imalathane
        box(0.05 + sep, 1.5, (120, 172, 245), (40, 96, 190), (58, 120, 214), (t - 0.45) / 0.5)    # zemin ofis
        label(d, (70, 600 - sep * 82), "ZEMİN · Hazır ofis katı", 1.3, t, size=44)
        label(d, (W - 70, 1330), "-1 · İmalathane", 1.5, t, size=44, anchor="r")
        caption(d, ["Üstü ofis,", "altı imalathane."], 270, 0.3, t, size=88, hl={"ofis,", "imalathane."})
    return bg, ov

def photo_shot(path, c0, c1, lab):
    def f(t, T):
        fr, _ = kenburns(load(path), c0, c1, t / T)
        return fr, lambda d: label(d, (70, 1290), lab, 0.1, t)
    return f

def video_shot(name, lab, zoom=1.0, speed=1.0):
    def f(t, T):
        fr = seg(name, t, speed)
        if zoom != 1.0:
            z = lerp(1.0, zoom, ease(t / T)); w, h = W / z, H / z
            fr = fr.transform((W, H), Image.EXTENT, ((W - w) / 2, (H - h) / 2, (W + w) / 2, (H + h) / 2), Image.BILINEAR)
        return fr, (lambda d: label(d, (70, 1290), lab, 0.1, t)) if lab else (lambda d: None)
    return f

def with_caption(shot, lines, t_in, hl=None, size=84, y=1110):
    def f(t, T):
        fr, ov = shot(t, T)
        def o(d): ov(d); caption(d, lines, y, t_in, t, size=size, hl=hl)
        return fr, o
    return f

def sc_beforeafter(t, T):  # temsili boş hâl: AI aşamasında üretilecek
    fr = seg("hol", 2.0)
    right = ImageEnhance.Color(fr.filter(ImageFilter.GaussianBlur(18))).enhance(0.2)
    right = ImageEnhance.Brightness(right).enhance(0.75)
    x = int(lerp(W * 0.92, W * 0.42, ease((t - 0.2) / 1.0)))
    out = fr.copy(); out.paste(right.crop((x, 0, W, H)), (x, 0))
    def ov(d):
        d.line((x, 300, x, 1450), fill=WHITE + (255,), width=6)
        d.ellipse((x - 34, 840, x + 34, 908), fill=WHITE + (255,))
        d.polygon([(x - 18, 874), (x - 6, 862), (x - 6, 886)], fill=NAVY + (255,)); d.polygon([(x + 18, 874), (x + 6, 862), (x + 6, 886)], fill=NAVY + (255,))
        pill(d, (70, 330), "ŞU AN", F("bold", 38), fg=WHITE, bg=(30, 30, 30))
        if x < W - 300:
            pill(d, (W - 70, 330), "BOŞ HÂLİ", F("bold", 38), anchor="r")
            f = F("semi", 34)
            for i, s in enumerate(["Temsili görsel", "AI aşamasında", "üretilecek"]):
                d.text((x + (W - x - text_w(d, s, f)) / 2, 980 + i * 46), s, font=f, fill=WHITE + (230,))
        pill(d, (W - 70, 1385), "Temsili görseldir", F("semi", 30), fg=WHITE, bg=(0, 0, 0), anchor="r")
    return out, ov

MAP = None
def sc_map(t, T):
    global MAP
    if MAP is None:
        MAP = (Image.open(f"{WORK}/map/dark.png").convert("RGB"), [float(v) for v in open(f"{WORK}/map/center.txt").read().split()])
    im, (cx, cy) = MAP
    z = lerp(1.25, 1.0, eout(t / T)); w, h = W / z, H / z
    ox, oy = cx - w / 2, cy - h / 2 - 120 / z
    fr = im.transform((W, H), Image.EXTENT, (ox, oy, ox + w, oy + h), Image.BILINEAR)
    px, py = (cx - ox) * z, (cy - oy) * z
    def ov(d):
        # TEM (2. Çevre Yolu) ~ haritada kuzeyde: dikey kesik çizgi + etiket
        tem_y = (cy - 450 - oy) * z
        p = ease((t - 0.9) / 0.6)
        if p > 0:
            for yy in range(int(py - 30), int(lerp(py - 30, tem_y + 40, p)), -26):
                d.line((px, yy, px, yy - 13), fill=YEL + (230,), width=6)
        label(d, (px, tem_y - 30), "TEM / O-2 · ~800 m", 1.4, t, size=40, anchor="c")
        dp = eout((t - 0.2) / 0.45)
        if dp > 0:
            r = 30 + 60 * ((t * 1.2) % 1.0)
            d.ellipse((px - r, py - r, px + r, py + r), outline=YEL + (int(200 * (1 - (r - 30) / 60)),), width=5)
            yy = py - (1 - dp) * 200
            d.ellipse((px - 26, yy - 26, px + 26, yy + 26), fill=YEL + (255,), outline=NAVY + (255,), width=6)
        label(d, (px, py + 50), "Hamidiye Mah. · Kâğıthane", 0.5, t, size=42, anchor="c")
        cards = ["Metro · X dk", "Levent / Maslak · X dk", "Merkez · X dk"]
        for i, s in enumerate(cards):
            label(d, (70, 1240 + i * 76), s, 1.0 + i * 0.15, t, size=36)
        d.text((W - 360, 1880), "© OpenStreetMap katkıcıları", font=F("med", 22), fill=(200, 200, 210, 200))
    return fr, ov

def sc_end(t, T):
    im = load(f"{WORK}/clean/7778.jpg")
    fr, _ = kenburns(im, (0.5, 0.5, 0.9), (0.5, 0.5, 0.8), t / T)
    fr = ImageEnhance.Brightness(fr.filter(ImageFilter.GaussianBlur(14))).enhance(0.35)
    def ov(d):
        p = eout(t / 0.4)
        pill(d, (W / 2, 470 - (1 - p) * 30), "SATILIK", F("black", 72), anchor="c", pad=(44, 20), alpha=p)
        caption(d, ["Kâğıthane'de", "köşe başı işyeri"], 650, 0.2, t, size=92)
        caption(d, ["Üstü hazır ofis", "Altı kapıdan yüklemeli imalathane"], 900, 0.5, t, size=50, color=(220, 228, 240))
        q = eout((t - 0.9) / 0.4)
        if q > 0:
            a = int(255 * q)
            d.rounded_rectangle((90, 1130, W - 90, 1370), radius=36, fill=(255, 255, 255, int(235 * q)))
            d.text((W / 2, 1185), "TEK YETKİLİ", font=F("bold", 40), fill=NAVY + (a,), anchor="mm")
            d.text((W / 2, 1255), "0 5XX XXX XX XX", font=F("black", 66), fill=NAVY + (a,), anchor="mm")
            d.text((W / 2, 1325), "EİDS Yetki No: XXXXXXXXXX", font=F("semi", 32), fill=(70, 80, 100, a), anchor="mm")
            d.text((W / 2, 1460), "[ EMLAK OFİSİ LOGOSU ]", font=F("bold", 34), fill=(255, 255, 255, int(160 * q)), anchor="mm")
    return fr, ov

# ---------- zaman çizelgesi ----------
TL = [
    (2.2, sc_hook, "cut"),
    (2.6, sc_corner, "flash"),
    (2.4, sc_section, "cut"),
    (2.0, with_caption(photo_shot(f"{WORK}/photos/IMG_7765.jpg", (0.42, 0.55, 1.0), (0.38, 0.56, 0.86), "Resepsiyon"), ["Hazır ofis katı"], 0.2, hl={"hazır"}), "cut"),
    (1.6, photo_shot(f"{WORK}/clean/7771.jpg", (0.5, 0.5, 1.0), (0.5, 0.48, 0.72), "Koridorlar"), "cut"),
    (2.2, video_shot("cumba", "Köşe cumbalı ofis"), "cut"),
    (1.4, video_shot("ofis", "X oda · laminat zemin"), "cut"),
    (1.2, photo_shot(f"{WORK}/photos/IMG_7767.jpg", (0.45, 0.5, 1.0), (0.48, 0.52, 0.85), "Mutfak"), "cut"),
    (1.7, with_caption(video_shot("walkin", "Alt sokak · kepenkli giriş"), ["Alt kat:", "kapıdan yükleme"], 0.15, hl={"yükleme"}), "flash"),
    (3.0, with_caption(video_shot("hol", "Kolonlu üretim holü · X m²", zoom=1.06), ["X m² üretim alanı"], 0.3, hl={"x", "m²"}), "cut"),
    (1.6, video_shot("dikis", "Dikiş / döşeme bölümü"), "cut"),
    (2.0, sc_beforeafter, "cut"),
    (2.8, sc_map, "flash"),
    (3.3, sc_end, "cut"),
]
total = sum(x[0] for x in TL); assert abs(total - DUR) < 0.05, total

def render_frame(gt):
    t0 = 0.0
    for dur, fn, trans in TL:
        if gt < t0 + dur or (dur, fn, trans) == TL[-1]:
            t = gt - t0; base, ov = fn(t, dur)
            base = darken_edges(base.convert("RGB"))
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer); ov(d)
            if gt < 26.7: top_band(d, gt); bottom_band(d, gt)
            return Image.alpha_composite(base.convert("RGBA"), layer).convert("RGB")
        t0 += dur

if os.environ.get("STILLS"):
    os.makedirs(OUT, exist_ok=True)
    for s in os.environ["STILLS"].split(","):
        render_frame(float(s)).save(f"{OUT}/still_{float(s):05.2f}.jpg", quality=85)
    sys.exit(0)

cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
       "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", OUT]
pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
t0 = 0.0; prev_last = None
for dur, fn, trans in TL:
    nfr = round(dur * FPS)
    for i in range(nfr):
        t = i / FPS
        base, ov = fn(t, dur)
        base = darken_edges(base.convert("RGB"))
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
        ov(d)
        gt = t0 + t
        if gt < 26.7:
            top_band(d, gt); bottom_band(d, gt)
        frame = Image.alpha_composite(base.convert("RGBA"), layer).convert("RGB")
        if trans == "flash" and i < 4:
            frame = Image.blend(frame, Image.new("RGB", (W, H), WHITE), 0.55 * (1 - i / 4))
        pr.stdin.write(frame.tobytes())
    t0 += dur
    print(f"{t0:5.1f}s  {fn.__name__ if hasattr(fn, '__name__') else 'shot'}", flush=True)
pr.stdin.close(); pr.wait()
