from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery

from config import LIFETIME_PRICE_STARS, PROMO_CODE
from keyboards import main_kb
from services.users import get_internal_user_id, activate_paid, save_payment

router = Router()


@router.message(Command("pay"))
@router.message(F.text == "💎 Оплатить")
async def pay_handler(message: Message):
    await message.answer_invoice(
        title="Lifetime-доступ к бюджет-боту",
        description="Один платеж. Полный доступ навсегда.",
        payload="lifetime_access",
        currency="XTR",
        prices=[LabeledPrice(label="Lifetime", amount=LIFETIME_PRICE_STARS)],
        provider_token="",
    )


@router.pre_checkout_query()
async def pre_checkout_handler(query: PreCheckoutQuery):
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    user_id = await get_internal_user_id(message.from_user.id)
    payment = message.successful_payment
    if payment.invoice_payload == "lifetime_access":
        await activate_paid(user_id)
        await save_payment(user_id, payment)
        await message.answer("🎉 Оплата прошла. Lifetime-доступ активирован.", reply_markup=main_kb)


@router.message(Command("promo"))
async def promo_handler(message: Message):
    user_id = await get_internal_user_id(message.from_user.id)
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Формат: /promo КОД")
        return
    if parts[1].strip() == PROMO_CODE:
        await activate_paid(user_id)
        await message.answer("🎉 Промокод принят. Lifetime-доступ активирован.", reply_markup=main_kb)
    else:
        await message.answer("Промокод не подошел.")
