# Soru Cozucu (Windows)

Kisayol tusuna (varsayilan `1`) basinca ekran goruntusu alir, AI'ya (OpenAI uyumlu API) gonderir, cevabi Telegram ile telefona yollar.

## Kurulum (5 dakika)

1. **Telegram bot:** Telegram'da `@BotFather`'a yaz -> `/newbot` -> isim ver -> verdigi **token**'i kopyala.
   Sonra kendi botunu ac ve `/start` yaz (chat_id otomatik bulunur).
2. **AI API anahtari:** Saglayicinin panelinden (varsayilan: lutheos.com) bir API anahtari olustur.
3. **Programi indir:** Bu deponun *Releases* sayfasindan `SoruCozucu.exe`'yi indir, bir klasore koy, cift tikla.
   (Windows "taninmayan uygulama" derse: *Ek bilgi* -> *Yine de calistir*.)
4. Ilk acilista `config.json` acilir. `api_key` ve `telegram_bot_token` alanlarini doldur, kaydet.

API anahtari exe'ye gomulu degildir; anahtar degisirse sadece `config.json`'daki `api_key`'i guncellemen yeterli,
programi yeniden indirmen ya da baslatman gerekmez.

## Kullanim

- `1` tusu ya da tray ikonuna sol tik -> ekran cekilir, telefona once "cozuluyor" sonra cevap gelir.
- Ikon rengi: mavi = hazir, turuncu = cozuluyor, kirmizi = hata (`soru-cozucu.log`'a bak).
- Sag tik -> Ayarlar / Cikis.

## Sorun giderme

- **`AI API anahtari gecersiz (401)`**: `config.json`'daki `api_key` yanlis, iptal edilmis ya da bakiyesi bitmis.
  Saglayici panelinden yeni anahtar alip `api_key`'e yaz.
- Eski surumden gelen gomulu anahtar otomatik olarak silinir ve yenisi istenir.

## Ayarlar (`config.json`)

| Alan | Aciklama |
|---|---|
| `api_key` | AI saglayicisinin API anahtari (zorunlu). |
| `base_url` | OpenAI uyumlu API adresi. Varsayilan `https://lutheos.com/v1`. |
| `model` | Kullanilacak model adi. |
| `telegram_bot_token` | BotFather'dan alinan token (zorunlu). |
| `telegram_chat_id` | Bos birakilirsa otomatik bulunur. |
| `hotkey` | Kisayol tusu. Ornek: `"1"`, `"f8"`, `"ctrl+shift+s"`. Degistirdikten sonra sag tik -> *Ayarlari yenile*. |
| `monitor` | Hangi ekran: `1` ana ekran, `2` ikinci ekran, `0` tum ekranlar. |
| `send_screenshot_to_telegram` | `true` ise ekran goruntusu de telefona gelir. |
| `prompt` | Modele verilen talimat. |
