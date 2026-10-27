import logging
from aiogram import Router, F, Bot
from aiogram.types import BusinessConnection, Message

from database import (
    get_business_by_user_id,
    get_business_by_connection_id,
    update_business_connection,
    get_faqs,
    get_recent_chat_history,
    add_chat_history
)
from services.ai_service import generate_business_response

logger = logging.getLogger(__name__)
router = Router(name="business")

@router.business_connection()
async def handle_business_connection(event: BusinessConnection, bot: Bot):
    """
    Tadbirkor o'z shaxsiy profilingizda botni Telegram Business -> Chatbots
    orqali ulaganda yoki ulanishni bekor qilganda chaqiriladi.
    """
    user_id = event.user.id
    conn_id = event.id
    is_enabled = event.is_enabled

    logger.info(f"Business connection update: user_id={user_id}, conn_id={conn_id}, enabled={is_enabled}")

    try:
        business = await get_business_by_user_id(user_id)
        if business:
            if is_enabled:
                await update_business_connection(user_id=user_id, connection_id=conn_id)
                await bot.send_message(
                    chat_id=user_id,
                    text=(
                        "🎉 <b>Tabriklaymiz! Shaxsiy profilingiz botga muvaffaqiyatli ulandi!</b>\n\n"
                        "Endi profilingizga yangi mijozlar yozganda, siz kiritgan biznes ma'lumotlari "
                        "va savol-javoblar qoidalari asosida AI avtomatik javob beradi.\n\n"
                        "⚡️ Agar mijozga o'zingiz qo'lda javob yozsangiz, AI xalaqit bermaydi."
                    ),
                    parse_mode="HTML"
                )
            else:
                # Ulanish o'chirilgan
                await update_business_connection(user_id=user_id, connection_id=None)
                await bot.send_message(
                    chat_id=user_id,
                    text="ℹ️ Telegram Business ulanishi bekor qilindi. AI avto-javob berish to'xtatildi.",
                    parse_mode="HTML"
                )
        else:
            logger.warning(f"Business connection qabul qilindi, lekin user_id={user_id} bazada ro'yxatdan o'tmagan.")
    except Exception as e:
        logger.error(f"Business connectionni qayta ishlashda xatolik: {e}", exc_info=True)

def is_location_query(text: str) -> bool:
    """Mijoz xabarida manzil yoki lokatsiya so'ralganini aniqlash"""
    t = text.lower()
    keywords = [
        "lokatsiya", "lakatsiya", "lokasiya", "location", "joylashuv",
        "manzil", "qayerda joylashgan", "qayerdasiz", "qayerda sizlar",
        "xarita", "karta", "geolokatsiya", "geoplace", "qatta joylashgan",
        "qattasiz", "qatta siz", "qaerdasiz", "qaerdan topsa boladi",
        "где вы", "где находитесь", "скиньте локацию", "скиньте геолокацию",
        "геолокация", "адрес"
    ]
    return any(kw in t for kw in keywords)

@router.business_message(F.text)
async def handle_business_message(message: Message):
    """
    Tadbirkorning shaxsiy profiliga kelgan xabarlarga AI orqali avto-javob berish.
    """
    conn_id = message.business_connection_id
    if not conn_id:
        return

    try:
        # 1. Shu connection_id bo'yicha tadbirkorni topish
        business = await get_business_by_connection_id(conn_id)
        if not business:
            logger.warning(f"Connection ID {conn_id} bo'yicha tadbirkor topilmadi.")
            return

        owner_id = business["user_id"]

        # 2. Xabar egasi tadbirkorning o'zi emasligini tekshirish
        if message.from_user and message.from_user.id == owner_id:
            # Tadbirkor o'zi mijozga javob yozmoqda - AI aralashmaydi
            logger.debug(f"Tadbirkor ({owner_id}) o'zi yozgan xabar, e'tiborsiz qoldirildi.")
            return

        # 3. Tadbirkorning is_active statusini tekshirish
        if not bool(business.get("is_active", 1)):
            logger.debug(f"Tadbirkor ({owner_id}) uchun bot vaqtincha to'xtatilgan.")
            return

        chat_id = message.chat.id
        user_text = message.text.strip()

        # 4. FAQ qoidalarini olish
        faqs = await get_faqs(owner_id)

        # 5. Oxirgi 5 ta xabar kontekstini olish
        recent_history = await get_recent_chat_history(
            business_connection_id=conn_id,
            chat_id=chat_id,
            limit=5
        )

        # Mijoz xabarini tarixga saqlash
        await add_chat_history(
            business_connection_id=conn_id,
            chat_id=chat_id,
            role="user",
            message_text=user_text
        )

        # 6. Gemini AI orqali javob olish
        reply_text = await generate_business_response(
            business_info=business,
            faqs=faqs,
            chat_history=recent_history,
            new_message=user_text
        )

        has_location = bool(business.get("latitude") is not None and business.get("longitude") is not None)
        send_loc = False
        if has_location and ("[SEND_LOCATION]" in reply_text or is_location_query(user_text)):
            send_loc = True

        clean_reply_text = reply_text.replace("[SEND_LOCATION]", "").strip()

        # 7. AI javobini mijozga qaytarish
        if clean_reply_text:
            await message.answer(
                text=clean_reply_text,
                business_connection_id=conn_id
            )

        # 8. Agar lokatsiya so'ralgan va mavjud bo'lsa, xaritadagi lokatsiyani yuborish
        if send_loc:
            try:
                await message.bot.send_location(
                    chat_id=chat_id,
                    latitude=float(business["latitude"]),
                    longitude=float(business["longitude"]),
                    business_connection_id=conn_id
                )
                logger.info(f"Mijoz ({chat_id}) uchun xaritadagi lokatsiya yuborildi.")
            except Exception as loc_err:
                logger.error(f"Lokatsiya yuborishda xatolik: {loc_err}", exc_info=True)

        # AI javobini ham tarixga saqlash
        await add_chat_history(
            business_connection_id=conn_id,
            chat_id=chat_id,
            role="model",
            message_text=clean_reply_text + (" [📍 Lokatsiya yuborildi]" if send_loc else "")
        )

        logger.info(f"Mijoz ({chat_id}) uchun javob muvaffaqiyatli yuborildi.")

    except Exception as e:
        logger.error(f"Business xabarga javob berishda xatolik yuz berdi: {e}", exc_info=True)
