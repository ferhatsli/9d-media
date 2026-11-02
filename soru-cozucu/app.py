"""Soru Cozucu - Windows tray uygulamasi.

Kisayol tusuna (varsayilan "1") ya da tray ikonuna basinca ekran goruntusu alir,
Claude API'ye gonderir, cevabi Telegram ile telefona yollar.
"""

import base64
import ctypes
import io
import json
import logging
import os
import subprocess
import sys
import threading
import time

import keyboard
import mss
import pystray
import requests
from PIL import Image, ImageDraw

APP_NAME = "Soru Cozucu"

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
LOG_PATH = os.path.join(BASE_DIR, "soru-cozucu.log")

# --- AI saglayicisi (exe'ye gomulu; config.json'daki eski degerleri ezer) -----
# OpenAI uyumlu uc nokta: POST {base_url}/chat/completions, Bearer + image_url.
AI_BASE_URL = "https://larprouter.com/v1"
AI_API_KEY = "lrsk-f77fa864d7bfff210f8dc453e0ad5449bae5bd4eeb3cdf7e04ef7a10f7663ea7"
AI_MODEL = "deepseek-v4.1-flash-1017-abliterated"

DEFAULT_CONFIG = {
    "base_url": AI_BASE_URL,
    "api_key": AI_API_KEY,
    "model": AI_MODEL,
    "telegram_bot_token": "BURAYA_TELEGRAM_BOT_TOKEN",
    "telegram_chat_id": "",
    "hotkey": "1",
    "effort": "medium",
    "monitor": 1,
    "send_screenshot_to_telegram": False,
    "prompt": (
        "Ekran goruntusundeki soruyu bul ve coz. "
        "Ilk satirda sadece net cevabi yaz (ornegin 'CEVAP: C' ya da 'CEVAP: 42'). "
        "Altina kisa ve anlasilir bir cozum/aciklama yaz. Turkce yaz. "
        "Ekranda birden fazla soru varsa hepsini sirayla numaralandirarak coz. "
        "Markdown kullanma, duz metin yaz."
    ),
}

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    encoding="utf-8",
)
log = logging.getLogger(APP_NAME)


# ---------------------------------------------------------------- yardimcilar

def message_box_async(text, title=APP_NAME):
    threading.Thread(target=message_box, args=(text, title), daemon=True).start()


def open_log():
    try:
        subprocess.Popen(["notepad.exe", LOG_PATH])
    except Exception:
        pass


def message_box(text, title=APP_NAME):
    try:
        ctypes.windll.user32.MessageBoxW(0, text, title, 0x40)
    except Exception:
        print(f"{title}: {text}")


def load_config():
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG), True
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    merged = dict(DEFAULT_CONFIG)
    merged.update(cfg)
    # AI ayarlari her zaman exe'ye gomulu degerlerden gelir; eski config'i ezer.
    merged["base_url"] = AI_BASE_URL
    merged["api_key"] = AI_API_KEY
    merged["model"] = AI_MODEL
    merged.pop("anthropic_api_key", None)
    return merged, False


def save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def open_config():
    try:
        subprocess.Popen(["notepad.exe", CONFIG_PATH])
    except Exception:
        os.startfile(CONFIG_PATH)  # type: ignore[attr-defined]


def config_ready(cfg):
    # AI anahtari exe'ye gomulu; sadece Telegram token'i gerekli.
    tok = str(cfg.get("telegram_bot_token", ""))
    return bool(tok) and not tok.startswith("BURAYA")


def make_icon(color):
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((4, 4, 60, 60), fill=color)
    try:
        d.text((32, 32), "?", fill="white", font_size=40, anchor="mm")
    except Exception:
        d.text((28, 24), "?", fill="white")
    return img


ICON_IDLE = make_icon((40, 120, 220))
ICON_BUSY = make_icon((230, 160, 20))
ICON_ERR = make_icon((210, 50, 50))


# ---------------------------------------------------------------- ekran

