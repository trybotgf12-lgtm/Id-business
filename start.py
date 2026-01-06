from telethon import events, Button
from client_session import client
from database import db
from config import CURRENCY

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    sender = await event.get_sender()
    user_id = sender.id
    username = sender.username or ""
    full_name = f"{sender.first_name} {sender.last_name or ''}".strip()
    
    # Check for referral parameter
    referrer_id = None
    if event.message.text and len(event.message.text.split()) > 1:
        try:
            referrer_id = int(event.message.text.split()[1])
            if referrer_id == user_id:
                referrer_id = None
        except:
            pass
    
    # Register user
    db.add_user(user_id, username, full_name, referrer_id)
    
    msg = (f"**ACCOUNT STORE**\n"
           f"━━━━━━━━━━━━━━━━━━━━\n\n"
           f"Hello **{full_name}**,\n"
           f"Welcome to our trusted digital store.\n\n"
           f"**Why choose us?**\n"
           f"• Trusted & Verified Seller\n"
           f"• Instant Auto-Delivery\n"
           f"• 100% Secure Payments\n"
           f"• Refer & Earn Coins\n\n"
           f"━━━━━━━━━━━━━━━━━━━━\n"
           f"**Choose an action to begin:**")
    
    buttons = [
        [Button.inline("🛒 Shop", b"shop_home"), Button.inline("👤 Profile", b"profile")],
        [Button.inline("🔗 Referrals", b"referral"), Button.inline("🆘 Support", b"support")]
    ]
    
    await event.respond(msg, buttons=buttons)


@client.on(events.CallbackQuery(pattern=b"back_home"))
async def back_home_handler(event):
    sender = await event.get_sender()
    full_name = f"{sender.first_name} {sender.last_name or ''}".strip()
    
    msg = (f"**ACCOUNT STORE**\n"
           f"━━━━━━━━━━━━━━━━━━━━\n\n"
           f"Hello **{full_name}**,\n"
           f"Welcome back to the store.\n\n"
           f"**Why choose us?**\n"
           f"• Trusted & Verified Seller\n"
           f"• Instant Auto-Delivery\n"
           f"• 100% Secure Payments\n"
           f"• Refer & Earn Coins\n\n"
           f"━━━━━━━━━━━━━━━━━━━━\n"
           f"**Choose an action to begin:**")
    
    buttons = [
        [Button.inline("🛒 Shop", b"shop_home"), Button.inline("👤 Profile", b"profile")],
        [Button.inline("🔗 Referrals", b"referral"), Button.inline("🆘 Support", b"support")]
    ]
    
    await event.edit(msg, buttons=buttons)


@client.on(events.CallbackQuery(pattern=b"support"))
async def support_handler(event):
    msg = (f"**CUSTOMER SUPPORT**\n"
           f"━━━━━━━━━━━━━━━━━━━━\n\n"
           f"Need help? Our team is online!\n\n"
           f"**Support Bot:** @your_support_bot\n"
           f"**Hours:** 10:00 AM - 10:00 PM IST")
    
    buttons = [
        [Button.url("💬 Contact Now", "https://t.me/your_support_bot")],
        [Button.inline("🏠 Main Menu", b"back_home")]
    ]
    await event.edit(msg, buttons=buttons)
