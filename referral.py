from telethon import events, Button
import urllib.parse
from client_session import client
from database import db
from config import BOT_TOKEN

@client.on(events.CallbackQuery(pattern=b"referral"))
async def referral_handler(event):
    sender = await event.get_sender()
    user_id = sender.id
    stats = db.get_referral_stats(user_id)
    bot_info = await client.get_me()
    bot_username = bot_info.username
    referral_link = f"https://t.me/{bot_username}?start={user_id}"
    
    msg = (f"**REFERRAL SYSTEM**\n"
           f"━━━━━━━━━━━━━━━━━━━━\n\n"
           f"Share this link with your friends and earn **10% commission** for every successful purchase!\n\n"
           f"**Your Referral Link:**\n"
           f"`{referral_link}`\n\n"
           f"**YOUR STATS**\n"
           f"• Total Referrals: `{stats['total_referrals']}`\n"
           f"• Coins Earned: `{stats['total_coins_earned']:.1f}`")
    
    share_text = urllib.parse.quote("Join this store and get the best digital products instantly! 🚀")
    share_url = f"https://t.me/share/url?url={referral_link}&text={share_text}"
    
    buttons = [
        [Button.url("📤 Share Link", share_url)],
        [Button.inline("🏠 Back to Home", b"back_home")]
    ]
    await event.edit(msg, buttons=buttons)

@client.on(events.CallbackQuery(pattern=b"order_history"))
async def order_history_handler(event):
    sender = await event.get_sender()
    user_id = sender.id
    orders = db.get_user_orders(user_id)
    
    if not orders:
        msg = f"**ORDER HISTORY**\n━━━━━━━━━━━━━━━━━━━━\n\nNo orders found!"
    else:
        msg = f"**ORDER HISTORY**\n━━━━━━━━━━━━━━━━━━━━\n\nShowing your last 10 orders:\n\n"
        for order in orders[:10]:
            date, product_name, amount, _ = order
            msg += f"📦 **{product_name}**\n💰 ₹{amount:.2f} | 📅 {date}\n\n"
    
    await event.edit(msg, buttons=[[Button.inline("🔙 Back to Profile", b"profile")]])
