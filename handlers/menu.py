import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from states import AddFaqStates, AiGenerateFaqStates, OnboardingStates
from database import (
    get_business_by_user_id,
    set_business_status,
    add_faq,
    get_faqs,
    get_faq_by_id,
    delete_faq
)
from keyboards import (
    get_main_menu,
    get_cancel_keyboard,
    get_my_info_inline_keyboard,
    get_faq_detail_keyboard,
    get_generated_faqs_keyboard
)
from services.ai_service import generate_top_faqs

logger = logging.getLogger(__name__)
router = Router(name="menu")

# ==================== 1. SAVOL-JAVOB QO'SHISH ====================

@router.message(F.text == "➕ Savol-javob qo'shish")
async def start_add_faq(message: Message, state: FSMContext):
    user_id = message.from_user.id
    business = await get_business_by_user_id(user_id)
    if not business:
        await message.answer("Avval /start orqali biznesingizni ro'yxatdan o'tkazing!")
        return

    await message.answer(
        "Mijozlaringiz ko'p beradigan savolni kiriting:\n\n"
        "<i>(Masalan: 'Bo'lib to'lash (kredit) bormi?', 'Kafolat bormi?')</i>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AddFaqStates.question)

@router.message(AddFaqStates.question, F.text)
async def process_faq_question(message: Message, state: FSMContext):
    question = message.text.strip()
    await state.update_data(faq_question=question)

    await message.answer(
        f"Savol: <b>\"{question}\"</b>\n\n"
        f"Endi ushbu savolga AI mijozga qanday javob berishi kerakligini yozing:\n"
        f"<i>(Masalan: 'Ha, Alif Nasiya orqali 12 oygacha foizsiz bo'lib to'lash imkoniyati bor.')</i>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AddFaqStates.answer)

@router.message(AddFaqStates.answer, F.text)
async def process_faq_answer(message: Message, state: FSMContext):
    answer = message.text.strip()
    data = await state.get_data()
    question = data.get("faq_question")
    user_id = message.from_user.id

    await add_faq(user_id=user_id, question=question, answer=answer)
    await state.clear()

    business = await get_business_by_user_id(user_id)
    is_active = bool(business.get("is_active", 1)) if business else True

    await message.answer(
        f"✅ <b>Yangi savol-javob muvaffaqiyatli saqlandi!</b>\n\n"
        f"❓ <b>Savol:</b> {question}\n"
        f"💬 <b>Javob:</b> {answer}\n\n"
        f"Endi AI mijozlardan shu mazmundagi savol tushganda shu qoida asosida javob beradi.",
        parse_mode="HTML",
        reply_markup=get_main_menu(is_active)
    )

# ==================== 2. MENING MA'LUMOTLARIM (TAHRIRLASH/O'CHIRISH) ====================

@router.message(F.text == "📋 Mening ma'lumotlarim")
async def show_my_info(message: Message):
    user_id = message.from_user.id
    business = await get_business_by_user_id(user_id)
    if not business:
        await message.answer("Biznes ma'lumotlari topilmadi. /start buyrug'ini bosing.")
        return

    faqs = await get_faqs(user_id)
    conn_status = "🟢 Ulangan" if business.get("business_connection_id") else "⚪️ Hali ulanmagan"
    bot_status = "🟢 Faol" if business.get("is_active", 1) else "🔴 To'xtatilgan"
    has_location = bool(business.get("latitude") is not None and business.get("longitude") is not None)
    loc_status = f"✅ Belgilangan" if has_location else "⚪️ Belgilanmagan (faqat matn)"

    text = (
        f"🏢 <b>Biznes nomi:</b> {business.get('company_name')}\n"
        f"💼 <b>Faoliyat & Narxlar:</b> {business.get('activity_description')}\n"
        f"📍 <b>Manzil & Ish vaqti:</b> {business.get('address_hours')}\n"
        f"🗺 <b>Xaritadagi lokatsiya:</b> {loc_status}\n"
        f"🚚 <b>Yetkazib berish & To'lov:</b> {business.get('delivery_payment')}\n\n"
        f"🔌 <b>Telegram Business ulanishi:</b> {conn_status}\n"
        f"⚡️ <b>AI Yordamchi holati:</b> {bot_status}\n"
        f"📚 <b>Saqlangan FAQ qoidalari soni:</b> {len(faqs)} ta\n\n"
        f"<i>Quyidagi tugmalar orqali savollarni ko'rishingiz, o'chirishingiz yoki biznes ma'lumotlarini qayta kiritishingiz mumkin:</i>"
    )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_my_info_inline_keyboard(faqs, has_location=has_location)
    )

@router.callback_query(F.data.startswith("view_faq_"))
async def cb_view_faq(callback: CallbackQuery):
    faq_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    faq = await get_faq_by_id(faq_id, user_id)

    if not faq:
        await callback.answer("Ushbu savol-javob topilmadi yoki o'chirilgan.", show_alert=True)
        return

    text = (
        f"❓ <b>Savol:</b>\n{faq['question']}\n\n"
        f"💬 <b>AI uchun belgilangan javob:</b>\n{faq['answer']}"
    )
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_faq_detail_keyboard(faq_id)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("del_faq_"))
async def cb_del_faq(callback: CallbackQuery):
    faq_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    deleted = await delete_faq(faq_id, user_id)

    if deleted:
        await callback.answer("Savol-javob o'chirildi!", show_alert=True)
    else:
        await callback.answer("O'chirishda xatolik yuz berdi.", show_alert=True)

    # Ro'yxatni yangilash
    business = await get_business_by_user_id(user_id)
    faqs = await get_faqs(user_id)
    conn_status = "🟢 Ulangan" if business.get("business_connection_id") else "⚪️ Hali ulanmagan"
    bot_status = "🟢 Faol" if business.get("is_active", 1) else "🔴 To'xtatilgan"
    has_location = bool(business.get("latitude") is not None and business.get("longitude") is not None)
    loc_status = f"✅ Belgilangan" if has_location else "⚪️ Belgilanmagan (faqat matn)"

    text = (
        f"🏢 <b>Biznes nomi:</b> {business.get('company_name')}\n"
        f"💼 <b>Faoliyat & Narxlar:</b> {business.get('activity_description')}\n"
        f"📍 <b>Manzil & Ish vaqti:</b> {business.get('address_hours')}\n"
        f"🗺 <b>Xaritadagi lokatsiya:</b> {loc_status}\n"
        f"🚚 <b>Yetkazib berish & To'lov:</b> {business.get('delivery_payment')}\n\n"
        f"🔌 <b>Telegram Business ulanishi:</b> {conn_status}\n"
        f"⚡️ <b>AI Yordamchi holati:</b> {bot_status}\n"
        f"📚 <b>Saqlangan FAQ qoidalari soni:</b> {len(faqs)} ta"
    )
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_my_info_inline_keyboard(faqs, has_location=has_location)
    )

