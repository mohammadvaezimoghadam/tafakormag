import os
import httpx
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("frontend.api")

class APIClient:
    def __init__(self, token=None):
        # آدرس بک‌اند داخل شبکه داکر یا پیش‌فرض لوکال‌هاست
        self.base_url = os.getenv("BACKEND_API_INTERNAL_URL", "http://backend:8000")
        
        headers = {
            "Content-Type": "application/json",
        }
        if token:
            headers["Authorization"] = f"Token {token}"
            
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=10.0
        )

    async def request_otp(self, phone: str, force_sms: bool = False):
        try:
            resp = await self.client.post("/api/auth/request-otp/", json={
                "phone": phone,
                "force_sms": force_sms
            })
            return resp.status_code, resp.json()
        except Exception as e:
            logger.error(f"request_otp failed: {e}")
            return 500, {"error": "خطا در برقراری ارتباط با سرور بک‌اند"}

    async def verify_otp(self, phone: str, otp: str):
        try:
            resp = await self.client.post("/api/auth/verify-otp/", json={
                "phone": phone,
                "otp": otp
            })
            return resp.status_code, resp.json()
        except Exception as e:
            logger.error(f"verify_otp failed: {e}")
            return 500, {"error": "خطا در تایید کد ورود"}

    async def fetch_profile(self):
        try:
            resp = await self.client.get("/api/auth/profile/")
            return resp.status_code, resp.json()
        except Exception as e:
            logger.error(f"fetch_profile failed: {e}")
            return 500, {"error": "خطا در دریافت پروفایل"}

    async def fetch_notes(self):
        try:
            resp = await self.client.get("/api/notes/")
            return resp.status_code, resp.json()
        except Exception as e:
            logger.error(f"fetch_notes failed: {e}")
            return 500, []

    async def search_notes(self, query: str):
        try:
            resp = await self.client.get("/api/notes/search/", params={"q": query})
            return resp.status_code, resp.json()
        except Exception as e:
            logger.error(f"search_notes failed: {e}")
            return 500, []

    async def create_note(self, data: dict):
        try:
            resp = await self.client.post("/api/notes/", json=data)
            return resp.status_code, resp.json()
        except Exception as e:
            logger.error(f"create_note failed: {e}")
            return 500, {"error": "خطا در ایجاد یادداشت"}

    async def update_note(self, note_id: int, data: dict):
        try:
            resp = await self.client.patch(f"/api/notes/{note_id}/", json=data)
            return resp.status_code, resp.json()
        except Exception as e:
            logger.error(f"update_note failed: {e}")
            return 500, {"error": "خطا در ویرایش یادداشت"}

    async def delete_note(self, note_id: int):
        try:
            resp = await self.client.delete(f"/api/notes/{note_id}/")
            return resp.status_code, None
        except Exception as e:
            logger.error(f"delete_note failed: {e}")
            return 500, {"error": "خطا در حذف یادداشت"}

    async def get_connect_token(self, platform: str):
        try:
            resp = await self.client.get("/api/auth/connect-token/", params={"platform": platform})
            return resp.status_code, resp.json()
        except Exception as e:
            logger.error(f"get_connect_token failed: {e}")
            return 500, {"error": "خطا در دریافت توکن ارتباط"}

    async def update_custom_bot(self, platform: str, token: str):
        try:
            resp = await self.client.post("/api/auth/update-custom-bot/", json={
                "platform": platform,
                "token": token
            })
            return resp.status_code, resp.json()
        except Exception as e:
            logger.error(f"update_custom_bot failed: {e}")
            return 500, {"error": "خطا در اتصال ربات اختصاصی"}

    async def close(self):
        await self.client.aclose()