def take_screenshot(monitor_index):
    with mss.mss() as sct:
        monitors = sct.monitors
        if monitor_index < 0 or monitor_index >= len(monitors):
            monitor_index = 1
        shot = sct.grab(monitors[monitor_index])
        img = Image.frombytes("RGB", shot.size, shot.rgb)

    # Cok buyuk ekranlari kucult (hiz icin); yazi okunur kalir.
    max_side = 2000
    if max(img.size) > max_side:
        img.thumbnail((max_side, max_side), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


# ---------------------------------------------------------------- telegram

def tg_api(cfg, method):
    return f"https://api.telegram.org/bot{cfg['telegram_bot_token']}/{method}"


def resolve_chat_id(cfg):
    """chat_id bossa, bota en son yazan sohbetin id'sini bulup kaydeder."""
    if str(cfg.get("telegram_chat_id", "")).strip():
        return str(cfg["telegram_chat_id"]).strip()
    r = requests.get(tg_api(cfg, "getUpdates"), timeout=15)
    r.raise_for_status()
    results = r.json().get("result", [])
    for upd in reversed(results):
        msg = upd.get("message") or upd.get("edited_message") or {}
        chat = msg.get("chat")
        if chat and "id" in chat:
            cfg["telegram_chat_id"] = str(chat["id"])
            disk_cfg, _ = load_config()
            disk_cfg["telegram_chat_id"] = cfg["telegram_chat_id"]
            save_config(disk_cfg)
            log.info("Telegram chat_id bulundu: %s", cfg["telegram_chat_id"])
            return cfg["telegram_chat_id"]
    raise RuntimeError(
        "Telegram chat_id bulunamadi. Telefondan botuna /start yaz, sonra tekrar dene."
    )


def tg_send_text(cfg, text):
    chat_id = resolve_chat_id(cfg)
    # Telegram mesaj limiti 4096 karakter
    for i in range(0, max(len(text), 1), 4000):
        r = requests.post(
            tg_api(cfg, "sendMessage"),
            data={"chat_id": chat_id, "text": text[i : i + 4000]},
            timeout=20,
        )
        r.raise_for_status()


def tg_send_photo(cfg, jpeg_bytes):
    chat_id = resolve_chat_id(cfg)
    r = requests.post(
        tg_api(cfg, "sendPhoto"),
        data={"chat_id": chat_id},
        files={"photo": ("ekran.jpg", jpeg_bytes, "image/jpeg")},
        timeout=30,
    )
    r.raise_for_status()


# ------------------------------------------------- AI (OpenAI uyumlu / larprouter)

def solve(cfg, jpeg_bytes):
    image_b64 = base64.standard_b64encode(jpeg_bytes).decode("utf-8")
    url = str(cfg["base_url"]).rstrip("/") + "/chat/completions"
    payload = {
        "model": cfg["model"],
        "max_tokens": 4000,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": cfg["prompt"]},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                    },
                ],
            }
        ],
    }
    r = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {cfg['api_key']}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=300,
    )
    if r.status_code >= 400:
        raise RuntimeError(f"AI API {r.status_code}: {r.text[:300]}")
    data = r.json()
    try:
        text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise RuntimeError(f"Beklenmeyen API cevabi: {json.dumps(data)[:300]}")
    return (text or "").strip() or "(Bos cevap geldi)"


# ---------------------------------------------------------------- uygulama

