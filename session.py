import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from config import API_ID, API_HASH

async def parse_session_file(file_path):
    try:
        if not os.path.exists(file_path):
            return None, None, False

        session_name = file_path.replace('.session', '')
        client = TelegramClient(session_name, API_ID, API_HASH)
        await client.connect()
        
        if not await client.is_user_authorized():
            await client.disconnect()
            return None, None, False
            
        me = await client.get_me()
        phone = f"+{me.phone}" if me.phone else f"ID: {me.id}"
        
        string_session = StringSession()
        string_session.set_DC(client.session.dc_id, client.session.server_address, client.session.port)
        string_session.auth_key = client.session.auth_key
        saved_string = string_session.save()
        
        await client.disconnect()
        return saved_string, phone, True
    except Exception:
        return None, None, False

async def get_otp(session_string, timeout=300):
    client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
    await client.connect()
    
    if not await client.is_user_authorized():
        yield "❌ Session invalid."
        await client.disconnect()
        return

    me = await client.get_me()
    yield f"✅ Connected as {me.first_name}. Waiting for OTP..."
    
    otp_future = asyncio.get_running_loop().create_future()

    @client.on(events.NewMessage(from_users=[777000, 42777]))
    async def handler(event):
        import re
        code_match = re.search(r'\b\d{5}\b', event.text)
        if code_match and not otp_future.done():
            otp_future.set_result(code_match.group(0))

    try:
        await asyncio.wait_for(otp_future, timeout=timeout)
        yield f"🔑 **OTP RECEIVED:** `{otp_future.result()}`"
    except asyncio.TimeoutError:
        yield "⏰ Timeout."
    finally:
        await client.disconnect()
