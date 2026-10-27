import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from database import init_db
from handlers import onboarding, menu, business

# Logging sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

async def main():
    if not BOT_TOKEN:
        logger.critical("BOT_TOKEN aniqlanmadi! .env faylida BOT_TOKEN ni ko'rsating.")
        return

    # Ma'lumotlar bazasini initsializatsiya qilish
    await init_db()
    logger.info("SQLite ma'lumotlar bazasi tayyorlandi.")

    # Bot va Dispatcher
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Routerlarni ulash
    dp.include_router(onboarding.router)
    dp.include_router(menu.router)
    dp.include_router(business.router)

    # Bot haqida ma'lumot olish
    bot_info = await bot.get_me()
    logger.info(f"Bot muvaffaqiyatli ishga tushdi: @{bot_info.username} ({bot_info.full_name})")

    # Telegram Business va oddiy yangilanishlarni qabul qilish
    # Business hodisalari aniq ko'rsatilishi shart
    allowed_updates = [
        "message",
        "edited_message",
        "callback_query",
        "business_connection",
        "business_message",
        "edited_business_message",
        "deleted_business_messages"
    ]

    try:
        # Eski to'plangan yangilanishlarni tashlab yuborish
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=allowed_updates)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
