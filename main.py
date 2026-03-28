import asyncio
import json
import random
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from config import TOKEN, ADMIN_ID, ADMIN_ID_2, DEFAULT_RATE

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# ================= Ручний курс =================
CURRENT_RATE = {
    "UAH_to_PLN": Decimal(str(DEFAULT_RATE["PLN"])),
    "PLN_to_UAH": Decimal(str(DEFAULT_RATE["PLN"]))
}

# ================= Адміни =================
ADMINS = [ADMIN_ID, ADMIN_ID_2]

user_data = {}

# ================= Keyboards =================
def main_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("💵 Продати UAH"))
    kb.add(KeyboardButton("💰 Купити UAH"))
    kb.add(KeyboardButton("📊 Актуальний курс"))
    return kb

def receive_method_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("Готівка"), KeyboardButton("Bank Transfer"))
    kb.add(KeyboardButton("🏠 Головне меню"))
    return kb

def receive_method_buy_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("Готівка"), KeyboardButton("Bank Transfer"), KeyboardButton("Blik"))
    kb.add(KeyboardButton("🏠 Головне меню"))
    return kb

# ================= Handlers =================
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    uid = message.from_user.id
    user_data[uid] = {}

    await message.answer(
        "👋 Вітаємо!\n\n"
        "Команда BatPay 💱\n"
        "За допомогою цього бота ви зможете швидко та безпечно створити заявку на переказ коштів в Україну та навпаки🇺🇦🔁🇵🇱 \n\n"
        "Обирайте дію, щоб продовжити ⬇️",
        reply_markup=main_keyboard()
    )

# ===== Головне меню =====
@dp.message_handler(lambda m: m.text == "🏠 Головне меню")
async def back_to_main(message: types.Message):
    await cmd_start(message)

# ===== ПРОДАЖ =====
@dp.message_handler(lambda m: m.text == "💵 Продати UAH")
async def sell_uah_start(message: types.Message):
    uid = message.from_user.id
    if uid not in user_data:
        user_data[uid] = {}

    await message.answer("Введіть суму в UAH:", reply_markup=types.ReplyKeyboardRemove())
    user_data[uid]['step'] = 'enter_amount'

# ===== КУПІВЛЯ =====
@dp.message_handler(lambda m: m.text == "💰 Купити UAH")
async def buy_uah_start(message: types.Message):
    uid = message.from_user.id
    if uid not in user_data:
        user_data[uid] = {}

    await message.answer("Введіть суму в UAH яку хочете отримати:", reply_markup=types.ReplyKeyboardRemove())
    user_data[uid]['step'] = 'buy_enter_amount'

# ================= Курс =================
@dp.message_handler(lambda m: m.text == "📊 Актуальний курс")
async def show_current_rate(message: types.Message):
    text = (
        f"Актуальний курс на {datetime.now().strftime('%d.%m.%Y')}⬇️\n\n"
        f"UAH🇺🇦-PLN🇵🇱: {CURRENT_RATE['UAH_to_PLN']}\n"
        f"PLN🇵🇱-UAH🇺🇦: {CURRENT_RATE['PLN_to_UAH']}"
    )
    await message.answer(text)

# ================= Адмін: встановлення курсу =================
@dp.message_handler(commands=['setrate'])
async def set_rate_admin(message: types.Message):
    if message.from_user.id not in ADMINS:
        return

    try:
        parts = message.text.split()
        if len(parts) != 3:
            await message.answer("Використання: /setrate <UAH_to_PLN> <PLN_to_UAH>")
            return

        uah_to_pln = Decimal(parts[1].replace(',', '.'))
        pln_to_uah = Decimal(parts[2].replace(',', '.'))

        CURRENT_RATE["UAH_to_PLN"] = uah_to_pln.quantize(Decimal("0.01"))
        CURRENT_RATE["PLN_to_UAH"] = pln_to_uah.quantize(Decimal("0.01"))

        await message.answer(
            f"Курс оновлено!\n"
            f"UAH → PLN: {CURRENT_RATE['UAH_to_PLN']}\n"
            f"PLN → UAH: {CURRENT_RATE['PLN_to_UAH']}"
        )
    except:
        await message.answer("Помилка формату")

