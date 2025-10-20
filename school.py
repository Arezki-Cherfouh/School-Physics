import os
from telethon import TelegramClient
import asyncio
from dotenv import load_dotenv
load_dotenv()
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
group_username = os.getenv("GROUP_USERNAME")
client = TelegramClient("session_name", api_id, api_hash)
# +213542859814
async def get_images():
    await client.start()
    os.makedirs("Exercices", exist_ok=True)
    async for msg in client.iter_messages(group_username):
        if msg.photo or (msg.document and msg.document.mime_type and msg.document.mime_type.startswith("image/")):
            file_name = f"Exercices/{msg.id}.jpg"
            if os.path.exists(file_name):
                print(f"Already downloaded {file_name}, skipping...")
                continue
            await msg.download_media(file=file_name)
            print(f"Downloaded {file_name}")
asyncio.run(get_images())
# async def main():
#     await client.start()
#     async for dialog in client.iter_dialogs():
#         print(dialog.name, dialog.id)
# asyncio.run(main())        