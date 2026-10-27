from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from states import OnboardingStates
from database import get_business_by_user_id, create_or_update_business
from keyboards import get_main_menu, get_cancel_keyboard, get_address_keyboard, get_skip_keyboard

router = Router(name="onboarding")

@router.message(Command("cancel"))
@router.message(F.text == "❌ Bekor qilish")
async def cancel_handler(message: Message, state: FSMContext):
    """Joriy FSM jarayonini bekor qilish"""
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
        
    business = await get_business_by_user_id(message.from_user.id)
    is_active = bool(business.get("is_active", 1)) if business else True
    
    await message.answer(
        "Amal bekor qilindi. Asosiy menyudasiz.",
        reply_markup=get_main_menu(is_active)
    )

@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    """/start buyrug'i: Mavjud foydalanuvchini tekshirish yoki onboardingni boshlash"""
    await state.clear()
    user_id = message.from_user.id
    business = await get_business_by_user_id(user_id)

    if business:
        is_active = bool(business.get("is_active", 1))
        company_name = business.get("company_name", "Kompaniya")
        status_text = "🟢 Faol" if is_active else "🔴 To'xtatilgan"
        
        await message.answer(
            f"Assalomu alaykum, <b>{company_name}</b> rahbari!\n\n"
            f"🤖 Sizning Telegram Business AI yordamchingiz tayyor.\n"
            f"Status: <b>{status_text}</b>\n\n"
            f"Kerakli bo'limni tanlang:",
            parse_mode="HTML",
            reply_markup=get_main_menu(is_active)
        )
    else:
        # Yangi foydalanuvchi uchun onboarding
        await message.answer(
            "Assalomu alaykum! <b>'Assalomu aleykum xizmat'</b> botiga xush kelibsiz! 🚀\n\n"
            "Bu bot sizning shaxsiy Telegram profilingizga (Telegram Business orqali) ulanib, "
            "mijozlaringizga 24/7 rejimida aqlli va xushmuomala tarzda avto-javob beradi.\n\n"
            "Boshlash uchun biznesingiz haqida 4 ta qisqa ma'lumotni kiritib oling:\n\n"
            "<b>1️⃣ Kompaniya yoki xizmat nomi nima?</b>\n"
            "<i>(Masalan: 'Artel Servis Markazi', 'Samarqand Oshxonasi', 'Apex Barbershop')</i>",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(OnboardingStates.company_name)

@router.message(OnboardingStates.company_name, F.text)
async def process_company_name(message: Message, state: FSMContext):
    company_name = message.text.strip()
    if len(company_name) < 2:
        await message.answer("Iltimos, kompaniya nomini to'liqroq yozing:")
        return

    await state.update_data(company_name=company_name)
    await message.answer(
        "<b>2️⃣ Nima bilan shug'ullanasiz?</b>\n\n"
        "Qanday mahsulotlar yoki xizmatlar taqdim etasiz va ularning taxminiy narxlari qanaqa?\n"
        "<i>(AI ushbu ma'lumotlar asosida mijozlarga to'g'ri maslahat bera oladi)</i>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(OnboardingStates.activity_description)

@router.message(OnboardingStates.activity_description, F.text)
async def process_activity_description(message: Message, state: FSMContext):
    activity_desc = message.text.strip()
    await state.update_data(activity_description=activity_desc)
    
    await message.answer(
        "<b>3️⃣ Manzilingiz va ish vaqtingiz qanday?</b>\n\n"
        "Siz manzilni matn ko'rinishida yozishingiz YOKI pastdagi <b>'📍 Joylashuvni yuborish'</b> tugmasini bosib (yoki xaritadan) joylashuvingizni yuborishingiz mumkin! 🗺\n\n"
        "<i>(Agar lokatsiya yuborsangiz, keyinchalik mijozlaringiz profilingizdan lokatsiya so'raganda bot avtomatik ushbu lokatsiyani yuboradi)</i>",
        parse_mode="HTML",
        reply_markup=get_address_keyboard()
    )
    await state.set_state(OnboardingStates.address_hours)

@router.message(OnboardingStates.address_hours, F.location)
async def process_address_location(message: Message, state: FSMContext):
    """Foydalanuvchi xaritadagi lokatsiyani yuborganda"""
    lat = message.location.latitude
    lon = message.location.longitude
    await state.update_data(latitude=lat, longitude=lon)

    await message.answer(
        "📍 <b>Xaritadagi joylashuv muvaffaqiyatli qabul qilindi!</b>\n\n"
        "Endi ish vaqtingiz yoki manzil bo'yicha qo'shimcha ma'lumotni yozing:\n"
        "<i>(Masalan: 'Har kuni 09:00 dan 20:00 gacha, mo'ljal: Korzinka yonida')</i>\n\n"
        "Agar ish vaqtini kiritishni xohlamasangiz, <b>'⏭ O'tkazib yuborish'</b> tugmasini bosing:",
        parse_mode="HTML",
        reply_markup=get_skip_keyboard()
    )
    await state.set_state(OnboardingStates.work_hours)

@router.message(OnboardingStates.address_hours, F.text)
async def process_address_hours(message: Message, state: FSMContext):
    """Foydalanuvchi lokatsiya o'rniga faqat matn yozganda"""
    address_hours = message.text.strip()
    await state.update_data(address_hours=address_hours, latitude=None, longitude=None)

    await message.answer(
        "<b>4️⃣ Yetkazib berish va to'lov turlari qanaqa?</b>\n\n"
        "<i>(Masalan: Butun O'zbekiston bo'ylab yetkazib berish bor (25,000 so'm), Toshkent bo'ylab Yandex orqali. To'lov: Naqd, Click, Payme, Uzum Nasiya)</i>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(OnboardingStates.delivery_payment)

@router.message(OnboardingStates.work_hours, F.text)
async def process_work_hours(message: Message, state: FSMContext):
    """Lokatsiya yuborilgandan keyingi ish vaqti / qo'shimcha izoh"""
    text = message.text.strip()
    if text == "⏭ O'tkazib yuborish":
        address_hours = "Xaritadagi geolokatsiya belgilangan"
    else:
        address_hours = f"Geolokatsiya xaritada. Ish vaqti/qo'shimcha: {text}"

    await state.update_data(address_hours=address_hours)

    await message.answer(
        "<b>4️⃣ Yetkazib berish va to'lov turlari qanaqa?</b>\n\n"
        "<i>(Masalan: Butun O'zbekiston bo'ylab yetkazib berish bor (25,000 so'm), Toshkent bo'ylab Yandex orqali. To'lov: Naqd, Click, Payme, Uzum Nasiya)</i>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(OnboardingStates.delivery_payment)

@router.message(OnboardingStates.delivery_payment, F.text)
async def process_delivery_payment(message: Message, state: FSMContext):
    delivery_payment = message.text.strip()
    data = await state.get_data()
    user_id = message.from_user.id

    company_name = data.get("company_name", "Kompaniya")
    activity_description = data.get("activity_description", "")
    address_hours = data.get("address_hours", "")
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    # Bazaga saqlash
    await create_or_update_business(
        user_id=user_id,
        company_name=company_name,
        activity_description=activity_description,
        address_hours=address_hours,
        delivery_payment=delivery_payment,
        latitude=latitude,
        longitude=longitude
    )

    await state.clear()

    await message.answer(
        "🎉 <b>Tabriklaymiz! Biznes ma'lumotlaringiz muvaffaqiyatli saqlandi!</b>\n\n"
        "Endi quyidagilarni amalga oshirishingiz mumkin:\n"
        "• <b>➕ Savol-javob qo'shish</b> — mijozlaringiz ko'p so'raydigan savollarni kiritish;\n"
        "• <b>🤖 AI yordamida savollar generatsiya qilish</b> — sohangizga xos eng dolzarb 5 ta savolni tayyorlab olish;\n"
        "• <b>🔗 Shaxsiy profilga ulash</b> — botni shaxsiy Telegram akkauntingizga bog'lash va mijozlarga avto-javob berishni boshlash.",
        parse_mode="HTML",
        reply_markup=get_main_menu(is_active=True)
    )
