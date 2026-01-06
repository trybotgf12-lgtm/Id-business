from telethon import events, Button
from client_session import client
from database import db
from config import CURRENCY, USD_SYMBOL, EXCHANGE_RATE, ADMINS, LOG_CHANNEL_ID, SOLD_LOG_GROUP_ID
import json
import asyncio
import os
from utils.session import get_otp
from utils.log_manager import send_log

def is_admin(user_id):
    return user_id in ADMINS

# State for Shop (e.g. Custom Quantity)
shop_states = {}

# --- Shop Navigation ---
@client.on(events.CallbackQuery(pattern=b"shop_home"))
async def shop_home(event):
    admin_flag = is_admin(event.sender_id)
    categories = db.get_active_categories(is_admin=admin_flag)
    
    if not categories:
        await event.answer("No stock available right now!", alert=True)
        return

    buttons = []
    # Create buttons for each category
    for cat in categories:
        cat_id, cat_name = cat
        buttons.append([Button.inline(f"{cat_name}", f"cat_{cat_id}")])
    
    buttons.append([Button.inline("🔙 Back", b"back_home")])
    
    msg = (f"**SHOP CATEGORIES**\n"
           f"━━━━━━━━━━━━━━━━━━━━\n\n"
           f"Browse our services and select a category to begin.")
    
    await event.edit(msg, buttons=buttons)

# --- Category View (List Products) ---
@client.on(events.CallbackQuery(pattern=r"cat_(\d+)"))
async def category_view(event):
    cat_id = int(event.data.decode().split('_')[1])
    admin_flag = is_admin(event.sender_id)
    products = db.get_active_products(cat_id, is_admin=admin_flag)
    
    if not products:
        await event.answer("No products with stock available in this category.", alert=True)
        return

    buttons = []
    # Get user currency preference
    user = db.get_user(event.sender_id)
    # Default to INR if user not found (shouldn't happen) or currency is None
    currency = user[4] if (user and len(user) > 4) else "INR" 

    for prod in products:
        prod_id, _, name, _, price, _ = prod  # last _ is cat_discount
        
        # Calculate USDT price
        usd_price = "{:.2f}".format(price / EXCHANGE_RATE)
        display_price = f"₹{price} | ${usd_price}"
        
        buttons.append([Button.inline(f"{name} - {display_price}", f"prod_{prod_id}")])
    
    buttons.append([Button.inline("🔙 Back", b"shop_home")])
    
    msg = (f"**AVAILABLE ITEMS**\n"
           f"━━━━━━━━━━━━━━━━━━━━\n\n"
           f"Select a product to view details and purchase.")
    
    await event.edit(msg, buttons=buttons)

# --- Product Details ---
@client.on(events.CallbackQuery(pattern=r"prod_(\d+)"))
async def product_view(event):
    prod_id = int(event.data.decode().split('_')[1])
    product = db.get_product(prod_id)
    
    if not product:
        await event.answer("Product not found.", alert=True)
        return
        
    _, cat_id, name, desc, price = product
    stock_count = db.get_stock_count(prod_id)
    
    # Combined Currency Display
    usd_price = "{:.2f}".format(price / EXCHANGE_RATE)
    price_str = f"₹{price} | ${usd_price}"
    
    msg = (f"**ITEM DETAILS**\n"
           f"━━━━━━━━━━━━━━━━━━━━\n\n"
           f"**Product:** {name}\n"
           f"**Description:**\n{desc}\n\n"
           f"**Price:** {price_str}\n"
           f"**Stock:** {stock_count} units available\n\n"
           f"━━━━━━━━━━━━━━━━━━━━")
    
    buttons = [
        [Button.inline("💳 Buy Now", f"buy_{prod_id}")],
        [Button.inline("🔙 Back", f"cat_{cat_id}")]
    ]
    
    await event.edit(msg, buttons=buttons)

