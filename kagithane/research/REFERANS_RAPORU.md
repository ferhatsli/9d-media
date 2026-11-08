# Kâğıthane Satılık İşyeri: Referans Analizi (Apify)

Tarih: 2026-11-08 · Kaynak: Apify API (Instagram, TikTok, YouTube) · Maliyet: **$1,28** (FREE plan, aylık $5 limit)

## 1. Yöntem

| Platform | Actor | Sorgu | Sonuç |
|---|---|---|---|
| Instagram | `apify/instagram-hashtag-scraper` (reels) | #satılıkişyeri #satılıkimalathane #satılıkofis #ticarigayrimenkul #satılıkdepo #commercialrealestate #warehouseforsale #industrialrealestate (her biri 25) | 200 reel |
| TikTok | `clockworks/tiktok-scraper` | "satılık işyeri", "satılık imalathane", "satılık depo", "commercial real estate tour", "warehouse for sale tour", "office building for sale" (her biri 20) | 120 video |
| YouTube | `streamers/youtube-scraper` | "satılık işyeri tanıtım", "satılık imalathane", "commercial property tour", "warehouse for sale video tour" | 60 shorts + 20 video |

- 400 içerikten **244 kısa video gerçek ilan/tur** olarak ayıklandı. Eğitim, mizah, ürün satışı ve "warehouse sale" indirim videoları elendi (`classify.py`).
- Bunlardan izlenmesi en yüksek **18 ilan videosu** indirildi. ffmpeg ile kesme temposu ölçüldü, kanca kareleri (0–3 sn) ve tüm videonun 12 karelik özeti tek tek incelendi. YouTube indirmeleri bot korumasına takıldı. YouTube verisi yalnız metadata düzeyinde kullanıldı.
- Tüm tablo: `references.csv` (400 satır, izlenmeye göre sıralı).

## 2. Sayılarla

**Süre ve izlenme (244 kısa ilan videosu, medyan):**

| Süre | n | Medyan izlenme |
|---|---|---|
| 0–15 sn | 39 | 3.670 |
| 15–30 sn | 44 | 2.026 |
| 30–45 sn | 42 | 1.332 |
| 45–60 sn | 49 | 1.962 |
| 60–90 sn | 48 | 4.835 |
| 90+ sn | 22 | 19.001* |

\* 90+ sn grubunu birkaç büyük yabancı hesap çekiyor; tek başına güvenilir bir sinyal sayılmamalı. Sinyal **U şeklinde**: ya çok kısa (≤15 sn, tek mesaj) ya da tam tur (60–90 sn). 30–45 sn aralığı en zayıf grup.

- **Format:** %88 dikey 9:16. TR ilanlarında medyan süre 41 sn, medyan izlenme ~1.000 (EN: ~8.000). TR pazarında kanca belirleyici.
- **Ses:** IG ilanlarının %74'ü, TikTok'takilerin neredeyse tamamı **orijinal ses** kullanıyor (konuşma veya seslendirme). Trend müzik nadir.
- **Tempo:** İyi performans gösteren "tur" videolarında ortalama çekim süresi **2,5–3,3 sn**, medyan 1,6–2,7 sn (05, 14, 16). Konuşmacılı videolar 6–15 sn'lik uzun planlar kullanıyor. (Sahne algılama, benzer iç mekân geçişlerini kaçırdığı için bu değerler alt sınırdır.)

**TR ilan açıklamalarında geçen bilgiler (n=159):**

| Bilgi | Oran |
|---|---|
| m² | %47 |
| Telefon | %38 |
| Konum (📍, mahalle/cadde) | %31 |
| Emoji madde listesi | %25 |
| Fiyat | %18 |
| Tavan yüksekliği | %16 |
| Elektrik/kW | %15 |
| EİDS/yetki no | %11 |
| **Yükleme/tır/kepenk** | **%8** |
| **Köşe başı** | **%2** |

→ **Farklılaşma fırsatı:** "Köşe başı" ve "kapıdan yükleme" neredeyse hiç kullanılmıyor. Konumlandırmamız tam bu boşluğa oturuyor.

**En sık TR hashtag'ler:** #satılıkofis #satılıkişyeri #satılıkdepo #satılık #satılıkfabrika #emlak #gayrimenkul #satılıkimalathane #ticarigayrimenkul #satılıkdükkan #yatırım #sanayi #satılıkbina

