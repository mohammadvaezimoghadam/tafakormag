import asyncio
import bale_bot
import telegram_bot


async def main():
    """اجرای همزمان ربات بله و ربات تلگرام در صورت فعال بودن"""
    import os
    enable_telegram = os.getenv("ENABLE_TELEGRAM", "false").lower() in ("true", "1", "yes")

    tasks = [bale_bot.run()]

    if enable_telegram:
        print("Starting Telegram bot...")
        tasks.append(telegram_bot.run())
    else:
        print("Telegram bot is disabled via ENABLE_TELEGRAM environment variable.")

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())