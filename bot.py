import logging
import os
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

# --- Настройки логирования ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TOKEN") 

if BOT_TOKEN is not None:
    print(f"token is set")
else:
    print(f"token is NOT set")
    raise EnvironmentError(f"Required environment variable token is not set.")

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

# --- Шаги диалога ---
CHOOSE_BUY, ENTER_AMOUNT, CHOOSE_PAY = range(3)


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

    await query.edit_message_text(
        f"Вы выбрали: *{currency}*\n\nСколько хотите купить? Введите число (не более 5 единиц валюты за один обмен):",
        parse_mode="Markdown",
    )
    return ENTER_AMOUNT


async def enter_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Игрок ввёл количество."""
    text = update.message.text.strip().replace(",", ".")

    try:
        amount = float(text)
    except ValueError:
        await update.message.reply_text(
            "Укажите количество цифрами, например: 6"
        )
        return ENTER_AMOUNT

    if amount <= 0:
        await update.message.reply_text(
            "Количество должно быть больше нуля."
        )
        return ENTER_AMOUNT

    if amount > 5:
        await update.message.reply_text(
            "За один обмен можно купить не более 5 единиц валюты."
        )
        return ENTER_AMOUNT

    context.user_data["amount"] = amount
    buy_currency = context.user_data["buy_currency"]

    await update.message.reply_text(
        f"Покупаем *{amount:g} {buy_currency}*.\n\nКакой валютой будете платить?",
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

    await query.edit_message_text(
        f"Для того, чтобы купить *{amount:g} {buy_currency}* — заплатите *{result_str} {pay_currency}*!",
        parse_mode="Markdown",
    )

    # Предлагаем начать заново
    await query.message.reply_text(
        "Вы можете написать об этом личное сообщение деду Егору (@iskuzmin) и произвести интересующий вас обмен\n\nХотите рассчитать ещё один обмен? Напишите /start",
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
            ENTER_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_amount)],
            CHOOSE_PAY: [CallbackQueryHandler(choose_pay_currency)],
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