# --- Buying Logic ---
@client.on(events.CallbackQuery(pattern=r"buy_(\d+)"))
async def buy_handler(event):
    prod_id = int(event.data.decode().split('_')[1])
    
    # Ask for Quantity
    buttons = [
        [Button.inline("1", f"buyq_{prod_id}_1"), Button.inline("5", f"buyq_{prod_id}_5"), Button.inline("10", f"buyq_{prod_id}_10")],
        [Button.inline("✏️ Custom Amount", f"buyqcustom_{prod_id}")],
        [Button.inline("🔙 Cancel", f"prod_{prod_id}")]
    ]
    msg = (f"**SELECT QUANTITY**\n"
           f"━━━━━━━━━━━━━━━━━━━━\n\n"
           f"How many units of **{db.get_product(prod_id)[2]}** would you like to purchase?")
    await event.edit(msg, buttons=buttons)

@client.on(events.CallbackQuery(pattern=r"buyq_(\d+)_(\d+)"))
async def buy_qty_confirm(event):
    data_parts = event.data.decode().split('_')
    prod_id = int(data_parts[1])
    qty = int(data_parts[2])
    
    # Get Product, Category, and User Info
    product = db.get_product(prod_id)
    cat_id = product[1]
    name = product[2]
    price = product[4] # Base price in DB (usually INR or Base Currency)
    
    cat = db.get_category(cat_id)
    cat_name = cat[1] if cat else "General"
    
    user = db.get_user(event.sender_id)
    balance = user[3]
    currency_pref = user[4] if (user and len(user) > 4) else "INR"
    
    # Calculate Totals
    # Discount Precedence: User > Category > Global
    
    # 1. User Discount
    discount = db.get_discount(event.sender_id)
    discount_source = "User Special"
    
    # 2. Category Discount
    if discount == 0:
        cat_disc = db.get_category_discount(cat_id)
        if cat_disc > 0:
            discount = cat_disc
            discount_source = "Category Deal"
            
    # 3. Global Discount
    if discount == 0:
        global_disc = db.get_config("global_discount")
        if global_disc:
            try:
                discount = float(global_disc)
                discount_source = "Global Sale"
            except: pass

    total_price_base = price * qty
    discounted_price_base = total_price_base
    
    discount_text = ""
    if discount > 0:
        discounted_price_base = total_price_base * (1 - discount / 100)
        discount_text = f"\n🎉 **{discount_source}:** {discount}% OFF"
    
    # Combined Price Display
    disp_price_inr = discounted_price_base
    disp_price_usdt = "{:.2f}".format(discounted_price_base / EXCHANGE_RATE)
    
    orig_disp_inr = total_price_base
    orig_disp_usdt = "{:.2f}".format(total_price_base / EXCHANGE_RATE)
    
    currency_display = f"₹{disp_price_inr} | ${disp_price_usdt}"
    orig_display = f"₹{orig_disp_inr} | ${orig_disp_usdt}"

    # Check Stock availability for UI
    stock_count = db.get_stock_count(prod_id)
    if stock_count < qty:
        await event.answer(f"❌ Not enough stock! Only {stock_count} available.", alert=True)
        # Alert admin even at this stage
        alert_msg = (f"⚠️ **LOW STOCK ATTEMPT**\n\n"
                     f"📦 Product: **{cat_name} - {product[2]}**\n"
                     f"🛑 Stock: **{stock_count}**\n"
                     f"🔢 Qty Sought: **{qty}**\n"
                     f"👤 User: `{event.sender_id}`\n\n"
                     f"Please restock soon! ⚡")
        for admin_id in ADMINS:
            try: await client.send_message(admin_id, alert_msg)
            except Exception as e: print(f"Failed admin alert: {e}")
        try: await send_log(client, "alert", alert_msg)
        except Exception as e: print(f"Failed log alert: {e}")
        return

    buttons = [
        [Button.inline(f"✅ Pay {currency_display}", f"confirm_{prod_id}_{qty}")],
        [Button.inline("❌ Cancel", f"prod_{prod_id}")]
    ]
    
    price_line = f"• **Price:** {currency_display}"
    if discount > 0:
        price_line = f"• **Price:** ~~{orig_display}~~ ➡️ **{currency_display}**"

    # Balance display logic
    if currency_pref == "USDT":
        disp_balance = f"${'{:.2f}'.format(balance / EXCHANGE_RATE)}"
        disp_after = f"${'{:.2f}'.format((balance - discounted_price_base) / EXCHANGE_RATE)}"
    else:
        disp_balance = f"₹{balance}"
        disp_after = f"₹{balance - discounted_price_base}"

    msg = (f"**CONFIRM PURCHASE**\n"
           f"━━━━━━━━━━━━━━━━━━━━\n\n"
           f"**Category:** {cat_name}\n"
           f"**Quantity:** {qty} units\n"
           f"{price_line}{discount_text}\n\n"
           f"**Your Balance:** {disp_balance}\n"
           f"**After Purchase:** {disp_after}\n\n"
           f"━━━━━━━━━━━━━━━━━━━━\n\n"
           f"**You will receive:**\n"
           f"• Phone number for Telegram login\n"
           f"• OTP code automatically detected\n"
           f"• Account password (if applicable)\n\n"
           f"**Important:** Please be ready to login immediately after confirmation!")
           
    await event.edit(msg, buttons=buttons)


