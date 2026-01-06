from telethon import events, Button
from client_session import client
from database import db
from config import CURRENCY, USD_SYMBOL, payment_config, EXCHANGE_RATE
import os

@client.on(events.CallbackQuery(pattern=b"profile"))
async def profile_handler(event):
    user_id = event.sender_id
    user = db.get_user(user_id)
    
    if not user:
        await event.answer("User not found.", alert=True)
        return
        
    balance = user[3]
    full_name = user[2]
    currency_pref = user[4] if len(user) > 4 else "INR"
    
    # Calculate display
    disp_balance_inr = balance
    disp_balance_usdt = "{:.2f}".format(balance / EXCHANGE_RATE)
    disp_balance = f"₹{disp_balance_inr} | ${disp_balance_usdt}"
    
    msg = (f"**USER PROFILE**\n"
           f"━━━━━━━━━━━━━━━━━━━━\n\n"
           f"Hello **{full_name}**,\n"
           f"**User ID:** `{user_id}`\n\n"
           f"**Total Balance:**\n"
           f"**{disp_balance}**\n\n"
           f"━━━━━━━━━━━━━━━━━━━━")
    
    buttons = [
        [Button.inline("➕ Add Funds", b"deposit")],
        [Button.inline("📦 My Orders", b"order_history")],
        [Button.inline("🔙 Back", b"back_home")]
    ]
    
    await event.edit(msg, buttons=buttons)

# my_orders_handler removed (using order_history version in referral.py)

@client.on(events.CallbackQuery(pattern=b"set_inr"))
async def set_inr(event):
    db.set_currency(event.sender_id, "INR")
    try:
        await event.answer("Currency set to INR 🇮🇳", alert=True)
        await profile_handler(event)
    except Exception:
        pass # Ignore if already INR

@client.on(events.CallbackQuery(pattern=b"set_usdt"))
async def set_usdt(event):
    db.set_currency(event.sender_id, "USDT")
    try:
        await event.answer("Currency set to USDT 💵", alert=True)
        await profile_handler(event)
    except Exception:
        pass # Ignore if already USDT

@client.on(events.CallbackQuery(pattern=b"deposit"))
async def deposit_menu(event):
    msg = (f"**ADD FUNDS**\n"
           f"━━━━━━━━━━━━━━━━━━━━\n\n"
           f"Select your preferred payment network below.\n\n"
           f"**Important:** Please send only the supported asset to the respective address.")
           
    buttons = [
        [Button.inline("💠 Polygon (USDT)", b"pay_poly"), Button.inline("🔴 TRC20 (USDT)", b"pay_trc20")],
        [Button.inline("🟡 BEP20 (USDT)", b"pay_bep20"), Button.inline("💎 TON (TON)", b"pay_ton")],
        [Button.inline("🇮🇳 UPI (INR)", b"pay_inr")],
        [Button.inline("🔙 Back", b"profile")]
    ]
    await event.edit(msg, buttons=buttons)

@client.on(events.CallbackQuery(pattern=b"pay_inr"))
async def pay_inr(event):
    upi = payment_config.get("UPI", "Not Set")
    msg = (f"**UPI PAYMENT**\n"
           f"━━━━━━━━━━━━━━━━━━━━\n\n"
           f"**UPI ID:** `{upi}`\n\n"
           f"1. Send the amount to the UPI ID above.\n"
           f"2. Save the payment screenshot.\n"
           f"3. Send the screenshot to @your_support_bot\n\n"
           f"**Status:** Funds will be added manually after verification.")
           
    # Check for QR Code
    if os.path.exists("qr_code.jpg"):
        await event.delete() # Delete old menu to send fresh photo
        buttons = [[Button.inline("🔙 Back", b"deposit")]]
        await client.send_file(
            event.chat_id, 
            "qr_code.jpg", 
            caption=msg, 
            buttons=buttons
        )
    else:
        buttons = [[Button.inline("🔙 Back", b"deposit")]]
        await event.edit(msg, buttons=buttons)

@client.on(events.CallbackQuery(pattern=b"pay_poly"))
async def pay_poly(event):
    addr = "your_polygon_address_here"
    msg = (f"**POLYGON NETWORK**\n"
           f"━━━━━━━━━━━━━━━━━━━━\n\n"
           f"**USDT (Polygon) Address:**\n`{addr}`\n\n"
           f"1. Send USDT (Polygon) to the address above.\n"
           f"2. Copy the Transaction Hash (TXID).\n"
           f"3. Send the TXID to @your_support_bot\n\n"
           f"**Features:** Fast & Extremely Low Fees")
    
    if os.path.exists("qr_poly.jpg"):
        await event.delete()
        await client.send_file(event.chat_id, "qr_poly.jpg", caption=msg, buttons=[[Button.inline("🔙 Back", b"deposit")]])
    else:
        await event.edit(msg, buttons=[[Button.inline("🔙 Back", b"deposit")]])

@client.on(events.CallbackQuery(pattern=b"pay_trc20"))
async def pay_trc20(event):
    addr = "your_trc20_address_here"
    msg = (f"**TRON (TRC20) NETWORK**\n"
           f"━━━━━━━━━━━━━━━━━━━━\n\n"
           f"**USDT (TRC20) Address:**\n`{addr}`\n\n"
           f"1. Send USDT (TRC20) to the address above.\n"
           f"2. Copy the Transaction Hash (TXID).\n"
           f"3. Send the TXID to @your_support_bot")
    
    if os.path.exists("qr_trc20.jpg"):
        await event.delete()
        await client.send_file(event.chat_id, "qr_trc20.jpg", caption=msg, buttons=[[Button.inline("🔙 Back", b"deposit")]])
    else:
        await event.edit(msg, buttons=[[Button.inline("🔙 Back", b"deposit")]])

@client.on(events.CallbackQuery(pattern=b"pay_bep20"))
async def pay_bep20(event):
    addr = "your_bep20_address_here"
    msg = (f"**BNB SMART CHAIN**\n"
           f"━━━━━━━━━━━━━━━━━━━━\n\n"
           f"**USDT (BEP20) Address:**\n`{addr}`\n\n"
           f"1. Send USDT (BEP20) to the address above.\n"
           f"2. Copy the Transaction Hash (TXID).\n"
           f"3. Send the TXID to @your_support_bot")
    
    if os.path.exists("qr_bep20.jpg"):
        await event.delete()
        await client.send_file(event.chat_id, "qr_bep20.jpg", caption=msg, buttons=[[Button.inline("🔙 Back", b"deposit")]])
    else:
        await event.edit(msg, buttons=[[Button.inline("🔙 Back", b"deposit")]])

@client.on(events.CallbackQuery(pattern=b"pay_ton"))
async def pay_ton(event):
    addr = "your_ton_address_here"
    msg = (f"**TON NETWORK**\n"
           f"━━━━━━━━━━━━━━━━━━━━\n\n"
           f"**TON Address:**\n`{addr}`\n\n"
           f"1. Send TON to the address above.\n"
           f"2. Copy the Transaction Hash (TXID).\n"
           f"3. Send the TXID to @your_support_bot\n\n"
           f"**Caution:** Always double-check the address!")
    
    if os.path.exists("qr_ton.jpg"):
        await event.delete()
        await client.send_file(event.chat_id, "qr_ton.jpg", caption=msg, buttons=[[Button.inline("🔙 Back", b"deposit")]])
    else:
        await event.edit(msg, buttons=[[Button.inline("🔙 Back", b"deposit")]])
