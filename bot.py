# create_bot_structure.py
import os

ROOT_DIR = "bot_runner"

structure = {
    "config.py": None,
    "api_client.py": None,
    "logger_config.py": None,
    "telegram_bot.py": None,
    "main.py": None,
    "requirements.txt": None,
    "logs": {},          # پوشه‌ی خالی
}

def create_structure(base_path, items):
    for name, content in items.items():
        path = os.path.join(base_path, name)
        if isinstance(content, dict):
            # پوشه است
            os.makedirs(path, exist_ok=True)
            create_structure(path, content)
        else:
            # فایل خالی
            os.makedirs(os.path.dirname(path), exist_ok=True)
            if not os.path.exists(path):
                with open(path, "w", encoding="utf-8") as f:
                    pass

if __name__ == "__main__":
    if os.path.exists(ROOT_DIR):
        print(f"پوشه‌ی '{ROOT_DIR}' از قبل وجود دارد. فقط موارد جدید اضافه می‌شوند.")
    else:
        os.makedirs(ROOT_DIR)
    create_structure(ROOT_DIR, structure)
    print(f"ساختار '{ROOT_DIR}' با موفقیت ایجاد شد (فایل‌ها خالی).")