## 3. Kanca kalıpları (ilk 0–3 sn)

18 videonun 16'sında **ilk karede ekranda metin var**. İşe yarayan 6 kalıp:

| # | Kalıp | Referans (izlenme) | Bize uygunluğu |
|---|---|---|---|
| K1 | **Rakam ilk karede:** üst/alt siyah bantta "For Sale · 20 Acre · Rental · Demand" kartı, ortada görüntü | 02 the.auren.group (2,05M), 12 hedef100insaat (115K, "BU FİYATA DÜKKAN YOK!! 1.300.000₺") | ✅ Emlakçı verisi gelince (m², fiyat gösterilecekse) |
| K2 | **Binada vurgu çizgisi:** sarı kontur ile satılık bölümü işaretleme + sarı hap etiketler ("Bim kiracılı · Kirası 240.000 TL") | 04 tapukur_com (1,13M) | ✅✅ **Köşe + 3 cephe**yi göstermenin en net yolu |
| K3 | **Konum pini + etiket:** havadan görüntüde bölge adı → pin → "SATILIK FABRİKA" çağrı kutusu | 05 kwgulcin (410K) | ✅ Drone yok; foto 7778–7780 + animasyonlu pin |
| K4 | **Kapıdan içeri push-in:** açık sanayi kapısından içeri yürüyerek giriş + "Let me show you…" altyazısı | 08 tommy_smalls79 (186K) | ✅✅ Storyboard A açılışıyla birebir aynı (foto 7785 kepenk) |
| K5 | **Merak/POV:** ilan ekranı kaydı + "SATILIK: 635 BİN TL" etiketi + "Bugün … geziyoruz" | 03 cemlikvlg (1,6M, içerik üreticisi) | ⚠️ Kurumsal tona uymaz; yalnız "soru" cümlesi alınabilir |
| K6 | **Sunucu + kelime kelime altyazı / kinetik tipografi** | 06, 13, 14, 15, 19 | ❌ Yüz kuralı nedeniyle sunucu yok → TR seslendirme + kelime kelime altyazıya çevrilmeli |

## 4. Gövde yapısı (en iyi analog: 05 kwgulcin, "Satılık Fabrika", 410K)

Akış: bölge etiketi → pin → **üstten arsa konturu "6000 m² ARSA ALANI"** → mesafe kartları ("Torbalı OSB 25 km", "Kemalpaşa OSB 50 km") → iç mekân + **teknik etiketler ekrana sabitlenmiş** ("11 m YÜKSEKLİK", "1000 kW Elektrik") → kapanış: "TEK YETKİLİ + telefon".

Diğer gözlemler:
- **Teknik değer görüntünün üstüne yapışık** (05, 17: "10,000 sq ft · 11.5 ft clear · 3-phase"). Ayrı bilgi kartından daha akıcı.
- **Kalıcı alt bant:** telefon/WhatsApp tüm video boyunca altta (09, 19).
- **Kapanış kartı:** "TEK YETKİLİ", ad, telefon (05). Satış etiketi (18).
- **Fiyat kartı tam ekran** gövdenin ortasında (19: "18.000.000 TL").
- 08'de seslendirme bir hikâye anlatıyor ("en son 2019'da … sattı, şimdi fiyat …"). Altyazılar kısa ve tek satır.

## 5. Storyboard güncellemeleri

### A: Dikey 9:16 (~30 sn → **28–32 sn**, gerekirse 15 sn kısa versiyon)