@router.callback_query(F.data == "view_my_location")
async def cb_view_my_location(callback: CallbackQuery):
    user_id = callback.from_user.id
    business = await get_business_by_user_id(user_id)
    if business and business.get("latitude") and business.get("longitude"):
        await callback.message.answer_location(
            latitude=float(business["latitude"]),
            longitude=float(business["longitude"])
        )
        await callback.answer()
    else:
        await callback.answer("Xaritadagi lokatsiya topilmadi.", show_alert=True)

@router.callback_query(F.data == "back_to_info")
async def cb_back_to_info(callback: CallbackQuery):
    user_id = callback.from_user.id
    business = await get_business_by_user_id(user_id)
    faqs = await get_faqs(user_id)
    conn_status = "🟢 Ulangan" if business.get("business_connection_id") else "⚪️ Hali ulanmagan"
    bot_status = "🟢 Faol" if business.get("is_active", 1) else "🔴 To'xtatilgan"
    has_location = bool(business.get("latitude") is not None and business.get("longitude") is not None)
    loc_status = f"✅ Belgilangan" if has_location else "⚪️ Belgilanmagan (faqat matn)"

    text = (
        f"🏢 <b>Biznes nomi:</b> {business.get('company_name')}\n"
        f"💼 <b>Faoliyat & Narxlar:</b> {business.get('activity_description')}\n"
        f"📍 <b>Manzil & Ish vaqti:</b> {business.get('address_hours')}\n"
        f"🗺 <b>Xaritadagi lokatsiya:</b> {loc_status}\n"
        f"🚚 <b>Yetkazib berish & To'lov:</b> {business.get('delivery_payment')}\n\n"
        f"🔌 <b>Telegram Business ulanishi:</b> {conn_status}\n"
        f"⚡️ <b>AI Yordamchi holati:</b> {bot_status}\n"
        f"📚 <b>Saqlangan FAQ qoidalari soni:</b> {len(faqs)} ta"
    )
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_my_info_inline_keyboard(faqs, has_location=has_location)
    )
    await callback.answer()

