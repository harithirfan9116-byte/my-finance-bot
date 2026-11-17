
import logging
from datetime import date

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from config import BOT_TOKEN

from database import (
    add_transaction,
    get_transactions,
    get_summary,
    get_monthly_report,
    reset_transactions,
    delete_transaction
)


# LOGGING
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)


# MAIN MENU
def main_menu():

    keyboard = [
        [
            InlineKeyboardButton("💰 Income", callback_data="income"),
            InlineKeyboardButton("💸 Expense", callback_data="expense")
        ],
        [
            InlineKeyboardButton("📊 Dashboard", callback_data="dashboard"),
            InlineKeyboardButton("📜 History", callback_data="history")
        ],
        [
            InlineKeyboardButton("📅 Monthly Report", callback_data="monthly_report")
        ],
        [
            InlineKeyboardButton("⚙️ Settings", callback_data="settings")
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


# BUILD TRANSACTION HISTORY
def build_history(user_id):

    transactions = get_transactions(user_id)

    if not transactions:

        text = (
            "📜 TRANSACTION HISTORY\n\n"
            "No transactions recorded yet."
        )

        keyboard = [
            [InlineKeyboardButton("🏠 Main Menu", callback_data="home")]
        ]

        return text, InlineKeyboardMarkup(keyboard)

    text = "📜 TRANSACTION HISTORY\n\n"
    keyboard = []

    for display_id, item in enumerate(transactions[:10], start=1):

        actual_id = item[0]
        transaction_type = item[2]
        amount = item[3]
        category = item[4]
        transaction_date = item[6]

        emoji = "💰" if transaction_type == "income" else "💸"

        text += (
            f"{emoji} {transaction_type.upper()}\n"
            f"RM {amount:.2f}\n"
            f"Category: {category}\n"
            f"Date: {transaction_date}\n"
            f"ID: {display_id}\n\n"
        )

        keyboard.append([
            InlineKeyboardButton(
                f"🗑 Delete #{display_id}",
                callback_data=f"delete_tx_{actual_id}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton("🏠 Main Menu", callback_data="home")
    ])

    return text, InlineKeyboardMarkup(keyboard)


# START COMMAND
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data.clear()

    await update.message.reply_text(
        "💰 WELCOME TO MY FINANCE!\n\n"
        "Manage your money easily.\n"
        "Choose your action below:",
        reply_markup=main_menu()
    )


# HANDLE BUTTON
async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    action = query.data

    # HOME
    if action == "home":

        context.user_data.clear()

        await query.edit_message_text(
            "💰 MY FINANCE\n\nChoose your action:",
            reply_markup=main_menu()
        )

    # INCOME OR EXPENSE
    elif action in ["income", "expense"]:

        context.user_data.clear()
        context.user_data["transaction_type"] = action

        title = "INCOME" if action == "income" else "EXPENSE"

        await query.edit_message_text(
            f"💰 {title}\n\n"
            "Please enter the amount in RM.\n\n"
            "Example: 500 or 25.50",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel", callback_data="home")]
            ])
        )

    # DASHBOARD
    elif action == "dashboard":

        income, expense = get_summary(user_id)
        balance = income - expense

        await query.edit_message_text(
            "📊 MY FINANCE DASHBOARD\n\n"
            f"💰 Total Income: RM {income:.2f}\n"
            f"💸 Total Expense: RM {expense:.2f}\n"
            "━━━━━━━━━━━━━━\n"
            f"💵 Balance: RM {balance:.2f}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh", callback_data="dashboard")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="home")]
            ])
        )

    # HISTORY
    elif action == "history":

        text, keyboard = build_history(user_id)

        await query.edit_message_text(
            text,
            reply_markup=keyboard
        )

    # DELETE TRANSACTION - ASK CONFIRMATION
    elif action.startswith("delete_tx_"):

        transaction_id = int(action.replace("delete_tx_", ""))

        await query.edit_message_text(
            "⚠️ DELETE TRANSACTION\n\n"
            "Are you sure you want to delete this transaction?\n\n"
            "This action cannot be undone.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "✅ Yes, Delete",
                        callback_data=f"confirm_delete_{transaction_id}"
                    ),
                    InlineKeyboardButton(
                        "❌ Cancel",
                        callback_data="cancel_delete"
                    )
                ]
            ])
        )

    # CONFIRM DELETE TRANSACTION
    elif action.startswith("confirm_delete_"):

        transaction_id = int(action.replace("confirm_delete_", ""))

        deleted = delete_transaction(transaction_id, user_id)

        if deleted:

            text, keyboard = build_history(user_id)

            await query.edit_message_text(
                "✅ Transaction deleted successfully!\n\n" + text,
                reply_markup=keyboard
            )

        else:

            await query.edit_message_text(
                "❌ Transaction not found or already deleted.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📜 Back to History", callback_data="history")],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="home")]
                ])
            )

    # CANCEL DELETE
    elif action == "cancel_delete":

        text, keyboard = build_history(user_id)

        await query.edit_message_text(
            text,
            reply_markup=keyboard
        )

    # MONTHLY REPORT
    elif action == "monthly_report":

        income, expense, balance, top_category, category_amount = (
            get_monthly_report(user_id)
        )

        current_month = date.today().strftime("%B %Y")

        await query.edit_message_text(
            "📅 MONTHLY FINANCIAL REPORT\n\n"
            f"Month: {current_month}\n"
            "━━━━━━━━━━━━━━\n"
            f"💰 Total Income: RM {income:.2f}\n"
            f"💸 Total Expense: RM {expense:.2f}\n"
            f"💵 Balance: RM {balance:.2f}\n"
            "━━━━━━━━━━━━━━\n"
            "🏆 Highest Expense Category:\n"
            f"{top_category} - RM {category_amount:.2f}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh", callback_data="monthly_report")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="home")]
            ])
        )

    # SETTINGS
    elif action == "settings":

        await query.edit_message_text(
            "⚙️ SETTINGS\n\nChoose an option:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🗑 Reset All Transactions", callback_data="reset")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="home")]
            ])
        )

    # RESET CONFIRMATION
    elif action == "reset":

        await query.edit_message_text(
            "⚠️ RESET ALL TRANSACTIONS\n\n"
            "Are you sure you want to delete all your records?\n"
            "This action cannot be undone.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Yes, Reset", callback_data="confirm_reset"),
                    InlineKeyboardButton("❌ Cancel", callback_data="settings")
                ]
            ])
        )

    # CONFIRM RESET
    elif action == "confirm_reset":

        deleted = reset_transactions(user_id)

        context.user_data.clear()

        await query.edit_message_text(
            "✅ Reset successful!\n\n"
            f"{deleted} transaction(s) deleted.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Main Menu", callback_data="home")]
            ])
        )

    # SAVE TRANSACTION
    elif action.startswith("category_"):

        category = action.replace("category_", "")

        transaction_type = context.user_data.get("transaction_type")
        amount = context.user_data.get("amount")

        if not transaction_type or amount is None:

            context.user_data.clear()

            await query.edit_message_text(
                "Session expired. Please start again.",
                reply_markup=main_menu()
            )

            return

        add_transaction(
            user_id,
            transaction_type,
            amount,
            category,
            "",
            date.today().isoformat()
        )

        context.user_data.clear()

        await query.edit_message_text(
            "✅ TRANSACTION SAVED!\n\n"
            f"Type: {transaction_type.upper()}\n"
            f"Amount: RM {amount:.2f}\n"
            f"Category: {category}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Main Menu", callback_data="home")]
            ])
        )


