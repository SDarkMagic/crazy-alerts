import server
import twitch
import queue
import os
import threading
import asyncio

def start_bot(q):
    async def start(q):
        token = os.getenv('OAUTH_TOKEN')
        secret = os.getenv('CLIENT_SECRET')
        channel = os.getenv('START_CHANNEL')
        client_id = os.getenv('CLIENT_ID')
        bot = twitch.Bot(token, secret, channel, q)
        await bot.start()
    asyncio.run(start(q))

def main():
    mem = queue.Queue()
    listener_thread = threading.Thread(target=start_bot, args=[mem])
    listener_thread.start()
    server.start(mem)

    listener_thread.join()
    mem.join()
    return

if __name__ == '__main__':
    main()