@client.on(events.CallbackQuery(pattern=r"confirm_(\d+)_(\d+)"))
async def confirm_buy(event):
    user_id = event.sender_id
    data_parts = event.data.decode().split('_')
    prod_id = int(data_parts[1])
    qty = int(data_parts[2])
    
    data, message = db.buy_item(user_id, prod_id, quantity=qty)
    
    if data:
        # Success!
        
        # --- Post-Purchase Logic (Immediate) ---
        
        # 1. Normalize data to list for processing
        items_list = data if isinstance(data, list) else [data]
        
        # 2. Award Referral Commission
        user_data = db.get_user(user_id)
        if user_data and len(user_data) > 8 and user_data[8]:
            referrer_id = user_data[8]
            prod_info = db.get_product(prod_id)
            base_price = prod_info[4]
            total_purchase = base_price * qty
            commission = total_purchase * 0.10
            db.add_deg_coins(referrer_id, commission)
            
            try:
                buyer_name = f"{user_data[2]}" if user_data[2] else f"User {user_id}"
                ref_stats = db.get_referral_stats(referrer_id)
                notify_msg = (f"**REFERRAL EARNING**\n"
                              f"━━━━━━━━━━━━━━━━━━━━\n\n"
                              f"You earned `{commission:.1f}` DEG Coins!\n\n"
                              f"**Referred User:** {buyer_name}\n"
                              f"**Purchase Amount:** ₹{total_purchase:.2f}\n"
                              f"**Your Commission:** {commission:.1f} coins\n\n"
                              f"━━━━━━━━━━━━━━━━━━━━\n"
                              f"**YOUR STATS:**\n"
                              f"• Total Coins: `{ref_stats['deg_coins']:.1f}`\n"
                              f"• Total Earned: `{ref_stats['total_coins_earned']:.1f}`\n\n"
                              f"Keep sharing to earn more! 🚀")
                await client.send_message(referrer_id, notify_msg)
            except Exception as e:
                print(f"Failed to notify referrer: {e}")

        # 3. Sale Logging & Stock Alerts
        prod_info = db.get_product(prod_id)
        prod_name = prod_info[2]
        user_info = db.get_user(user_id)
        username = f"@{user_info[1]}" if user_info[1] else f"[{user_id}]"

        # Check Stock Level Alert
        new_stock = db.get_stock_count(prod_id)
        if new_stock == 0:
             alert_msg = (f"⚠️ **STOCK FINISHED ALERT**\n\n"
                          f"📦 Product: **{prod_name}**\n"
                          f"🛑 Status: **OUT OF STOCK**\n\n"
                          f"Please restock soon! ⚡")
             for admin_id in ADMINS:
                 try: await client.send_message(admin_id, alert_msg)
                 except Exception as e: print(f"Failed admin alert: {e}")
             try: await send_log(client, "alert", alert_msg)
             except Exception as e: print(f"Failed log alert: {e}")

        # Sale Log
        if SOLD_LOG_GROUP_ID:
            try:
                sensitive_msg = (f"🔐 **New Sale**\n"
                                 f"👤 User: {username} (`{user_id}`)\n"
                                 f"📦 Prod: {prod_name}\n"
                                 f"🔢 Qty: {qty}\n")
                
                text_content = ""
                for idx, item in enumerate(items_list):
                    text_content += f"--- Item {idx+1} ---\n"
                    try:
                        j = json.loads(item)
                        if isinstance(j, dict):
                            if "phone" in j: text_content += f"Phone: {j['phone']}\n"
                            if "session" in j: text_content += f"Session: {j['session']}\n"
                            if "password" in j: text_content += f"Password: {j['password']}\n"
                            for k, v in j.items():
                                if k not in ["phone", "session", "password", "type"]:
                                    text_content += f"{k}: {v}\n"
                        else: text_content += f"{item}\n"
                    except: text_content += f"{item}\n"
                    text_content += "\n"
                
                if len(text_content) > 3000:
                    import io
                    f = io.BytesIO(text_content.encode('utf-8'))
                    f.name = f"sale_{user_id}_{prod_id}.txt"
                    await send_log(client, "sold", sensitive_msg, file=f)
                else:
                    await send_log(client, "sold", sensitive_msg + f"```\n{text_content}\n```")
            except Exception as e:
                print(f"Failed to send sensitive log: {e}")

        # --- Delivery Flow ---
        
        # Check if items are sessions
        is_session = False
        try:
            item_json = json.loads(items_list[0])
            if isinstance(item_json, dict) and item_json.get("type") == "session":
                is_session = True
        except (json.JSONDecodeError, TypeError):
            pass

        # Delivery logic
        user = db.get_user(user_id)
        balance = user[3]

        if is_session:
            # Session flow
            shop_states[user_id] = {
                "state": "delivery_session", 
                "items": items_list, 
                "idx": 0,
                "total": len(items_list)
            }
            await deliver_next_session(event, user_id)
            return

        else:
            # Normal Item Flow
            clean_items = []
            for item in items_list:
                try:
                    j = json.loads(item)
                    if isinstance(j, dict):
                        line = j.get("data", "")
                        pwd = j.get("password")
                        if pwd: line += f" | Password: {pwd}"
                        clean_items.append(line)
                    else: clean_items.append(item)
                except: clean_items.append(item)

            if len(clean_items) > 1:
                filename = f"order_{user_id}_{prod_id}.txt"
                with open(filename, "w", encoding="utf-8") as f:
                    for item in clean_items:
                        f.write(f"{item}\n")
                
                await event.edit(f"**PURCHASE SUCCESS**\n"
                                 f"━━━━━━━━━━━━━━━━━━━━\n\n"
                                 f"**Quantity:** {qty}\n"
                                 f"**Your items are attached in the file below.**\n\n"
                                 f"**Remaining Balance:** ₹{balance}",
                                 buttons=[[Button.inline("🔙 Back to Home", b"back_home")]])
                
                await client.send_file(event.chat_id, filename, caption="📦 Here are your items.")
                os.remove(filename)
            else:
                item_data = items_list[0]
                display_text = ""
                try:
                    j = json.loads(item_data)
                    if isinstance(j, dict):
                        display_text = f"`{j.get('data')}`"
                        if j.get("password"):
                            display_text += f"\n🔐 **Password:** `{j.get('password')}`"
                    else: display_text = f"`{item_data}`"
                except: display_text = f"`{item_data}`"
                    
                await event.edit(f"**PURCHASE SUCCESS**\n"
                                 f"━━━━━━━━━━━━━━━━━━━━\n\n"
                                 f"**Item Details:**\n{display_text}\n\n"
                                 f"**Remaining Balance:** ₹{balance}", 
                                 buttons=[[Button.inline("🔙 Back to Home", b"back_home")]])

            # Feedback request for non-session items
            await asyncio.sleep(2)
            feedback_msg = (f"**Thanks for trusting & Dealing with us** 🤝\n\n"
                            f"Join Our channel and Stay away From scammers\n"
                            f"📈 **Be Updated of everything**\n"
                            f"➖➖➖➖➖\n"
                            f"➠ VOUCHES ~ @your_proofs_channel\n"
                            f"➠ Support ~ @your_support_bot\n\n"
                            f"🖤 **Drop Review/Vouch and Rating out of 10 on our Deal** 👇")
            await client.send_message(event.chat_id, feedback_msg)
            shop_states[user_id] = {"state": "waiting_feedback"}
    else:
        # Failure (Low balance or No stock)
        await event.answer(f"❌ Error: {message}", alert=True)
        
        # Check if it was a missing stock error to alert admin
        if "stock" in message.lower():
             prod_info = db.get_product(prod_id)
             prod_name = prod_info[2] if prod_info else f"Unknown ({prod_id})"
             alert_msg = (f"⚠️ **STOCK DEPLETED ALERT**\n\n"
                          f"📦 Product: **{prod_name}**\n"
                          f"🛑 Status: **OUT OF STOCK**\n"
                          f"👤 Attempt by: {event.sender_id}\n\n"
                          f"Please restock soon! ⚡")
             for admin_id in ADMINS:
                 try: await client.send_message(admin_id, alert_msg)
                 except Exception as e: print(f"Failed admin alert: {e}")
             try: await send_log(client, "alert", alert_msg)
             except Exception as e: print(f"Failed log alert: {e}")

