from telethon import functions, types
from database import db
from config import SOLD_LOG_GROUP_ID

async def get_or_create_topic(client, group_id, title, config_key):
    existing_id = db.get_config(config_key)
    if existing_id:
        return int(existing_id)
    
    try:
        result = await client(functions.channels.CreateForumTopicRequest(
            channel=group_id,
            title=title
        ))
        topic_id = None
        for update in result.updates:
            if isinstance(update, types.UpdateMessageID):
                topic_id = update.id
            if isinstance(update, types.UpdateNewChannelMessage):
                 if isinstance(update.message, types.MessageService):
                      if isinstance(update.message.action, types.MessageActionTopicCreate):
                           topic_id = update.message.id
                           
        if topic_id:
            db.set_config(config_key, topic_id)
            return topic_id
    except Exception as e:
        print(f"Error creating topic: {e}")
    return None

async def send_log(client, category, message, file=None):
    if not SOLD_LOG_GROUP_ID: return
    
    topic_map = {
        "sold": ("🛒 Sold Accounts", "topic_sold_id"),
        "stock": ("📥 Stock Updates", "topic_stock_id"),
        "vouch": ("⭐ Vouches", "topic_vouch_id"),
        "alert": ("⚠️ Stock Alerts", "topic_alert_id")
    }
    
    if category not in topic_map: return
    title, key = topic_map[category]
    topic_id = await get_or_create_topic(client, SOLD_LOG_GROUP_ID, title, key)
    
    try:
        if file:
            await client.send_file(SOLD_LOG_GROUP_ID, file, caption=message, reply_to=topic_id)
        else:
            await client.send_message(SOLD_LOG_GROUP_ID, message, reply_to=topic_id)
    except:
        try:
             if file: await client.send_file(SOLD_LOG_GROUP_ID, file, caption=message)
             else: await client.send_message(SOLD_LOG_GROUP_ID, message)
        except: pass
