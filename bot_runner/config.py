import os

BALE_BOT_TOKEN = os.getenv("BALE_BOT_TOKEN", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_PROXY_URL = os.getenv("TELEGRAM_PROXY_URL", None)
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://backend:8000/api")

BALE_BASE_URL = "https://tapi.bale.ai/bot"
BALE_FILE_URL = "https://tapi.bale.ai/file"

VERIFY_LINK_URL = f"{BACKEND_API_URL}/bot/verify-link/"
FETCH_TASKS_URL = f"{BACKEND_API_URL}/bot/tasks/"

POLL_INTERVAL = 3
