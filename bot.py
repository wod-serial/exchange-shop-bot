import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

BOT_TOKEN = os.getenv("TOKEN") 

if BOT_TOKEN is not None:
    print(f"token is set")
else:
    print(f"token is NOT set")
    raise EnvironmentError(f"Required environment variable token is not set.")

# --- Настройки логирования ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Валюты и коэффициенты ---
SELL_COEFFICIENTS = {
    "Золото АД":        0.3,
    "Обол":             0.2,
    "Красный талон":    0.3,
    "Пеггат":           0.6,
    "Золотая корона":   0.6,
    "Серебряная корона":0.1,
    "Топаз":            0.3,
    "Гранат":           0.3,
    "Опал":             0.3,
    "Аметист":          0.2,
    "Берилл":           0.2,
}

BUY_COEFFICIENTS = {
    "Золото АД":        0.1,
    "Обол":             0.1,
    "Красный талон":    0.2,
    "Пеггат":           0.4,
    "Золотая корона":   0.4,
    "Серебряная корона":0.1,
    "Топаз":            0.2,
    "Гранат":           0.2,
    "Опал":             0.2,
    "Аметист":          0.1,
    "Берилл":           0.1,
}

CURRENCIES = list(SELL_COEFFICIENTS.keys())

# --- Склонения валют (1, 2-4, 5+) ---
CURRENCY_FORMS = {
    "Золото АД":         ("Золото АД",        "Золота АД",        "Золота АД"),
    "Обол":              ("Обол",              "Обола",            "Оболов"),
    "Красный талон":     ("Красный талон",     "Красных талона",   "Красных талонов"),
    "Пеггат":            ("Пеггат",            "Пеггата",          "Пеггатов"),
    "Золотая корона":    ("Золотая корона",    "Золотых короны",   "Золотых корон"),
    "Серебряная корона": ("Серебряная корона", "Серебряных короны","Серебряных корон"),
    "Топаз":             ("Топаз",             "Топаза",           "Топазов"),
    "Гранат":            ("Гранат",            "Граната",          "Гранатов"),
    "Опал":              ("Опал",              "Опала",            "Опалов"),
    "Аметист":           ("Аметист",           "Аметиста",         "Аметистов"),
    "Берилл":            ("Берилл",            "Берилла",          "Бериллов"),
}

def decline(amount, currency):
    """Возвращает правильную форму названия валюты для заданного числа."""
    forms = CURRENCY_FORMS[currency]
    if amount % 100 in range(11, 20):
        return forms[2]
    rem = amount % 10
    if rem == 1:
        return forms[0]
    elif rem in (2, 3, 4):
        return forms[1]
    else:
        return forms[2]

# --- Шаги диалога ---
CHOOSE_BUY, ENTER_AMOUNT, CHOOSE_PAY, FINAL = range(4)


def make_currency_keyboard(exclude=None):
    """Создаёт клавиатуру с кнопками валют."""
    buttons = []
    row = []
    for currency in CURRENCIES:
        if currency == exclude:
            continue
        row.append(InlineKeyboardButton(currency, callback_data=currency))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start — начало диалога."""
    context.user_data.clear()
    await update.message.reply_text(
        "Добро пожаловать в обменный пункт «Щедрый Хотэй», расположенный в СТЗ.\n\nЧто хотите купить?",
        reply_markup=make_currency_keyboard(),
    )
    return CHOOSE_BUY


async def choose_buy_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Игрок выбрал валюту для покупки."""
    query = update.callback_query
    await query.answer()

    currency = query.data
    context.user_data["buy_currency"] = currency

    amount_keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("1", callback_data="amount_1"),
        InlineKeyboardButton("2", callback_data="amount_2"),
        InlineKeyboardButton("3", callback_data="amount_3"),
        InlineKeyboardButton("4", callback_data="amount_4"),
        InlineKeyboardButton("5", callback_data="amount_5"),
    ]])
    await query.edit_message_text(
        f"Вы выбрали: *{currency}*\n\nСколько хотите купить?",
        parse_mode="Markdown",
        reply_markup=amount_keyboard,
    )
    return ENTER_AMOUNT


async def enter_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Игрок нажал кнопку с количеством."""
    query = update.callback_query
    await query.answer()

    amount = int(query.data.split("_")[1])
    context.user_data["amount"] = amount
    buy_currency = context.user_data["buy_currency"]

    await query.edit_message_text(
        f"Покупаем *{amount} {decline(amount, buy_currency)}*.\n\nКакой валютой будете платить?",
        parse_mode="Markdown",
        reply_markup=make_currency_keyboard(exclude=buy_currency),
    )
    return CHOOSE_PAY


async def choose_pay_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Игрок выбрал валюту для оплаты — считаем результат."""
    query = update.callback_query
    await query.answer()

    pay_currency = query.data
    buy_currency = context.user_data["buy_currency"]
    amount = context.user_data["amount"]

    # Формула: (Y * коэф_продажи[X]) / коэф_покупки[Z] + 1
    result = (amount * SELL_COEFFICIENTS[buy_currency]) / BUY_COEFFICIENTS[pay_currency] + 1

    # Округляем вверх до целого
    import math
    result = math.ceil(result)
    result_str = str(result)

    final_keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("Начать новый обмен", callback_data="new_exchange"),
        InlineKeyboardButton("Завершить", callback_data="finish"),
    ]])
    await query.edit_message_text(
        f"Для того, чтобы купить *{amount} {decline(amount, buy_currency)}* — заплатите *{result_str} {decline(result, pay_currency)}*!\n\nВы можете написать об этом личное сообщение деду Егору (@iskuzmin) и произвести интересующий вас обмен",
        parse_mode="Markdown",
        reply_markup=final_keyboard,
    )

    return FINAL


async def handle_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопок на финальном экране."""
    query = update.callback_query
    await query.answer()

    if query.data == "new_exchange":
        context.user_data.clear()
        await query.edit_message_text(
            "Добро пожаловать в обменный пункт «Щедрый Хотэй», расположенный в СТЗ.

Что хотите купить?",
            reply_markup=make_currency_keyboard(),
        )
        return CHOOSE_BUY
    else:
        await query.edit_message_text(
            "Спасибо за визит в обменный пункт «Щедрый Хотэй»! До свидания."
        )
        return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена диалога."""
    context.user_data.clear()
    await update.message.reply_text(
        "Диалог отменён. Напишите /start чтобы начать заново."
    )
    return ConversationHandler.END


async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_BUY: [CallbackQueryHandler(choose_buy_currency)],
            ENTER_AMOUNT: [CallbackQueryHandler(enter_amount, pattern="^amount_")],
            CHOOSE_PAY: [CallbackQueryHandler(choose_pay_currency)],
            FINAL: [CallbackQueryHandler(handle_final, pattern="^(new_exchange|finish)$")],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
    )

    app.add_handler(conv_handler)

    print("Бот запущен. Нажми Ctrl+C для остановки.")
    async with app:
        await app.start()
        await app.updater.start_polling()
        await asyncio.Event().wait()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())