async def deliver_next_session(event, user_id):
    if user_id not in shop_states: return
    state = shop_states[user_id]
    items = state["items"]
    idx = state["idx"]
    total = state["total"]
    
    if idx >= total:
        await event.edit("**✅ All Accounts Delivered!**", buttons=[[Button.inline("🔙 Home", b"back_home")]])
        del shop_states[user_id]
        return

    # Get current item
    item_str = items[idx]
    try:
        item_json = json.loads(item_str)
        phone = item_json.get("phone", "Unknown")
        session_str = item_json.get("session")
        password = item_json.get("password")
    except:
        await event.respond("❌ Error parsing session data.")
        return

    # Navigation Buttons
    buttons = []
    if idx < total - 1:
        buttons.append([Button.inline(f"➡️ Next Account ({idx+2}/{total})", b"next_session_delivery")])
    else:
        buttons.append([Button.inline("🏁 Finish", b"finish_session_delivery")])
    
    pass_text = "\n🔐 **Password:** `your_password`"
    
    base_msg = (f"**📦 Account {idx+1}/{total}**\n\n"
                f"📱 **Phone:** `{phone}`{pass_text}\n"
                f"⏳ **You have 5 minutes to login.**\n"
                f"__Please login now.__\n\n")

    msg = await event.edit(base_msg + f"🔋 **Connecting to session for OTP...**", buttons=buttons)

    # Start OTP Listener
    current_listener_id = f"{user_id}_{idx}"
    shop_states[user_id]["listener_id"] = current_listener_id
    
    try:
        async for status in get_otp(session_str):
            # Check if user moved on (state changed or listener ID changed)
            if user_id not in shop_states or shop_states[user_id].get("listener_id") != current_listener_id:
                break
                
            # Check for Timeout
            if "Timeout" in status:
                # Notify Owner/Admins
                try:
                    user_info = await event.get_sender()
                    username = f"@{user_info.username}" if user_info.username else f"[{user_info.id}]"
                    for admin_id in ADMINS:
                        await client.send_message(admin_id, f"⚠️ **OTP Timeout Alert**\nUser {username} failed to login to `{phone}`.\nAuto-skipping to next.")
                except: pass
                
                await msg.respond(f"⏰ **Timeout for {phone}!** Moving to next account...")
                
                # Auto-Next Logic
                shop_states[user_id]["idx"] += 1
                shop_states[user_id]["listener_id"] = "switching" 
                await deliver_next_session(event, user_id)
                return # Stop this execution
                
            try:
                # Update message but keep buttons
                msg = await msg.edit(base_msg + f"{status}", buttons=buttons)
            except Exception:
                pass
    except Exception as e:
         pass 