# ================= Основний =================
@dp.message_handler()
async def handle_all(message: types.Message):
    uid = message.from_user.id
    if uid not in user_data:
        user_data[uid] = {}

    if message.text == "🏠 Головне меню":
        await cmd_start(message)
        return

    step = user_data[uid].get('step')

    # ===== ПРОДАЖ =====
    if step == 'enter_amount':
        try:
            amount_uah = Decimal(message.text.replace(',', '.'))
            user_data[uid]['amount_uah'] = amount_uah

            rate = CURRENT_RATE["UAH_to_PLN"]
            amount_pln = (amount_uah / rate).quantize(Decimal("0.01"))

            user_data[uid]['amount_pln'] = amount_pln

            await message.answer(
                f"Сума по актуальному курсу {amount_pln:.2f} PLN.\nОберіть зручний спосіб оплати:",
                reply_markup=receive_method_keyboard()
            )
            user_data[uid]['step'] = 'choose_method'
        except:
            await message.answer("Будь ласка, введіть правильне число.")

    # ===== КУПІВЛЯ =====
    elif step == 'buy_enter_amount':
        try:
            amount_uah = Decimal(message.text.replace(',', '.'))
            user_data[uid]['buy_amount_uah'] = amount_uah

            rate = CURRENT_RATE["PLN_to_UAH"]
            amount_pln = (amount_uah / rate).quantize(Decimal("0.01"))

            user_data[uid]['buy_amount_pln'] = amount_pln

            await message.answer(
                f"Сума по актуальному курсу {amount_pln:.2f} PLN.\nОберіть зручний спосіб оплати:",
                reply_markup=receive_method_buy_keyboard()
            )
            user_data[uid]['step'] = 'buy_choose_method'
        except:
            await message.answer("Будь ласка, введіть правильне число.")

    elif step == 'buy_choose_method':
        method = message.text

        if method == "Готівка":
            user_data[uid]['method'] = "Готівка"
            await finalize_buy(uid, message)
            return

        user_data[uid]['method'] = method

        await message.answer("Надішліть реквізити для отримання коштів.\nВведіть ПІБ отримувача:", reply_markup=types.ReplyKeyboardRemove())
        user_data[uid]['step'] = 'buy_enter_name'

    elif step == 'buy_enter_name':
        name = message.text.strip()
        if all(c.isalpha() or c.isspace() for c in name):
            user_data[uid]['name'] = name
            await message.answer("Введіть IBAN (26 цифровий номер рахунку):")
            user_data[uid]['step'] = 'buy_enter_iban'
        else:
            await message.answer("Будь ласка, введіть ПІБ тільки латиницею.")

    elif step == 'buy_enter_iban':
        iban = message.text.replace(' ', '')
        if len(iban) == 26 and iban.isalnum():
            user_data[uid]['iban'] = iban
            await message.answer("Введіть ІПН/ЄДРПОУ:")
            user_data[uid]['step'] = 'buy_enter_inp'
        else:
            await message.answer("Невірний IBAN (26 символів).")

    elif step == 'buy_enter_inp':
        user_data[uid]['inp'] = message.text
        await message.answer("Введіть номер карти:")
        user_data[uid]['step'] = 'buy_enter_card'

    elif step == 'buy_enter_card':
        user_data[uid]['card'] = message.text
        await finalize_buy(uid, message)

    # ===== ПРОДАЖ метод =====
    elif step == 'choose_method':
        if message.text == "Готівка":
            user_data[uid]['method'] = "Готівка"
            await finalize_order(uid, message)

        elif message.text == "Bank Transfer":
            user_data[uid]['method'] = "Bank Transfer"
            await message.answer("Введіть IBAN (26 цифровий номер рахунку):", reply_markup=types.ReplyKeyboardRemove())
            user_data[uid]['step'] = 'enter_iban'

        else:
            await message.answer("Будь ласка, виберіть кнопку.")

    elif step == 'enter_iban':
        iban = message.text.replace(' ', '')
        if len(iban) == 26:
            user_data[uid]['iban'] = iban
            await message.answer("Введіть ПІБ отримувача:")
            user_data[uid]['step'] = 'enter_name'
        else:
            await message.answer("Невірний IBAN")

    elif step == 'enter_name':
        user_data[uid]['name'] = message.text
        await finalize_order(uid, message)

# ================= Final SELL =================
async def finalize_order(uid, message):
    order_id = random.randint(10000, 99999)
    d = user_data[uid]

    text = f"Дякуємо! Вашу заявку прийнято та передано в обробку.\n\nID: {order_id}\n" \
           f"{d['amount_uah']} UAH → {d['amount_pln']:.2f} PLN\n" \
           f"Метод: {d['method']}\n\n" \
           f"Очікуйте, будь-ласка - менеджер зв'яжеться з вами протягом 15 хвилин @batpay_ex_support"

    await message.answer(text, reply_markup=main_keyboard())

    admin_text = (
        f"Нова заявка!\nID: {order_id}\nUser: {message.from_user.full_name}\n"
        f"Telegram: @{message.from_user.username} (ID: {uid})\n"
        f"Сума: {d['amount_uah']} UAH → {d['amount_pln']:.2f} PLN\n"
        f"Метод: {d['method']}\n"
        f"ПІБ: {d.get('name','')}\n"
        f"IBAN: {d.get('iban','')}"
    )

    for admin in ADMINS:
        await bot.send_message(admin, admin_text)

    user_data[uid] = {}

# ================= Final BUY =================
async def finalize_buy(uid, message):
    order_id = random.randint(10000, 99999)
    d = user_data[uid]

    text = f"Дякуємо! Вашу заявку прийнято та передано в обробку.\n\nID: {order_id}\n" \
           f"Сума: {d['buy_amount_pln']:.2f} PLN → {d['buy_amount_uah']} UAH\n" \
           f"Метод: {d['method']}\n\n" \
           f"Очікуйте, будь-ласка - менеджер зв'яжеться з вами протягом 15 хвилин @batpay_ex_support"

    await message.answer(text, reply_markup=main_keyboard())

    admin_text = (
        f"Нова заявка!\nID: {order_id}\nUser: {message.from_user.full_name}\n"
        f"Telegram: @{message.from_user.username} (ID: {uid})\n"
        f"Сума: {d['buy_amount_pln']:.2f} PLN → {d['buy_amount_uah']} UAH\n"
        f"Метод: {d['method']}\n"
        f"ПІБ: {d.get('name','')}\n"
        f"IBAN: {d.get('iban','')}\n"
        f"ІПН/ЄДРПОУ: {d.get('inp','')}\n"
        f"Номер карти: {d.get('card','')}"
    )

    for admin in ADMINS:
        await bot.send_message(admin, admin_text)

    user_data[uid] = {}

# ================= Main =================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)