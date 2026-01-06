from telethon import events, Button, functions
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.errors import UserNotParticipantError
from client_session import client
from config import FORCE_JOIN_CHANNELS, ADMINS
import asyncio

@client.on(events.NewMessage(incoming=True))
async def force_join_group_middleware(event):
    if not event.is_group:
        return

    if not FORCE_JOIN_CHANNELS:
        return

    sender = await event.get_sender()
    if not sender:
        return

    if sender.id in ADMINS:
        return
        
    missing_channels = []
    for channel_id in FORCE_JOIN_CHANNELS:
        try:
            await client(GetParticipantRequest(channel=channel_id, participant=sender.id))
        except UserNotParticipantError:
            missing_channels.append(channel_id)
        except Exception:
             continue

    if missing_channels:
        try:
            await event.delete()
        except:
            return 

        buttons = []
        for ch in missing_channels:
            try:
                entity = await client.get_entity(ch)
                if hasattr(entity, 'username') and entity.username:
                    url = f"https://t.me/{entity.username}"
                    name = entity.title or entity.username
                else:
                    url = f"https://t.me/c/{str(ch).replace('-100', '')}/1" 
                    name = getattr(entity, 'title', f"Channel {ch}")
                buttons.append([Button.url(f"Join {name}", url)])
            except:
                buttons.append([Button.url(f"Join Channel", f"https://t.me/telegram")])

        text = (f"Hello **{sender.first_name}**,\n\n"
                f"**Access Denied**\n"
                f"You must join our channels to send messages in this group.")

        try:
            warning_msg = await event.respond(text, buttons=buttons)
            await asyncio.sleep(15)
            await warning_msg.delete()
        except:
            pass
