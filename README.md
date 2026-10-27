# 🌟 "Assalomu aleykum xizmat" — Multi-tenant Telegram SaaS Boti

Tadbirkorlarning shaxsiy Telegram profillariga (Telegram Business orqali) ulanuvchi va ularning nomidan 24/7 rejimida professional, muloyim va aqlli avto-javob beruvchi sun'iy intellekt (Gemini 2.5 Flash) yordamchisi.

---

## 🛠 Texnologiyalar
- **Python 3.11+** (Python 3.12 tavsiya etiladi)
- **aiogram 3.x** (Telegram Business API: `business_connection`, `business_message` qo'llab-quvvatlovi bilan)
- **google-genai** (Google Gemini rasmiy SDK, `gemini-2.5-flash` modeli)
- **aiosqlite** (Asinxron SQLite3 ma'lumotlar bazasi)
- **python-dotenv** (Muhit o'zgaruvchilarini boshqarish)

---

## 📂 Loyiha tuzilmasi

```text
Assalomu aleykum xizmat/
├── config.py                 # Konfiguratsiya va muhit o'zgaruvchilari
├── database.py               # aiosqlite asinxron ma'lumotlar bazasi va CRUD funksiyalar
├── states.py                 # FSM holatlari (Onboarding, FAQ qo'shish, AI generatsiya)
├── keyboards.py              # Reply va Inline klaviaturalar
├── services/
│   ├── __init__.py
│   └── ai_service.py         # Google Gemini 2.5 Flash bilan integratsiya va System Prompt
├── handlers/
│   ├── __init__.py
│   ├── onboarding.py         # Yangi tadbirkorlar uchun FSM so'rovnomasi
│   ├── menu.py               # Asosiy menyu (FAQ boshqaruvi, AI generatsiya, profil sozlamalari)
│   └── business.py           # Telegram Business hodisalari va mijozlarga AI javob berish
├── main.py                   # Botni ishga tushiruvchi asosiy fayl
├── requirements.txt          # Kerakli Python kutubxonalari
├── .env.example              # Muhit o'zgaruvchilari namunasi
└── README.md                 # To'liq qo'llanma
```

---

## 🚀 O'rnatish va Ishga Tushirish

### 1. Loyihani yuklab olish va virtual muhit yaratish
```bash
# Loyiha papkasiga o'ting
cd "Assalomu aleykum xizmat"

# Python 3.11+ virtual muhit yaratish
python3.12 -m venv venv

# Virtual muhitni faollashtirish
source venv/bin/activate  # macOS / Linux
# yoki Windows: venv\Scripts\activate

# Kutubxonalarni o'rnatish
pip install -r requirements.txt
```

### 2. .env faylini sozlash
`.env.example` faylidan nusxa olib `.env` yarating:
```bash
cp .env.example .env
```
`.env` faylini ochib, o'zingizning kalitlaringizni kiriting:
```ini
# BotFather dan olingan Telegram Bot tokeni
BOT_TOKEN=1234567890:AAH...

# Google AI Studio dan olingan bepul Gemini API kaliti
# Kalit olish: https://aistudio.google.com/
GEMINI_API_KEY=AIzaSy...

# Ma'lumotlar bazasi fayli
DB_NAME=assalomu_xizmat.db

# Gemini modeli
GEMINI_MODEL=gemini-2.5-flash
```

---

## ⚙️ Telegram Business uchun BotFather Sozlamasi (MUHIM!)

Bot Telegram Business akkauntlariga ulana olishi uchun quyidagi qadamni bajaring:
1. Telegram'da [@BotFather](https://t.me/BotFather) ga kiring.
2. `/mybots` buyrug'ini yuboring va o'zingizning botingizni tanlang.
3. **Bot Settings** -> **Business Mode** (yoki **Telegram Business**) bo'limiga kiring.
4. **Turn on** tugmasini bosing (Business Mode faollashadi).

---

## 📱 Botning Ishlash Bosqichlari

### 1-qism: Tadbirkor Interfeysi (Private Chat)
1. Foydalanuvchi botga `/start` bosadi.
2. Agar u yangi bo'lsa, ketma-ket ma'lumotlar to'planadi:
   - Kompaniya yoki xizmat nomi
   - Nima bilan shug'ullanadi (mahsulot/xizmatlar va narxlar)
   - Manzil va ish vaqti (matn ko'rinishida yozish YOKI "📍 Joylashuvni yuborish" tugmasi orqali xaritadagi geolokatsiyani yuborish mumkin)
   - Yetkazib berish va to'lov turlari
3. Shundan so'ng **Asosiy Menyu** ochiladi:
   - **➕ Savol-javob qo'shish**: Mijozlar ko'p beradigan savolni va AI berishi kerak bo'lgan javobni kiritish (`faqs` jadvaliga saqlanadi).
   - **📋 Mening ma'lumotlarim**: Biznes ma'lumotlarini ko'rish, xaritadagi geolokatsiyani ko'rish, har bir FAQ ni alohida ko'rish va o'chirish, biznes ma'lumotlarini qayta kiritish.
   - **🤖 AI yordamida savollar generatsiya qilish**: Foydalanuvchi o'z sohasini yozsa, Gemini shu sohada eng ko'p so'raladigan 5 ta savolni chiqarib beradi va har biriga bitta tugma orqali javob yozib bazaga qo'shish mumkin.
   - **🔗 Shaxsiy profilga ulash**: Telegram Business orqali ulash bo'yicha yo'riqnoma.
   - **⏸ Botni vaqtincha to'xtatish / ▶️ Yoqish**: Avto-javobni yoqish yoki to'xtatish (`is_active` statusi).

### 2-qism: Telegram Business va Mijozlarga Javob Berish
1. Tadbirkor Telegram sozlamalarida (`Settings -> Telegram Business -> Chatbots`) botni ulaydi.
2. `@dp.business_connection()` orqali `business_connection_id` tadbirkorning `user_id` siga avtomatik biriktiriladi.
3. Mijozdan xabar kelganda (`@dp.business_message(F.text)`):
   - Xabar egasi tadbirkorning o'zi emasligi tekshiriladi (`message.from_user.id != owner_id`).
   - Tadbirkorning `is_active` statusi tekshiriladi.
   - Tadbirkorning biznes ma'lumotlari, geolokatsiyasi va barcha FAQ qoidalari olinadi.
   - Mijoz bilan oldingi 5 ta xabar konteksti olinadi.
   - `gemini-2.5-flash` modeliga qat'iy System Prompt bilan dinamik so'rov yuboriladi (yolg'on ma'lumot to'qimaslik, muloyimlik, o'zbek tilida ravon javob berish).
   - Javob matni `message.answer(text, business_connection_id=conn_id)` orqali mijozga yuboriladi.
   - **📍 Avtomatik Lokatsiya**: Agar mijoz xaritadan lokatsiya so'rasa ("lokatsiya tashlang", "qayerda joylashgansiz", "geolokatsiya" va h.k.) va tadbirkorda lokatsiya saqlangan bo'lsa, bot avtomatik tarzda Telegram xarita lokatsiyasini (`send_location`) mijozga yuboradi.

---

## ▶️ Ishga tushirish

```bash
source venv/bin/activate
python main.py
```
Konsolda quyidagi xabarni ko'rasiz:
```text
SQLite ma'lumotlar bazasi tayyorlandi.
Bot muvaffaqiyatli ishga tushdi: @your_bot_username (Assalomu aleykum xizmat)
```