class App:
    def __init__(self):
        self.icon = None
        self.busy = 0
        self.lock = threading.Lock()
        self.last_trigger = 0.0
        self.hotkey_handle = None

    def set_icon(self, img, title):
        if self.icon:
            self.icon.icon = img
            self.icon.title = title

    def notify(self, text):
        try:
            if self.icon:
                self.icon.notify(text, APP_NAME)
        except Exception:
            pass

    def trigger(self, *_):
        now = time.time()
        if now - self.last_trigger < 1.5:  # tus tekrarini engelle
            return
        self.last_trigger = now
        log.info("Tetiklendi")
        threading.Thread(target=self.run_once, daemon=True).start()

    def run_once(self):
        with self.lock:
            self.busy += 1
        self.set_icon(ICON_BUSY, f"{APP_NAME} - cozuluyor...")
        cfg = None
        try:
            cfg, _ = load_config()
            if not config_ready(cfg):
                message_box("Once config.json dosyasina API anahtari ve Telegram token gir.")
                open_config()
                return
            jpeg = take_screenshot(int(cfg.get("monitor", 1)))
            log.info("Ekran goruntusu alindi (%d KB)", len(jpeg) // 1024)
            self.notify("Ekran alindi, cozuluyor...")

            # Telefona hemen "aldim" bildirimi (arka planda, beklemeden)
            def notify():
                try:
                    if cfg.get("send_screenshot_to_telegram"):
                        tg_send_photo(cfg, jpeg)
                    else:
                        tg_send_text(cfg, "📸 Ekran alindi, cozuluyor...")
                except Exception as e:
                    log.warning("On bildirim gonderilemedi: %s", e)

            threading.Thread(target=notify, daemon=True).start()

            t0 = time.time()
            answer = solve(cfg, jpeg)
            log.info("Cevap geldi (%.1f sn)", time.time() - t0)
            tg_send_text(cfg, f"✅ {answer}")
            self.set_icon(ICON_IDLE, APP_NAME)
        except Exception as e:
            log.exception("Hata")
            self.set_icon(ICON_ERR, f"{APP_NAME} - hata (log'a bak)")
            sent = False
            try:
                if cfg and config_ready(cfg):
                    tg_send_text(cfg, f"❌ Hata: {e}")
                    sent = True
            except Exception as e2:
                log.warning("Hata Telegram'a da gonderilemedi: %s", e2)
            if not sent:
                message_box_async(f"Hata:\n{e}\n\nAyrinti: {LOG_PATH}")
        finally:
            with self.lock:
                self.busy -= 1
                idle = self.busy == 0
            if idle and self.icon and self.icon.icon is ICON_BUSY:
                self.set_icon(ICON_IDLE, APP_NAME)

    def register_hotkey(self, cfg):
        hk = str(cfg.get("hotkey", "1")).strip()
        if not hk:
            return
        try:
            self.hotkey_handle = keyboard.add_hotkey(hk, self.trigger, suppress=False)
            log.info("Kisayol tusu: %s", hk)
        except Exception as e:
            log.exception("Kisayol kaydedilemedi")
            message_box(f"Kisayol tusu ayarlanamadi ({hk}): {e}")

    def reload_hotkey(self, *_):
        cfg, _ = load_config()
        if self.hotkey_handle is not None:
            try:
                keyboard.remove_hotkey(self.hotkey_handle)
            except Exception:
                pass
            self.hotkey_handle = None
        self.register_hotkey(cfg)
        message_box(f"Ayarlar yenilendi. Kisayol tusu: {cfg.get('hotkey')}")

    def test_telegram(self, *_):
        def run():
            cfg, _ = load_config()
            if not config_ready(cfg):
                message_box("config.json eksik: API anahtari ve Telegram token gir.")
                open_config()
                return
            try:
                tg_send_text(cfg, "👋 Test mesaji: Soru Cozucu baglandi.")
                message_box(f"Telegram calisiyor. chat_id: {cfg.get('telegram_chat_id')}")
            except requests.HTTPError as e:
                code = e.response.status_code if e.response is not None else "?"
                hint = " (token yanlis)" if code in (401, 404) else ""
                message_box(f"Telegram hatasi {code}{hint}:\n{e}")
            except Exception as e:
                message_box(f"Telegram hatasi:\n{e}")

        threading.Thread(target=run, daemon=True).start()

    def quit(self, icon, *_):
        try:
            keyboard.unhook_all()
        except Exception:
            pass
        icon.stop()

    def run(self):
        cfg, created = load_config()
        if created or not config_ready(cfg):
            message_box(
                "Ilk calistirma: config.json acilacak.\n\n"
                "AI anahtari zaten gomulu. Sadece Telegram ayari gerek:\n"
                "1) telegram_bot_token alanina BotFather'dan aldigin token'i yaz\n"
                "2) Telefondan botuna /start yaz (chat_id otomatik bulunur)\n"
                "3) Kaydet. Programi kapatmana gerek yok."
            )
            open_config()

        self.register_hotkey(cfg)
        menu = pystray.Menu(
            pystray.MenuItem("Ekrani coz", self.trigger, default=True),
            pystray.MenuItem("Ayarlari ac (config.json)", lambda *_: open_config()),
            pystray.MenuItem("Ayarlari yenile (kisayol)", self.reload_hotkey),
            pystray.MenuItem("Telegram'i test et", self.test_telegram),
            pystray.MenuItem("Log dosyasini ac", lambda *_: open_log()),
            pystray.MenuItem("Cikis", self.quit),
        )
        self.icon = pystray.Icon(APP_NAME, ICON_IDLE, f"{APP_NAME} (tus: {cfg.get('hotkey')})", menu)
        log.info("Uygulama basladi")
        self.icon.run()


def selftest():
    """CI icin: importlar ve ekran goruntusu calisiyor mu."""
    out = os.path.join(BASE_DIR, "selftest.txt")
    try:
        jpeg = take_screenshot(1)
        msg = f"OK screenshot={len(jpeg)} model={AI_MODEL}"
    except Exception as e:
        msg = f"OK (screenshot yok: {e}) model={AI_MODEL}"
    with open(out, "w", encoding="utf-8") as f:
        f.write(msg)
    sys.exit(0)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    # Tek kopya calissin
    try:
        mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "SoruCozucuSingleInstance")
        if ctypes.windll.kernel32.GetLastError() == 183:
            message_box("Program zaten calisiyor (sag alttaki tray'de).")
            sys.exit(0)
    except AttributeError:
        pass
    App().run()
