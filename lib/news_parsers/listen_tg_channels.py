from telethon import TelegramClient, events
import const

# Замените на свои данные
api_id = 123456     # <-- твой API ID
api_hash = 'your_api_hash_here'  # <-- твой API HASH
session_name = 'session0'  # Название файла сессии

# Создание клиента
client = TelegramClient(session_name, api_id, api_hash)

# Обработчик новых сообщений
@client.on(events.NewMessage)
async def handler(event):
    sender = await event.get_sender()
    chat = await event.get_chat()
    print(f"[{chat.title}] {event.text}")

# Запуск клиента
client.start()
print("Listening to Telegram channels...")

client.run_until_disconnected()
