from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="🧾 История")],
        [KeyboardButton(text="👨‍👩‍👧 Семья"), KeyboardButton(text="📤 Excel")],
        [KeyboardButton(text="⚙️ Категории"), KeyboardButton(text="❓ Помощь")],
        [KeyboardButton(text="💎 Оплатить")],
    ],
    resize_keyboard=True,
)
