import json
import logging
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

# GenAI client
_client: Optional[genai.Client] = None

def get_gemini_client() -> Optional[genai.Client]:
    global _client
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY o'rnatilmagan!")
        return None
    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client

def build_system_prompt(business_info: Dict[str, Any], faqs: List[Dict[str, Any]]) -> str:
    """Tadbirkor ma'lumotlari va FAQ bazasi asosida dinamik System Prompt yaratish"""
    company_name = business_info.get("company_name", "Kompaniya")
    activity = business_info.get("activity_description", "Noma'lum")
    address_hours = business_info.get("address_hours", "Noma'lum")
    delivery_payment = business_info.get("delivery_payment", "Noma'lum")

    faqs_text = ""
    if faqs:
        for idx, faq in enumerate(faqs, 1):
            faqs_text += f"{idx}. Savol: {faq['question']}\n   Javob: {faq['answer']}\n"
    else:
        faqs_text = "Hozircha qo'shimcha savol-javoblar bazasi yo'q.\n"

    latitude = business_info.get("latitude")
    longitude = business_info.get("longitude")
    has_location = bool(latitude is not None and longitude is not None)
    location_desc = f"Mavjud (Kenglik: {latitude}, Uzunlik: {longitude})" if has_location else "Kiritilmagan (faqat matn)"

    system_prompt = f"""Sen "{company_name}" biznesining Telegram'dagi rasmiy, juda xushmuomala, professional va aqlli yordamchisisan.
Mijozlar senga Telegram orqali yozganda sen tadbirkor nomidan javob berasan.

BIZNES HAQIDA MA'LUMOTLAR:
- Tashkilot / Xizmat nomi: {company_name}
- Faoliyat turi, mahsulotlar va narxlar: {activity}
- Manzil va ish vaqti: {address_hours}
- Yetkazib berish va to'lov turlari: {delivery_payment}
- Xaritadagi aniq lokatsiya (GPS): {location_desc}

ANIQ SAVOL-JAVOBLAR (FAQ) BAZASI:
{faqs_text}

QAT'IY QOIDALAR VA KO'RSATMALAR:
1. Har doim o'zbek tilida (agar mijoz rus yoki ingliz tilida yozsa, u yozgan tilda) samimiy, do'stona va yuksak odob bilan javob ber.
2. Har bir murojaatga salomlashish ("Assalomu alaykum!", "Xush kelibsiz!") bilan boshlash maqsadga muvofiq, lekin suhbat davomida ortiqcha takrorlama.
3. Javoblarni yuqorida keltirilgan biznes ma'lumotlari va FAQ bazasiga to'liq asoslangan holda ber.
4. MUHIM QOIDA: Agar mijoz so'ragan savolga javob yuqoridagi ma'lumotlar bazasida UMUMAN BO'LMASA, HECH QACHON o'zingdan yolg'on, taxminiy ma'lumot to'qib chiqarma! Bunday holatda mijozga xushmuomalalik bilan:
   "Kechirasiz, ushbu masala bo'yicha aniq ma'lumot berish uchun tez orada mas'ul xodimimiz siz bilan bog'lanadi." deb javob ber.
5. Javoblaring Telegram xabari formatiga mos, lo'nda, qulay o'qiladigan va chiroyli emojilar bilan bezatilgan bo'lsin. Ortiqcha keraksiz cho'zma gaplardan qoch.
6. LOKATSIYA SO'ROVLARI: Agar mijoz manzil, lokatsiya, geolokatsiya, xarita yoki "qayerdasiz", "joylashuvingiz qayerda", "lokatsiya tashlang" kabi joylashuvni so'rasa:
   - Agar xaritadagi lokatsiya mavjud bo'lsa ({has_location}): mijozga xushmuomalalik bilan manzil/ish vaqtini ayt va xabaring ichiga albatta [SEND_LOCATION] belgisini qo'sh (masalan: "Bizning manzilimiz: ... Xaritadagi joylashuvimizni yuboryapman: [SEND_LOCATION]"). Tizim bu belgi orqali mijozga Telegram xaritadagi lokatsiyani avtomatik yuboradi.
   - Agar lokatsiya mavjud bo'lmasa: faqat yuqoridagi matnli manzil ma'lumotlarini taqdim et.
"""
    return system_prompt

async def generate_business_response(
    business_info: Dict[str, Any],
    faqs: List[Dict[str, Any]],
    chat_history: List[Dict[str, str]],
    new_message: str
) -> str:
    """Telegram Business mijoz xabariga AI orqali javob olish"""
    client = get_gemini_client()
    if not client:
        return "Assalomu alaykum! Xabaringiz qabul qilindi. Mas'ul xodimimiz tez orada siz bilan bog'lanadi."

    system_instruction = build_system_prompt(business_info, faqs)

    # Suhbat tarixini tayyorlash
    contents: List[types.Content] = []
    for item in chat_history:
        role = "user" if item.get("role") == "user" else "model"
        contents.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=item.get("message_text", ""))]
            )
        )

    # Yangi xabarni qo'shish
    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=new_message)]
        )
    )

    try:
        response = await client.aio.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.3,
            )
        )
        if response and response.text:
            return response.text.strip()
        return "Assalomu alaykum! Xabaringiz qabul qilindi, tez orada mutaxassisimiz javob beradi."
    except Exception as e:
        logger.error(f"Gemini API xatoligi: {e}", exc_info=True)
        return "Assalomu alaykum! Xabaringiz uchun rahmat. Tez orada sizga xodimimiz javob qaytaradi."

async def generate_top_faqs(sphere: str) -> List[str]:
    """Tadbirkor kiritgan soha bo'yicha mijozlar eng ko'p so'raydigan 5 ta savolni generatsiya qilish"""
    client = get_gemini_client()
    if not client:
        return [
            "Mahsulot yoki xizmatlaringiz narxi qancha?",
            "Yetkazib berish xizmati bormi va qancha vaqt oladi?",
            "Ish vaqtingiz va manzilingiz qayerda?",
            "Kredit yoki bo'lib to'lash imkoniyati bormi?",
            "Kafolat (garantiya) beriladimi?"
        ]

    prompt = f"""Foydalanuvchi biznes sohasi: "{sphere}".
Ushbu sohada mijozlar Telegram orqali tadbirkorga eng ko'p beradigan 5 ta dolzarb va real savolni tuzib ber.
Javobni FAQAT quyidagi JSON formatida qaytar (boshqa hech qanday so'z, izoh yoki markdown belgisisiz):
["1-savol matni", "2-savol matni", "3-savol matni", "4-savol matni", "5-savol matni"]
Savollar aniq, o'zbek tilida va xaridor nuqtai nazaridan yozilgan bo'lsin.
"""
    try:
        response = await client.aio.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.4,
                response_mime_type="application/json"
            )
        )
        if response and response.text:
            cleaned_text = response.text.strip()
            # JSON parse
            questions = json.loads(cleaned_text)
            if isinstance(questions, list) and len(questions) > 0:
                return [str(q).strip() for q in questions[:5]]
    except Exception as e:
        logger.error(f"FAQ generatsiya xatosi: {e}", exc_info=True)

    # Fallback default savollar
    return [
        f"{sphere} bo'yicha narxlar va xizmat turlari qanday?",
        "Yetkazib berish yoki filialga borish shartlari qanaqa?",
        "To'lov turlari qaysilar (naqd, Click, Payme, muddatli to'lov)?",
        "Ish vaqtingiz va dam olish kunlaringiz bormi?",
        "Buyurtma berish uchun nima qilish kerak?"
    ]
