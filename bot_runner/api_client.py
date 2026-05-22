import os
import httpx
import logging
from config import VERIFY_LINK_URL, FETCH_TASKS_URL, BACKEND_API_URL

logger = logging.getLogger("api_client")
BOT_API_KEY = os.getenv("BOT_API_KEY", "")


class APIClient:
    def __init__(self):
        headers = {}
        if BOT_API_KEY.strip():
            headers["X-Bot-API-Key"] = BOT_API_KEY.strip()
        self.client = httpx.AsyncClient(timeout=10.0, headers=headers)

    async def verify_link(self, token: str, platform: str, chat_id: int) -> dict:
        payload = {
            "token": token,
            "platform": platform,
            "chat_id": str(chat_id)
        }
        try:
            resp = await self.client.post(VERIFY_LINK_URL, json=payload)
            resp.raise_for_status()
            logger.info(f"verify_link success for chat_id={chat_id}")
            return resp.json()
        except Exception as e:
            logger.error(f"verify_link failed: {e}")
            raise

    async def fetch_tasks(self) -> list:
        try:
            resp = await self.client.get(FETCH_TASKS_URL)
            resp.raise_for_status()
            data = resp.json()
            tasks = data if isinstance(data, list) else data.get("tasks", [])
            if tasks:
                logger.info(f"Fetched {len(tasks)} task(s)")
            return tasks
        except Exception as e:
            logger.error(f"fetch_tasks failed: {e}")
            return []

    async def complete_task(self, task_id: int, message_id: str = None) -> bool:
        url = f"{BACKEND_API_URL}/bot/tasks/{task_id}/"
        payload = {"message_id": message_id} if message_id else {}
        try:
            resp = await self.client.post(url, json=payload)
            resp.raise_for_status()
            logger.info(f"Task {task_id} completed, message_id={message_id}")
            return True
        except Exception as e:
            logger.error(f"complete_task {task_id} failed: {e}")
            return False

    async def register_destination(
        self, user_id: int, platform: str, chat_id: str, label: str
    ) -> dict:
        url = f"{BACKEND_API_URL}/bot/register-destination/"
        payload = {
            "user_id": user_id,
            "platform": platform,
            "chat_id": str(chat_id),
            "label": label,
        }
        try:
            resp = await self.client.post(url, json=payload)
            resp.raise_for_status()
            logger.info(f"Destination registered for user {user_id}: {label}")
            return resp.json()
        except Exception as e:
            logger.error(f"register_destination failed: {e}")
            raise

    async def get_destinations(self, user_id: int, platform: str) -> list:
        url = f"{BACKEND_API_URL}/bot/destinations/"
        params = {"user_id": user_id, "platform": platform}
        try:
            resp = await self.client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            return data if isinstance(data, list) else data.get("destinations", [])
        except Exception as e:
            logger.error(f"get_destinations failed: {e}")
            return []

    async def set_default_destination(
        self, user_id: int, platform: str, destination_id: int
    ) -> bool:
        url = f"{BACKEND_API_URL}/bot/set-default-destination/"
        payload = {
            "user_id": user_id,
            "platform": platform,
            "destination_id": destination_id,
        }
        try:
            resp = await self.client.post(url, json=payload)
            resp.raise_for_status()
            logger.info(f"Default destination set to {destination_id} for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"set_default_destination failed: {e}")
            return False

    async def get_user_id_by_chat(self, platform: str, chat_id: int) -> int:
        """دریافت user_id از روی chat_id (برای ثبت مقصد)"""
        url = f"{BACKEND_API_URL}/bot/user-by-chat/"
        params = {"platform": platform, "chat_id": str(chat_id)}
        try:
            resp = await self.client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            return data.get("user_id")
        except Exception as e:
            logger.error(f"get_user_id_by_chat failed: {e}")
            raise

    async def register_phone_chat(self, platform: str, phone: str, chat_id: int) -> dict:
        """همگام‌سازی شماره تلفن و شناسه چت پیام‌رسان در مدل کاربر"""
        url = f"{BACKEND_API_URL}/bot/register-phone-chat/"
        payload = {
            "platform": platform,
            "phone": phone,
            "chat_id": str(chat_id)
        }
        try:
            resp = await self.client.post(url, json=payload)
            resp.raise_for_status()
            logger.info(f"register_phone_chat success for phone={phone}, chat_id={chat_id}")
            return resp.json()
        except Exception as e:
            logger.error(f"register_phone_chat failed for phone={phone}: {e}")
            raise

    async def close(self):
        await self.client.aclose()