@client.on(events.CallbackQuery(pattern=b"next_session_delivery"))
async def next_session_handler(event):
    user_id = event.sender_id
    if user_id in shop_states:
        shop_states[user_id]["idx"] += 1
        # "listener_id" change will stop the previous loop naturally (on next iteration)
        shop_states[user_id]["listener_id"] = "switching" 
        await deliver_next_session(event, user_id)

@client.on(events.CallbackQuery(pattern=b"finish_session_delivery"))
async def finish_session_handler(event):
    await event.edit("**✅ Order Complete!**\nThank you for purchasing.", buttons=[[Button.inline("🔙 Home", b"back_home")]])
    
    # Send Thanks and ask for Feedback
    feedback_msg = (f"**Thanks for trusting & Dealing with us** 🤝\n\n"
                    f"Join Our channel and Stay away From scammers\n"
                    f"📈 **Be Updated of everything**\n"
                    f"➖➖➖➖➖\n"
                    f"➠ VOUCHES ~ @your_vouches_channel\n"
                    f"➠ Store  ~ @your_store_channel\n"
                    f"➠ Support ~ @your_support_bot\n\n"
                    f"🖤 **Drop Review/Vouch and Rating out of 10 on our Deal** 👇")
    
    await client.send_message(event.chat_id, feedback_msg)
    
    if event.sender_id in shop_states:
        shop_states[event.sender_id] = {"state": "waiting_feedback"} # Reuse state
    else:
        shop_states[event.sender_id] = {"state": "waiting_feedback"}

