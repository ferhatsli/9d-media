# Soru Cozucu (Windows)

Kisayol tusuna (varsayilan `1`) basinca ekran goruntusu alir, Claude'a gonderir, cevabi Telegram ile telefona yollar.

## Kurulum (5 dakika)

1. **Telegram bot:** Telegram'da `@BotFather`'a yaz -> `/newbot` -> isim ver -> verdigi **token**'i kopyala.
   Sonra kendi botunu ac ve `/start` yaz (chat_id otomatik bulunur).
2. **Claude API anahtari:** https://console.anthropic.com -> API Keys -> Create Key.
3. **Programi indir:** Bu deponun *Releases* sayfasindan `SoruCozucu.exe`'yi indir, bir klasore koy, cift tikla.
   (Windows "taninmayan uygulama" derse: *Ek bilgi* -> *Yine de calistir*.)
4. Ilk acilista `config.json` acilir. `anthropic_api_key` ve `telegram_bot_token` alanlarini doldur, kaydet.

## Kullanim

- `1` tusu ya da tray ikonuna sol tik -> ekran cekilir, telefona once "cozuluyor" sonra cevap gelir.
- Ikon rengi: mavi = hazir, turuncu = cozuluyor, kirmizi = hata (`soru-cozucu.log`'a bak).
- Sag tik -> Ayarlar / Cikis.

## Ayarlar (`config.json`)

| Alan | Aciklama |
|---|---|
| `hotkey` | Kisayol tusu. Ornek: `"1"`, `"f8"`, `"ctrl+shift+s"`. Degistirdikten sonra sag tik -> *Ayarlari yenile*. |
| `model` | `claude-opus-5-5` (varsayilan, en iyi). Daha hizli/ucuz: `claude-sonnet-5-5`. |
| `effort` | `low` (en hizli), `medium`, `high` (en dikkatli). |
| `monitor` | Hangi ekran: `1` ana ekran, `2` ikinci ekran, `0` tum ekranlar. |
| `send_screenshot_to_telegram` | `true` ise ekran goruntusu de telefona gelir. |
| `prompt` | Modele verilen talimat. |
