import os

def load_env():
    # Try current directory first, then parent directory (root .env)
    for path in [".env", "../.env"]:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip()
                        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                            v = v[1:-1]
                        if k not in os.environ:
                            os.environ[k] = v
            break

load_env()

BALE_BOT_TOKEN = os.getenv("BALE_BOT_TOKEN", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_PROXY_URL = os.getenv("TELEGRAM_PROXY_URL", None)
TELEGRAM_API_URL = os.getenv("TELEGRAM_API_URL", "https://api.telegram.org/bot")
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://backend:8000/api")

BALE_BASE_URL = "https://tapi.bale.ai/bot"
BALE_FILE_URL = "https://tapi.bale.ai/file"

VERIFY_LINK_URL = f"{BACKEND_API_URL}/bot/verify-link/"
FETCH_TASKS_URL = f"{BACKEND_API_URL}/bot/tasks/"

POLL_INTERVAL = 3