# RECEIVE AMOUNT
async def amount_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if "transaction_type" not in context.user_data:

        await update.message.reply_text(
            "Please choose Income or Expense from the main menu.",
            reply_markup=main_menu()
        )

        return

    try:

        amount = float(update.message.text.replace(",", "").strip())

        if amount <= 0 or amount > 100000000:
            raise ValueError

        if round(amount, 2) != amount:
            raise ValueError

    except ValueError:

        await update.message.reply_text(
            "❌ Invalid amount.\n"
            "Please enter a valid amount, for example 500 or 25.50."
        )

        return

    context.user_data["amount"] = amount

    transaction_type = context.user_data["transaction_type"]

    if transaction_type == "income":

        categories = [
            "Allowance",
            "Salary",
            "Part-time",
            "Other"
        ]

    else:

        categories = [
            "Food",
            "Transport",
            "Shopping",
            "Education",
            "Entertainment",
            "Bills",
            "Other"
        ]

    keyboard = []

    for category in categories:

        keyboard.append([
            InlineKeyboardButton(
                category,
                callback_data=f"category_{category}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton("❌ Cancel", callback_data="home")
    ])

    await update.message.reply_text(
        f"Amount: RM {amount:.2f}\n\n"
        "Please choose a category:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ERROR HANDLER
async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):

    logger.error(
        "Error occurred:",
        exc_info=context.error
    )


# MAIN
def main():

    print("Starting My Finance Bot...")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        CallbackQueryHandler(button_handler)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            amount_handler
        )
    )

    app.add_error_handler(error_handler)

    print("Waiting for Telegram messages...")

    app.run_polling()


if __name__ == "__main__":
    main()
