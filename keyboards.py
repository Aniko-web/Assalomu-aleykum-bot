from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from typing import List, Dict, Any

def get_main_menu(is_active: bool = True) -> ReplyKeyboardMarkup:
    """Asosiy menyu klaviaturasi"""
    status_btn = "⏸ Botni vaqtincha to'xtatish" if is_active else "▶️ Botni yoqish"
    
    keyboard = [
        [KeyboardButton(text="➕ Savol-javob qo'shish")],
        [
            KeyboardButton(text="📋 Mening ma'lumotlarim"),
            KeyboardButton(text="🤖 AI yordamida savollar")
        ],
        [
            KeyboardButton(text="🔗 Shaxsiy profilga ulash"),
            KeyboardButton(text=status_btn)
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        persistent=True
    )

def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Jarayonni bekor qilish tugmasi"""
    keyboard = [
        [KeyboardButton(text="❌ Bekor qilish")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_address_keyboard() -> ReplyKeyboardMarkup:
    """Manzil kiritish bosqichida lokatsiya yuborish yoki bekor qilish klaviaturasi"""
    keyboard = [
        [KeyboardButton(text="📍 Joylashuvni yuborish", request_location=True)],
        [KeyboardButton(text="❌ Bekor qilish")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_skip_keyboard() -> ReplyKeyboardMarkup:
    """Ixtiyoriy qadamni o'tkazib yuborish tugmasi"""
    keyboard = [
        [KeyboardButton(text="⏭ O'tkazib yuborish")],
        [KeyboardButton(text="❌ Bekor qilish")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_my_info_inline_keyboard(faqs: List[Dict[str, Any]], has_location: bool = False) -> InlineKeyboardMarkup:
    """Biznes ma'lumotlari menyusi uchun inline tugmalar"""
    inline_keyboard = []
    
    if faqs:
        for index, faq in enumerate(faqs, 1):
            q_short = faq["question"][:25] + ("..." if len(faq["question"]) > 25 else "")
            inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"❓ #{index}: {q_short}",
                    callback_data=f"view_faq_{faq['id']}"
                ),
                InlineKeyboardButton(
                    text="🗑 O'chirish",
                    callback_data=f"del_faq_{faq['id']}"
                )
            ])
            
    if has_location:
        inline_keyboard.append([
            InlineKeyboardButton(
                text="🗺 Xaritadagi joylashuvimni ko'rish",
                callback_data="view_my_location"
            )
        ])

    inline_keyboard.append([
        InlineKeyboardButton(
            text="✏️ Biznes ma'lumotlarini qayta kiritish",
            callback_data="edit_business_info"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

def get_faq_detail_keyboard(faq_id: int) -> InlineKeyboardMarkup:
    """Alohida FAQ ko'rilgandagi inline tugmalar"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🗑 Shu savolni o'chirish", callback_data=f"del_faq_{faq_id}"),
            InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_info")
        ]
    ])

def get_generated_faqs_keyboard(questions: List[str]) -> InlineKeyboardMarkup:
    """AI taklif qilgan savollarga javob yozish tugmalari"""
    inline_keyboard = []
    for idx, q in enumerate(questions):
        inline_keyboard.append([
            InlineKeyboardButton(
                text=f"✍️ {idx+1}-savolga javob yozish",
                callback_data=f"answer_ai_faq_{idx}"
            )
        ])
    inline_keyboard.append([
        InlineKeyboardButton(text="❌ Yopish", callback_data="close_ai_suggestions")
    ])
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