| Sn | Eski | Yeni (referansa göre) |
|---|---|---|
| 0–2 | Kepenk push-in + "Kapıya kamyon yanaşan bir ofis?" | **Aynen kalır (K4).** Ek: **ilk karede** üst bantta kalıcı başlık "SATILIK · KÂĞITHANE · KÖŞE BAŞI" (K1). Soru metni büyük, iki satır. |
| 2–6 | İzometrik kesit | Önce **foto 7778/7780 üzerinde sarı kontur** (binanın tamamı) + 3 giriş oku "Üst sokak · Yan sokak · Alt sokak" (K2). Sonra izometrik kesite geçiş. "Köşe başı · 3 cephe · 2 kat". |
| 6–13 | Zemin kat ~1,5 sn kesmeler | Tempo **2–2,5 sn**'ye çıksın (referans ortalaması 2,5–3,3). Her plana **yapışık etiket**: "Resepsiyon", "Köşe cumbalı ofis", "X oda". |
| 13–21 | -1 hol + "X m² kolonlu üretim alanı" | Hol genel planı **3–4 sn tutulsun** (ölçek hissi). Etiketler: "X m² · tavan Y m · Z kW" (05/17 kalıbı). "Temsili" etiketi korunur. |
| 21–26 | Harita animasyonu | **Pin + mesafe kartları** (05 kalıbı): TEM/O-1, metro, Levent/Maslak dakika. |
| 26–30 | Özet + logo + telefon + yetki no | "**TEK YETKİLİ**" + telefon + **EİDS yetki no** (ilan mevzuatı). Telefon **tüm video boyunca altta kalıcı bant** olarak da dursun. |
| Ses | Kepenk SFX + müzik | **TR seslendirme ana katman** + kelime kelime altyazı (K6'nın yüzsüz karşılığı), alçak müzik yatağı. Sessiz izleyen için tüm bilgi ekranda olmalı. |

### B: Yatay 16:9 (~70 sn)
- TR'de YouTube'daki yatay ilan videoları çok düşük izleniyor (çoğu <500). 16:9 sürüm **sahibinden/web sitesi/WhatsApp gönderimi** için düşünülmeli. Yapı korunur.
- 6–14 sn "köşeyi dönüş" sahnesine K2 konturu eklenir. Her bölüm başına alt-üçte-bir bölüm başlığı (Konum / Zemin kat / -1 kat).

### Ek teslimler
- **15 sn 4:5 feed** sürümü: K1 + K2 + -1 hol + kapanış. (≤15 sn grubu medyan izlenmede 2. sırada.)
- **Kapak görseli:** sarı konturlu köşe bina + "Üstü ofis, altı imalathane" (açıklamada nadir kullanılan iki ifade).

## 6. Açıklama (caption) şablonu

```
📍 Kâğıthane / Hamidiye: SATILIK KÖŞE BAŞI İŞYERİ
Üstü hazır ofis, altı kapıdan yüklemeli imalathane

✅ Toplam X m² (zemin X m² + -1 X m²)
✅ 3 cephe · 3 ayrı giriş
✅ Alt sokaktan kepenkli giriş (X × Y m)
✅ X oda · resepsiyon · mutfak · yönetici odası
✅ Elektrik: X kW
💰 Fiyat: X TL  (gösterilmeyecekse: "Fiyat için arayın")

📞 0 5XX XXX XX XX · TEK YETKİLİ
EİDS Yetki No: XXXXXXXXX

#satılıkişyeri #satılıkimalathane #satılıkofis #ticarigayrimenkul
#satılıkdepo #kağıthane #istanbulgayrimenkul #satılıkbina #yatırım
```

## 7. Emlakçıya ek sorular (referanslardan çıkanlar)

1. **-1 kat tavan yüksekliği** (tur videolarında standart bilgi)
2. **Kepenk ölçüsü** (genişlik × yükseklik) ve yanaşabilen araç (kamyonet / kamyon)
3. **EİDS yetki belge no**, "tek yetkili" mi?
4. **Fiyat videoda gösterilebilir mi?** (TR'de en çok izlenen ilan videolarının bir kısmı fiyatı ilk karede veriyor)
5. Mezura satış sonrası **kiracı olarak kalabilir mi?** "Kiracılı satış" yatırımcı için güçlü bir kanca (04: "Bim kiracılı, kirası 240.000 TL" → 1,13M izlenme)
6. Ulaşım mesafeleri için hangi noktalar öne çıksın (TEM, metro, Levent/Maslak)?

## 8. Dosyalar

- `references.csv`: 400 içerik; platform, kaynak, izlenme, beğeni, ER, süre, en-boy, hesap, tarih, müzik, URL, metin
- `deep/selection.json`, `deep/tempo.json`: derin analiz seti ve tempo ölçümleri
- `build_table.py`, `classify.py`, `tempo.py`: tekrar üretilebilir analiz
- Ham veri, indirilen videolar ve kare montajları (`raw/`, `deep/vid|frames|montage/`) telif ve boyut nedeniyle git dışında tutuluyor.