@client.on(events.CallbackQuery(pattern=b"stop_otp_silent"))
async def stop_otp_silent(event):
    await event.answer("Listener Stopped. Click Next/Finish.", alert=True)
    if event.sender_id in shop_states:
        shop_states[event.sender_id]["listener_id"] = "stopped"

@client.on(events.CallbackQuery(pattern=b"stop_reason_user"))
async def stop_otp_handler(event):
    await event.edit("🛑 **OTP Listener Stopped.**", buttons=[[Button.inline("🔙 Home", b"back_home")]])

@client.on(events.CallbackQuery(pattern=r"buyqcustom_(\d+)"))
async def buy_q_custom(event):
    prod_id = int(event.data.decode().split('_')[1])
    shop_states[event.sender_id] = {"state": "wait_qty", "prod_id": prod_id}
    await event.respond("🔢 Enter the **Quantity** you want to buy:")
    await event.answer()

@client.on(events.NewMessage())
async def shop_msg_handler(event):
    if event.sender_id not in shop_states: return
    
    state_data = shop_states[event.sender_id]
    state = state_data.get("state")
    
    if state == "waiting_feedback":
        try:
             user_info = await event.get_sender()
             sender_name = user_info.first_name if user_info.first_name else "User"
             # Clean name to prevent any accidental link parsing
             sender_name = sender_name.replace("@", "").replace("[", "").replace("]", "")
             
             msg_content = event.message.text if event.message.text else "[Media]"
             vouch_line = f"vouch:- {msg_content}"
             
             # Format as:
             # **Name**
             # vouch:- items got instantly!
             full_log_msg = f"**{sender_name}**\n{vouch_line}"
             
             # Send to the feedback topic as a COPY (prevents profile links and 'Forwarded from')
             if event.message.media:
                 await send_log(client, "vouch", full_log_msg, file=event.message.media)
             else:
                 await send_log(client, "vouch", full_log_msg)
                 
             await event.respond("✅ **Thank you for your feedback!**")
        except Exception as e:
             print(f"Error forwarding feedback: {e}")
        
        del shop_states[event.sender_id]
        return

    if state_data.get("state") == "wait_qty":
        try:
            qty = int(event.text)
            if qty < 1: raise ValueError
            
            prod_id = state_data["prod_id"]
            
            # Get Product, Category, and User Info
            product = db.get_product(prod_id)
            cat_id = product[1]
            name = product[2]
            price = product[4]
            
            cat = db.get_category(cat_id)
            cat_name = cat[1] if cat else "General"
            
            user = db.get_user(event.sender_id)
            balance = user[3]
            currency_pref = user[4] if (user and len(user) > 4) else "INR"
            
            # Discount Logic
            # 1. User Discount
            discount = db.get_discount(event.sender_id)
            discount_source = "User Special"
            
            # 2. Category Discount
            if discount == 0:
                cat_disc = db.get_category_discount(cat_id)
                if cat_disc > 0:
                    discount = cat_disc
                    discount_source = "Category Deal"
            
            # 3. Global Discount
            if discount == 0:
                global_disc = db.get_config("global_discount")
                if global_disc:
                    try:
                        discount = float(global_disc)
                        discount_source = "Global Sale"
                    except: pass

            total_price_base = price * qty
            discounted_price_base = total_price_base
            
            discount_text = ""
            if discount > 0:
                discounted_price_base = total_price_base * (1 - discount / 100)
                discount_text = f"\n🎉 **{discount_source}:** {discount}% OFF"
            
            # Combined Price Display
            disp_price_inr = discounted_price_base
            disp_price_usdt = "{:.2f}".format(discounted_price_base / EXCHANGE_RATE)
            
            orig_disp_inr = total_price_base
            orig_disp_usdt = "{:.2f}".format(total_price_base / EXCHANGE_RATE)
            
            currency_display = f"₹{disp_price_inr} | ${disp_price_usdt}"
            orig_display = f"₹{orig_disp_inr} | ${orig_disp_usdt}"
            
            stock_count = db.get_stock_count(prod_id)
            if stock_count < qty:
                await event.respond(f"❌ Not enough stock! Only {stock_count} available.")
                return

            buttons = [
                [Button.inline(f"✅ Pay {currency_display}", f"confirm_{prod_id}_{qty}")],
                [Button.inline("❌ Cancel", f"prod_{prod_id}")]
            ]
            
            price_line = f"• **Price:** {currency_display}"
            if discount > 0:
                price_line = f"• **Price:** ~~{orig_display}~~ ➡️ **{currency_display}**"
            
            # Balance display logic
            if currency_pref == "USDT":
                disp_balance = f"${'{:.2f}'.format(balance / EXCHANGE_RATE)}"
                disp_after = f"${'{:.2f}'.format((balance - discounted_price_base) / EXCHANGE_RATE)}"
            else:
                disp_balance = f"₹{balance}"
                disp_after = f"₹{balance - discounted_price_base}"

            msg = (f"**CONFIRM PURCHASE**\n"
                   f"━━━━━━━━━━━━━━━━━━━━\n\n"
                   f"**Category:** {cat_name}\n"
                   f"**Quantity:** {qty} units\n"
                   f"{price_line}{discount_text}\n\n"
                   f"**Your Balance:** {disp_balance}\n"
                   f"**After Purchase:** {disp_after}\n\n"
                   f"━━━━━━━━━━━━━━━━━━━━\n\n"
                   f"**You will receive:**\n"
                   f"• Phone number for Telegram login\n"
                   f"• OTP code automatically detected\n"
                   f"• Account password (if applicable)\n\n"
                   f"**Important:** Please be ready to login immediately after confirmation!")

            await event.respond(msg, buttons=buttons)
            
            del shop_states[event.sender_id]
            
        except ValueError:
            await event.respond("❌ Invalid number. Enter a valid quantity (e.g. 5).")