@router.callback_query(F.data == "edit_business_info")
async def cb_edit_business_info(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Keling, biznesingiz ma'lumotlarini yangilaymiz.\n\n"
        "<b>1️⃣ Kompaniya yoki xizmat nomi nima?</b>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(OnboardingStates.company_name)
    await callback.answer()

# ==================== 3. AI YORDAMIDA SAVOLLAR GENERATSIYA QILISH ====================

@router.message(F.text == "🤖 AI yordamida savollar")
@router.message(F.text.startswith("🤖 AI yordamida"))
async def start_ai_faq_generation(message: Message, state: FSMContext):
    user_id = message.from_user.id
    business = await get_business_by_user_id(user_id)
    if not business:
        await message.answer("Avval /start orqali biznesingizni kiriting.")
        return

    company_name = business.get("company_name", "")
    await message.answer(
        f"🤖 <b>AI orqali savollar generatsiya qilish</b>\n\n"
        f"Biznesingiz yoki faoliyat sohangizni yozing (masalan: <i>'{company_name}'</i>, <i>'Stomatologiya klinikasi'</i>, <i>'Avtoehtiyot qismlar do'koni'</i>).\n\n"
        f"Gemini siz uchun mijozlar eng ko'p so'raydigan 5 ta savolni avtomatik tuzib beradi!",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AiGenerateFaqStates.sphere)

@router.message(AiGenerateFaqStates.sphere, F.text)
async def process_ai_sphere(message: Message, state: FSMContext):
    sphere = message.text.strip()
    status_msg = await message.answer("⏳ Gemini AI sizning sohangiz bo'yicha eng dolzarb 5 ta savolni tayyorlamoqda...")

    try:
        questions = await generate_top_faqs(sphere)
        await state.update_data(generated_questions=questions)

        msg_text = f"🎯 <b>\"{sphere}\" sohasi bo'yicha mijozlarning eng ko'p beradigan 5 ta savoli:</b>\n\n"
        for idx, q in enumerate(questions, 1):
            msg_text += f"<b>{idx}.</b> {q}\n"
        msg_text += "\nQuyidagi tugmalar orqali istalgan savolga javob yozib, uni o'z bazangizga qo'shishingiz mumkin:"

        await status_msg.delete()
        await message.answer(
            msg_text,
            parse_mode="HTML",
            reply_markup=get_generated_faqs_keyboard(questions)
        )
    except Exception as e:
        logger.error(f"Generatsiya xatosi: {e}")
        await status_msg.edit_text("Kechirasiz, savollarni generatsiya qilishda xatolik yuz berdi. Qayta urinib ko'ring.")

@router.callback_query(F.data.startswith("answer_ai_faq_"))
async def cb_answer_ai_faq(callback: CallbackQuery, state: FSMContext):
    idx = int(callback.data.split("_")[3])
    data = await state.get_data()
    questions = data.get("generated_questions", [])

    if idx >= len(questions):
        await callback.answer("Savol topilmadi.", show_alert=True)
        return

    selected_question = questions[idx]
    await state.update_data(selected_ai_question=selected_question)

    await callback.message.answer(
        f"Tanlangan savol:\n<b>❓ \"{selected_question}\"</b>\n\n"
        f"Ushbu savolga AI mijozga qanday javob berishi kerakligini yozing:",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AiGenerateFaqStates.waiting_answer)
    await callback.answer()

@router.message(AiGenerateFaqStates.waiting_answer, F.text)
async def process_ai_faq_answer(message: Message, state: FSMContext):
    answer = message.text.strip()
    data = await state.get_data()
    question = data.get("selected_ai_question")
    user_id = message.from_user.id

    if question:
        await add_faq(user_id=user_id, question=question, answer=answer)
        await state.clear()

        business = await get_business_by_user_id(user_id)
        is_active = bool(business.get("is_active", 1)) if business else True

        await message.answer(
            f"✅ <b>Savol-javob bazangizga qo'shildi!</b>\n\n"
            f"❓ <b>Savol:</b> {question}\n"
            f"💬 <b>Javob:</b> {answer}",
            parse_mode="HTML",
            reply_markup=get_main_menu(is_active)
        )
    else:
        await message.answer("Savol topilmadi. Qaytadan urinib ko'ring.")
        await state.clear()

@router.callback_query(F.data == "close_ai_suggestions")
async def cb_close_ai(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.answer("Yopildi.")

# ==================== 4. TELEGRAM BUSINESS PROFILGA ULASH ====================

@router.message(F.text == "🔗 Shaxsiy profilga ulash")
async def connect_instructions(message: Message):
    bot_info = await message.bot.get_me()
    bot_username = bot_info.username

    text = (
        "🔗 <b>Botni shaxsiy Telegram profilingizga ulash yo'riqnomasi:</b>\n\n"
        "<i>Eslatma: Ushbu imkoniyatdan foydalanish uchun sizda Telegram Premium bo'lishi talab etiladi (Telegram Business funksiyasi).</i>\n\n"
        "<b>Qadamma-qadam qo'llanma:</b>\n"
        "1️⃣ Telegram ilovangizda <b>Sozlamalar (Settings)</b> bo'limiga kiring;\n"
        "2️⃣ <b>Telegram Business</b> bo'limiga o'ting;\n"
        "3️⃣ U yerdan <b>Chatbots (Чат-боты)</b> bandini tanlang;\n"
        f"4️⃣ Qidiruv maydoniga botimiz usernamesini kiriting:\n"
        f"   👉 <code>@{bot_username}</code>\n"
        "5️⃣ Botga ruxsat bering va saqlang!\n\n"
        "⚡️ Bot ulangach, u avtomatik ravishda profilingizni taniydi va shaxsiy xabarlaringizga siz kiritgan biznes qoidalari asosida mijozlarga avto-javob bera boshlaydi!"
    )
    await message.answer(text, parse_mode="HTML")

# ==================== 5. BOTNI VAQTINCHA TO'XTATISH / YOQISH ====================

@router.message(F.text == "⏸ Botni vaqtincha to'xtatish")
async def pause_bot(message: Message):
    user_id = message.from_user.id
    business = await get_business_by_user_id(user_id)
    if not business:
        await message.answer("Avval /start orqali ro'yxatdan o'ting.")
        return

    await set_business_status(user_id, is_active=False)
    await message.answer(
        "⏸ <b>AI Yordamchi vaqtincha to'xtatildi!</b>\n\n"
        "Endi profilingizga kelgan mijoz xabarlariga AI javob bermaydi. "
        "Istalgan vaqtda qayta yoqishingiz mumkin.",
        parse_mode="HTML",
        reply_markup=get_main_menu(is_active=False)
    )

@router.message(F.text == "▶️ Botni yoqish")
async def resume_bot(message: Message):
    user_id = message.from_user.id
    business = await get_business_by_user_id(user_id)
    if not business:
        await message.answer("Avval /start orqali ro'yxatdan o'ting.")
        return

    await set_business_status(user_id, is_active=True)
    await message.answer(
        "▶️ <b>AI Yordamchi muvaffaqiyatli yoqildi!</b>\n\n"
        "Mijozlaringizdan kelgan xabarlarga AI yana avtomatik javob berishni boshlaydi.",
        parse_mode="HTML",
        reply_markup=get_main_menu(is_active=True)
    )
