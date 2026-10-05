import os
import sys
import json
import sqlite3
import hashlib
import socket
import mimetypes
from datetime import datetime
from urllib.parse import urlparse, parse_qs, unquote
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(os.getenv("PORT", 8080))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
PATCH_DIR = os.path.join(BASE_DIR, "patches")
DB_PATH = os.path.join(DATA_DIR, "patches.db")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PATCH_DIR, exist_ok=True)

# Ensure UTF-8 output in Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Maintain rolling logs in memory for the web UI
SERVER_LOGS = []

def add_log(category: str, message: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    entry = {"time": timestamp, "cat": category, "msg": message}
    SERVER_LOGS.append(entry)
    if len(SERVER_LOGS) > 100:
        SERVER_LOGS.pop(0)
    print(f"[{timestamp}] [{category}] {message}", flush=True)


# ==============================================================================
# Database Layer (SQLite)
# ==============================================================================
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS apps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        app_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        package_name TEXT NOT NULL,
        description TEXT,
        created_at TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        app_id TEXT NOT NULL,
        version TEXT NOT NULL,
        target_version_code INTEGER NOT NULL DEFAULT 1,
        is_force INTEGER NOT NULL DEFAULT 0,
        is_active INTEGER NOT NULL DEFAULT 0,
        filename TEXT NOT NULL,
        file_path TEXT NOT NULL,
        size_bytes INTEGER NOT NULL DEFAULT 0,
        md5 TEXT NOT NULL,
        release_notes TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(app_id) REFERENCES apps(app_id)
    );
    """)
    conn.commit()

    # Seed default applications if table is empty
    cursor.execute("SELECT COUNT(*) FROM apps")
    if cursor.fetchone()[0] == 0:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO apps (app_id, name, package_name, description, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            "quran_app",
            "اپلیکیشن جامع قرآن و عترت",
            "ir.tafakormag.quran",
            "نسخه فلاتر کلاینت قرآن با تلاوت، ترجمه و مقالات تدبر",
            now
        ))
        cursor.execute("""
            INSERT INTO apps (app_id, name, package_name, description, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            "tafakor_app",
            "سامانه تفکر مگ",
            "ir.tafakormag.portal",
            "پورتال مجله و سامانه همراه تفکر",
            now
        ))
        conn.commit()
        add_log("DB", "Initialized database with default apps: quran_app, tafakor_app.")

    conn.close()

def db_get_apps():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.*, 
               (SELECT COUNT(*) FROM patches p WHERE p.app_id = a.app_id) as total_patches,
               (SELECT p.version FROM patches p WHERE p.app_id = a.app_id AND p.is_active = 1 LIMIT 1) as active_version,
               (SELECT p.is_force FROM patches p WHERE p.app_id = a.app_id AND p.is_active = 1 LIMIT 1) as active_is_force
        FROM apps a
        ORDER BY a.id ASC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def db_add_app(app_id: str, name: str, package_name: str, description: str):
    conn = get_db()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO apps (app_id, name, package_name, description, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (app_id.strip(), name.strip(), package_name.strip(), description.strip(), now))
    conn.commit()
    conn.close()

def db_get_patches(app_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM patches
        WHERE app_id = ?
        ORDER BY id DESC
    """, (app_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def db_get_active_patch(app_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM patches
        WHERE app_id = ? AND is_active = 1
        LIMIT 1
    """, (app_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def db_activate_patch(app_id: str, patch_id: int):
    conn = get_db()
    cursor = conn.cursor()
    # First deactivate all for this app
    cursor.execute("UPDATE patches SET is_active = 0 WHERE app_id = ?", (app_id,))
    if patch_id > 0:
        cursor.execute("UPDATE patches SET is_active = 1 WHERE id = ? AND app_id = ?", (patch_id, app_id))
    conn.commit()
    conn.close()

def db_toggle_force(patch_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE patches SET is_force = 1 - is_force WHERE id = ?", (patch_id,))
    conn.commit()
    conn.close()

def db_delete_patch(patch_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT file_path FROM patches WHERE id = ?", (patch_id,))
    row = cursor.fetchone()
    if row and row["file_path"] and os.path.exists(row["file_path"]):
        try:
            os.remove(row["file_path"])
        except Exception as e:
            add_log("WARN", f"Could not remove patch file from disk: {e}")
    cursor.execute("DELETE FROM patches WHERE id = ?", (patch_id,))
    conn.commit()
    conn.close()

def db_create_patch(app_id: str, version: str, target_version_code: int, is_force: bool, activate: bool,
                    filename: str, file_path: str, size_bytes: int, md5: str, release_notes: str):
    conn = get_db()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if activate:
        cursor.execute("UPDATE patches SET is_active = 0 WHERE app_id = ?", (app_id,))

    cursor.execute("""
        INSERT INTO patches (app_id, version, target_version_code, is_force, is_active, filename, file_path, size_bytes, md5, release_notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        app_id,
        version,
        target_version_code,
        1 if is_force else 0,
        1 if activate else 0,
        filename,
        file_path,
        size_bytes,
        md5,
        release_notes,
        now
    ))
    patch_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return patch_id

def compute_file_md5(filepath: str) -> str:
    hasher = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def get_detected_ips():
    ips = []
    try:
        hostname = socket.gethostname()
        for ip in socket.gethostbyname_ex(hostname)[2]:
            if not ip.startswith("127.") and not ip.startswith("169.254."):
                ips.append(ip)
    except Exception:
        pass

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        primary = s.getsockname()[0]
        s.close()
        if primary not in ips and not primary.startswith("127."):
            ips.append(primary)
    except Exception:
        pass

    def ip_priority(ip):
        if ip.startswith("192.168.1.") or ip.startswith("192.168.0."):
            return 0
        if ip.startswith("192.168."):
            return 1
        if ip.startswith("10."):
            return 2
        return 3

    ips.sort(key=ip_priority)
    return ips or ["127.0.0.1"]


# ==============================================================================
# Modern Dark Dashboard UI (HTML / CSS / JS)
# ==============================================================================
DASHBOARD_HTML = """<!DOCTYPE html>
<html dir="rtl" lang="fa">
<head>
  <meta charset="utf-8">
  <meta content="width=device-width, initial-scale=1.0" name="viewport">
  <title>فلاتر او‌تی‌ای | سامانه مدیریت انتشار و رول‌بک پچ‌های فلاتر (CodePush / OTA Hub)</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link href="https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
  <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" rel="stylesheet">
  
  <style>
    * { box-sizing: border-box; }
    body {
      font-family: 'Vazirmatn', -apple-system, BlinkMacSystemFont, Segoe UI, Tahoma, sans-serif;
      background-color: #f8fafc;
      color: #0f172a;
      margin: 0;
      padding: 0;
    }
    .font-code { font-family: 'JetBrains Mono', monospace; }
  </style>
  
  <script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
  <script>
    tailwind.config = {
      darkMode: "class",
      theme: {
        extend: {
          colors: {
            primary: "#1e3a5f",
            "primary-container": "#2563eb",
            secondary: "#64748b",
            background: "#f8fafc",
            surface: "#ffffff",
            "surface-dim": "#f1f5f9",
            "surface-border": "#e2e8f0",
            tertiary: "#b91c1c",
            "tertiary-container": "#dc2626"
          },
          fontFamily: {
            sans: ['Vazirmatn', 'sans-serif'],
            mono: ['JetBrains Mono', 'monospace']
          }
        }
      }
    };
  </script>
</head>
<body class="bg-slate-50 text-slate-900 antialiased min-h-screen">

  <!-- Fixed Right Sidebar -->
  <aside id="main-sidebar" class="fixed right-0 top-0 h-full w-64 bg-white z-50 flex flex-col justify-between border-l border-slate-200 shadow-sm transition-transform duration-300 translate-x-full lg:translate-x-0">
    <div class="flex flex-col">
      <!-- Sidebar Brand Header -->
      <div class="h-16 px-5 flex items-center justify-between border-b border-slate-100">
        <div class="flex items-center gap-2.5">
          <div class="w-9 h-9 rounded-xl bg-blue-600 text-white flex items-center justify-center font-black text-base shadow-sm">
            ⚡
          </div>
          <div class="flex flex-col">
            <span class="text-sm font-extrabold text-slate-900 leading-tight">فلاتر او‌تی‌ای</span>
            <span class="text-[10px] text-slate-400 font-mono" dir="ltr">Flutter OTA Hub</span>
          </div>
        </div>
        <div class="h-2.5 w-2.5 rounded-full bg-emerald-500 ring-4 ring-emerald-50"></div>
      </div>

      <!-- App Switcher in Sidebar -->
      <div class="p-4 border-b border-slate-100">
        <span class="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-2">برنامه فعال (Workspace)</span>
        <button onclick="openAppModal()" class="w-full flex items-center justify-between p-2.5 bg-slate-50 hover:bg-slate-100 rounded-xl border border-slate-200/80 text-right transition-all group">
          <div class="flex items-center gap-2.5 truncate">
            <div class="w-8 h-8 rounded-lg bg-blue-600 text-white flex items-center justify-center font-bold text-xs shrink-0" id="sidebar-app-avatar">QD</div>
            <div class="flex flex-col truncate text-right">
              <span class="text-xs font-bold text-slate-900 truncate" id="sidebar-app-name">اپلیکیشن جامع قرآن</span>
              <span class="text-[10px] text-slate-400 font-mono truncate" dir="ltr" id="sidebar-app-pkg">ir.tafakormag.quran</span>
            </div>
          </div>
          <span class="material-symbols-outlined text-slate-400 group-hover:text-blue-600 text-[18px]">unfold_more</span>
        </button>
      </div>

      <!-- Navigation Links -->
      <div class="px-4 py-3">
        <span class="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-2">کنترل پنل مرکزی</span>
        <nav class="flex flex-col gap-1.5" id="sidebar-nav">
          <button onclick="switchView('dashboard')" data-view="dashboard" class="nav-link flex items-center justify-between px-3 py-2.5 rounded-xl bg-blue-600 text-white shadow-sm font-bold text-xs text-right w-full transition-all">
            <span class="flex items-center gap-2.5"><span class="material-symbols-outlined text-[19px]">dashboard</span>داشبورد و وضعیت زنده</span>
            <span class="material-symbols-outlined text-[16px]">chevron_left</span>
          </button>
          <button onclick="switchView('publisher')" data-view="publisher" class="nav-link flex items-center justify-between px-3 py-2.5 rounded-xl text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-all text-xs font-semibold text-right w-full">
            <span class="flex items-center gap-2.5"><span class="material-symbols-outlined text-[19px]">cloud_upload</span>انتشار پچ جدید</span>
            <span class="material-symbols-outlined text-[16px]">chevron_left</span>
          </button>
          <button onclick="switchView('rollback')" data-view="rollback" class="nav-link flex items-center justify-between px-3 py-2.5 rounded-xl text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-all text-xs font-semibold text-right w-full">
            <span class="flex items-center gap-2.5"><span class="material-symbols-outlined text-[19px]">history</span>تاریخچه و رول‌بک</span>
            <span class="material-symbols-outlined text-[16px]">chevron_left</span>
          </button>
          <button onclick="switchView('logs')" data-view="logs" class="nav-link flex items-center justify-between px-3 py-2.5 rounded-xl text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-all text-xs font-semibold text-right w-full">
            <span class="flex items-center gap-2.5"><span class="material-symbols-outlined text-[19px]">terminal</span>لاگ‌های زنده کلاینت</span>
            <span class="material-symbols-outlined text-[16px]">chevron_left</span>
          </button>
          <button onclick="switchView('apps')" data-view="apps" class="nav-link flex items-center justify-between px-3 py-2.5 rounded-xl text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-all text-xs font-semibold text-right w-full">
            <span class="flex items-center gap-2.5"><span class="material-symbols-outlined text-[19px]">apps</span>مدیریت برنامه‌ها</span>
            <span class="material-symbols-outlined text-[16px]">chevron_left</span>
          </button>
          <button onclick="openNewAppModal()" class="flex items-center justify-between px-3 py-2 rounded-xl text-blue-600 hover:bg-blue-50 transition-all text-xs font-bold text-right w-full mt-2 border border-dashed border-blue-200">
            <span class="flex items-center gap-2"><span class="material-symbols-outlined text-[18px]">add_box</span>+ ثبت برنامه جدید</span>
            <span class="material-symbols-outlined text-[16px]">chevron_left</span>
          </button>
        </nav>
      </div>
    </div>

    <!-- Sidebar Bottom Status -->
    <div class="px-5 py-3 text-[11px] text-slate-400 border-t border-slate-100 flex items-center justify-between font-mono" dir="ltr">
      <span>Flutter OTA</span>
      <span class="text-emerald-600 font-bold">● Active</span>
    </div>
  </aside>

  <!-- Content Canvas Area (pr-0 on mobile, pr-64 on desktop) -->
  <div class="pr-0 lg:pr-64 min-h-screen flex flex-col transition-all">

    <!-- Top Global Header -->
    <header class="sticky top-0 h-14 bg-white/95 backdrop-blur-md border-b border-slate-200 z-40 flex items-center justify-between px-6 shadow-xs">
      <div class="flex items-center gap-3">
        <button onclick="toggleSidebar()" class="lg:hidden p-1.5 text-slate-600 hover:text-slate-900 rounded-lg border border-slate-200 flex items-center justify-center">
          <span class="material-symbols-outlined text-[20px]">menu</span>
        </button>
        
        <h1 id="current-page-badge" class="text-sm font-extrabold text-slate-800 flex items-center gap-2">
          <span class="material-symbols-outlined text-blue-600 text-[19px]">dashboard</span>
          <span>داشبورد مدیریت پچ‌ها</span>
        </h1>
      </div>

      <div class="flex items-center gap-3">
        <!-- Active App Indicator & Switcher Button -->
        <button onclick="openAppModal()" class="flex items-center gap-2 px-3 py-1.5 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-xl text-xs font-bold text-slate-700 transition-colors">
          <span class="w-2 h-2 rounded-full bg-blue-600"></span>
          <span id="header-app-name">اپلیکیشن جامع قرآن</span>
          <span class="material-symbols-outlined text-slate-400 text-[16px]">expand_more</span>
        </button>

        <span class="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>آنلاین</span>
        </span>
      </div>
    </header>

    <!-- Main Body Content -->
    <main class="flex-1 w-full max-w-6xl mx-auto px-4 sm:px-6 py-6 space-y-6">

    <!-- ==================== VIEW 1: DASHBOARD ==================== -->
    <div id="view-dashboard" class="view-tab space-y-6">
      
      <!-- 3 Key Metric Cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
        
        <!-- Card 1: Active Patch & Emergency Rollback -->
        <div class="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between pb-3 mb-3 border-b border-slate-100">
              <span class="text-xs font-bold text-slate-500 uppercase">نسخه فعال جاری</span>
              <span id="live-status-chip" class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                <span>فعال در کلاینت‌ها</span>
              </span>
            </div>
            <div class="text-3xl font-black font-mono text-slate-900 my-2" dir="ltr" id="current-patch-version">-</div>
            <div class="text-xs text-slate-500 leading-relaxed truncate" id="meta-notes-text">در حال بارگذاری اطلاعات پچ...</div>
          </div>
          <div class="pt-4 mt-3 border-t border-slate-100 flex items-center justify-between">
            <span class="text-[11px] text-slate-400 font-mono" id="meta-date">-</span>
            <button onclick="triggerKillSwitch()" class="text-xs text-red-600 hover:text-white hover:bg-red-600 px-3 py-1.5 rounded-lg border border-red-200 transition-all font-bold flex items-center gap-1">
              <span class="material-symbols-outlined text-[16px]">power_settings_new</span>
              <span>رول‌بک اضطراری به استور</span>
            </button>
          </div>
        </div>

        <!-- Card 2: Update Policy -->
        <div class="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between pb-3 mb-3 border-b border-slate-100">
              <span class="text-xs font-bold text-slate-500 uppercase">سیاست دریافت آپدیت</span>
              <span class="material-symbols-outlined text-slate-400 text-[20px]">policy</span>
            </div>
            <div class="text-2xl font-black text-slate-900 my-2" id="policy-chip">اختیاری (Optional)</div>
            <p class="text-xs text-slate-500">نحوه برخورد اپلیکیشن کلاینت هنگام یافتن نسخه جدید</p>
          </div>
          <div class="pt-4 mt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-600">
            <span>کد بیلد تارگت:</span>
            <span class="font-mono font-bold text-slate-900 bg-slate-100 px-2 py-0.5 rounded border border-slate-200" id="meta-target-code">1</span>
          </div>
        </div>

        <!-- Card 3: App Stats & Connectivity -->
        <div class="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between pb-3 mb-3 border-b border-slate-100">
              <span class="text-xs font-bold text-slate-500 uppercase">کل پچ‌های ذخیره‌شده</span>
              <span class="material-symbols-outlined text-slate-400 text-[20px]">layers</span>
            </div>
            <div class="text-3xl font-black text-blue-600 my-2 flex items-baseline gap-2">
              <span id="stat-patch-count">۰</span>
              <span class="text-xs font-bold text-slate-500">نسخه در دیتابیس</span>
            </div>
            <p class="text-xs text-slate-500">پایگاه داده سبک و پایدار SQLite در سرور محلی</p>
          </div>
          <div class="pt-4 mt-3 border-t border-slate-100 flex items-center justify-between">
            <span class="text-xs text-slate-500">تست اندپوینت:</span>
            <a href="#" id="stat-test-link" target="_blank" class="text-xs text-blue-600 hover:underline font-mono font-bold">/check API ↗</a>
          </div>
        </div>

      </div>

      <!-- Recent Patches Table Card -->
      <div class="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs">
        <div class="flex items-center justify-between pb-4 mb-3 border-b border-slate-100 flex-wrap gap-2">
          <div>
            <h2 class="text-sm font-extrabold text-slate-900">آخرین پچ‌های ثبت‌شده</h2>
            <p class="text-xs text-slate-500">نسخه‌های اخیر ایجاد شده برای این برنامه</p>
          </div>
          <div class="flex items-center gap-2">
            <button onclick="switchView('publisher')" class="h-8 px-3.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold transition-all shadow-xs flex items-center gap-1.5">
              <span class="material-symbols-outlined text-[16px]">add</span>
              <span>+ انتشار پچ جدید</span>
            </button>
            <button onclick="switchView('rollback')" class="h-8 px-3 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-bold transition-all border border-slate-200 flex items-center gap-1">
              <span>مدیریت تاریخچه</span>
              <span class="material-symbols-outlined text-[15px]">arrow_back</span>
            </button>
          </div>
        </div>
        <div class="w-full overflow-x-auto">
          <table class="w-full text-right border-collapse text-xs">
            <thead>
              <tr class="bg-slate-50 text-slate-600 border-b border-slate-100">
                <th class="py-2.5 px-3 font-bold">نسخه</th>
                <th class="py-2.5 px-3 font-bold text-center">وضعیت</th>
                <th class="py-2.5 px-3 font-bold text-center">سیاست</th>
                <th class="py-2.5 px-3 font-bold text-center">بیلد تارگت</th>
                <th class="py-2.5 px-3 font-bold">تاریخ انتشار</th>
                <th class="py-2.5 px-3 font-bold">توضیحات</th>
              </tr>
            </thead>
            <tbody id="dashboard-recent-table" class="divide-y divide-slate-100">
              <tr>
                <td colspan="6" class="text-center py-6 text-slate-400">در حال بارگذاری...</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </div>

    <!-- ==================== VIEW 2: PATCH PUBLISHER ==================== -->
    <div id="view-publisher" class="view-tab hidden space-y-6">
      <div class="max-w-3xl mx-auto bg-white border border-slate-200 rounded-2xl p-6 shadow-xs">
        
        <div class="pb-4 mb-5 border-b border-slate-100">
          <h2 class="text-base text-slate-900 font-extrabold">انتشار پچ جدید فلاتر (Deploy Patch)</h2>
          <p class="text-xs text-slate-500 mt-1">فایل زیپ یا باینری تغییرات کدهای فلاتر را انتخاب کرده و نسخه موردنظر را مشخص کنید.</p>
        </div>

        <!-- Compact File Selector Drop Zone -->
        <div class="bg-slate-50 hover:bg-slate-100/80 transition-all border-2 border-dashed border-slate-300 rounded-xl p-6 flex flex-col items-center justify-center text-center cursor-pointer mb-5" id="drop-zone" onclick="document.getElementById('real-file-input').click()">
          <input type="file" id="real-file-input" class="hidden" accept=".zip,.bundle" onchange="handleFileChange(this.files)">
          <div class="w-10 h-10 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mb-2">
            <span class="material-symbols-outlined text-[22px]">cloud_upload</span>
          </div>
          <span class="text-xs text-slate-800 font-bold">برای انتخاب فایل پچ (.zip یا .bundle) کلیک کنید یا فایل را به اینجا بکشید</span>
          <span class="text-[11px] text-slate-400 mt-1">حداکثر حجم مجاز: ۵۰ مگابایت</span>
          <div class="mt-3 flex items-center gap-2" id="selected-file-badge" style="display: none;">
            <span class="font-mono text-xs bg-blue-50 border border-blue-200 text-blue-700 px-3 py-1 rounded-md font-bold" dir="ltr" id="selected-file-name">file.zip</span>
            <span class="text-xs text-slate-500 font-semibold" id="selected-file-size">۰ MB</span>
          </div>
        </div>

        <!-- Clean Form Inputs -->
        <div class="space-y-4">
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-bold text-slate-700 mb-1">شماره نسخه پچ (SemVer) *</label>
              <input type="text" id="input-patch-version" placeholder="مثال: 1.0.1" dir="ltr" class="w-full h-10 px-3 bg-white text-slate-900 font-mono text-xs rounded-lg border border-slate-200 focus:outline-none focus:border-blue-500 font-bold">
            </div>
            <div>
              <label class="block text-xs font-bold text-slate-700 mb-1">کد بیلد مقصد نیتیو (Target Build) *</label>
              <input type="number" id="input-target-build" value="1" dir="ltr" class="w-full h-10 px-3 bg-white text-slate-900 font-mono text-xs rounded-lg border border-slate-200 focus:outline-none focus:border-blue-500 font-bold">
            </div>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-bold text-slate-700 mb-1">نوع دریافت پچ (Policy)</label>
              <select id="select-policy" class="w-full h-10 px-3 bg-white text-slate-900 text-xs rounded-lg border border-slate-200 focus:outline-none focus:border-blue-500 font-semibold">
                <option value="optional" selected>آپدیت اختیاری (اعمال در شروع بعدی اپلیکیشن)</option>
                <option value="force">آپدیت اجباری (Force Update - الزام به دریافت)</option>
              </select>
            </div>
            <div class="flex items-center pt-5">
              <label class="flex items-center gap-2 cursor-pointer select-none text-xs text-slate-700 font-bold">
                <input type="checkbox" id="auto-deploy" checked class="w-4 h-4 rounded text-blue-600 focus:ring-0 cursor-pointer">
                <span>فعال‌سازی و انتشار فوری پس از آپلود</span>
              </label>
            </div>
          </div>

          <div>
            <label class="block text-xs font-bold text-slate-700 mb-1">یادداشت فنی تغییرات (اختیاری)</label>
            <textarea id="textarea-notes" rows="2" placeholder="توضیحاتی درباره رفع ایرادها یا قابلیت‌های جدید..." class="w-full px-3 py-2 bg-slate-50 text-slate-900 text-xs rounded-lg border border-slate-200 focus:outline-none focus:border-blue-500 focus:bg-white transition-all leading-relaxed"></textarea>
          </div>
        </div>

        <div class="pt-5 mt-5 border-t border-slate-100 flex items-center justify-end">
          <button type="button" id="btn-deploy-patch" onclick="uploadPatch()" class="h-10 px-6 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition-all shadow-xs flex items-center gap-2">
            <span class="material-symbols-outlined text-[18px]">publish</span>
            <span>بارگذاری و انتشار پچ</span>
          </button>
        </div>

      </div>
    </div>

    <!-- ==================== VIEW 3: VERSION ROLLBACK MATRIX ==================== -->
    <div id="view-rollback" class="view-tab hidden space-y-6">
      <div class="w-full bg-white border border-slate-200 rounded-2xl p-6 shadow-xs flex flex-col">
        <div class="flex items-center justify-between pb-4 mb-4 border-b border-slate-100 flex-wrap gap-3">
          <div>
            <h2 class="text-base text-slate-900 font-extrabold flex items-center gap-2">
              <span class="material-symbols-outlined text-blue-600 text-[22px]">history</span>
              <span>تاریخچه پچ‌ها و رول‌بک</span>
            </h2>
            <p class="text-xs text-slate-500 mt-0.5">مشاهده تمام پچ‌های منتشرشده با قابلیت فعال‌سازی آنی (Rollback) یا حذف.</p>
          </div>
          <div class="flex items-center gap-2 flex-wrap">
            <div class="relative">
              <input type="text" id="search-patches" oninput="filterPatchesTable()" placeholder="جستجوی پچ یا یادداشت..." class="h-8 pr-8 pl-3 bg-slate-50 text-slate-900 text-xs rounded-lg border border-slate-200 focus:outline-none focus:border-blue-500 font-sans w-48">
              <span class="material-symbols-outlined absolute right-2 top-2 text-slate-400 text-[16px]">search</span>
            </div>
            <button class="h-8 px-3 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold border border-slate-200 flex items-center gap-1" onclick="loadPatches()">
              <span class="material-symbols-outlined text-[15px]">refresh</span>
              <span>به‌روزرسانی</span>
            </button>
            <span class="text-xs bg-slate-100 text-slate-700 border border-slate-200 px-3 py-1 rounded-full font-medium" id="table-patch-count">۰ نسخه ثبت‌شده</span>
            <button onclick="triggerKillSwitch()" class="h-8 px-3 bg-red-600 hover:bg-red-700 text-white rounded-lg text-xs font-bold transition-all shadow-xs flex items-center gap-1">
              <span class="material-symbols-outlined text-[16px]">power_settings_new</span>
              <span>رول‌بک سراسری (Panic)</span>
            </button>
          </div>
        </div>

        <!-- Clean 5-Column Table Container -->
        <div class="w-full overflow-x-auto">
          <table class="w-full text-right border-collapse text-xs">
            <thead>
              <tr class="bg-slate-50 text-slate-700 font-bold border-b border-slate-200">
                <th class="py-3 px-4 rounded-r-lg">نسخه و وضعیت</th>
                <th class="py-3 px-3 text-center">مشخصات بیلد</th>
                <th class="py-3 px-3 text-center">نوع آپدیت</th>
                <th class="py-3 px-4">تاریخ و یادداشت</th>
                <th class="py-3 px-4 text-left rounded-l-lg" dir="ltr">عملیات</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100" id="patches-table-body">
              <tr>
                <td colspan="5" class="text-center py-8 text-slate-400">در حال دریافت لیست نسخه‌ها از پایگاه داده...</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- ==================== VIEW 4: LIVE TELEMETRY FEED ==================== -->
    <div id="view-logs" class="view-tab hidden space-y-6">
      <div class="w-full bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm text-left font-mono" dir="ltr">
        <div class="flex items-center justify-between pb-4 mb-4 border-b border-slate-800 text-right flex-wrap gap-3" dir="rtl">
          <div class="flex items-center gap-2">
            <span class="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
            <span class="text-sm text-slate-100 font-extrabold">کنسول زنده ارتباط با کلاینت‌ها (Live Telemetry Stream)</span>
          </div>
          <div class="flex items-center gap-2 flex-wrap">
            <div class="flex items-center bg-slate-800 p-0.5 rounded-lg border border-slate-700">
              <button onclick="setLogFilter('ALL')" data-filter="ALL" class="log-filter-btn h-7 px-2.5 bg-blue-600 text-white rounded text-xs font-bold transition-all">همه</button>
              <button onclick="setLogFilter('CHECK')" data-filter="CHECK" class="log-filter-btn h-7 px-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs transition-all border-none">استعلام (CHECK)</button>
              <button onclick="setLogFilter('DOWNLOAD')" data-filter="DOWNLOAD" class="log-filter-btn h-7 px-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs transition-all border-none">دانلود</button>
              <button onclick="setLogFilter('UPLOAD')" data-filter="UPLOAD" class="log-filter-btn h-7 px-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs transition-all border-none">آپلود</button>
              <button onclick="setLogFilter('ROLLBACK')" data-filter="ROLLBACK" class="log-filter-btn h-7 px-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs transition-all border-none">رول‌بک</button>
              <button onclick="setLogFilter('ERROR')" data-filter="ERROR" class="log-filter-btn h-7 px-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs transition-all border-none">خطاها</button>
            </div>
            <button onclick="clearLogsConsole()" class="h-7 px-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs border border-slate-700 flex items-center gap-1">
              <span class="material-symbols-outlined text-[15px]">delete_sweep</span>
              <span>پاک‌سازی</span>
            </button>
            <button onclick="pollLogs()" class="h-7 px-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs border border-slate-700 flex items-center gap-1">
              <span class="material-symbols-outlined text-[15px]">refresh</span>
              <span>بروزرسانی</span>
            </button>
          </div>
        </div>
        <div id="live-logs-container" class="max-h-[520px] overflow-y-auto space-y-2 text-xs text-slate-300 pr-1">
          <div class="text-slate-500 italic">در حال اتصال به جریان لاگ‌های سرور...</div>
        </div>
      </div>
    </div>

    <!-- ==================== VIEW 5: APPS MANAGEMENT ==================== -->
    <div id="view-apps" class="view-tab hidden space-y-6">
      <div class="w-full bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
        <div class="flex items-center justify-between pb-4 mb-5 border-b border-slate-100 flex-wrap gap-3">
          <div>
            <h2 class="text-base text-slate-900 font-extrabold flex items-center gap-2">
              <span class="material-symbols-outlined text-blue-600 text-[22px]">apps</span>
              <span>مدیریت اپلیکیشن‌های تحت پوشش (Applications Matrix)</span>
            </h2>
            <p class="text-xs text-slate-500 mt-0.5">مشاهده و سوییچ بین برنامه‌های فلاتر یا ثبت پروژه جدید جهت توزیع پچ‌های مستقل.</p>
          </div>
          <button onclick="openNewAppModal()" class="h-9 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition-all shadow-sm flex items-center gap-1.5">
            <span class="material-symbols-outlined text-[18px]">add_circle</span>
            <span>+ ثبت برنامه جدید</span>
          </button>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5" id="apps-cards-grid">
          <!-- Rendered dynamically -->
        </div>
      </div>
    </div>

  </main>
  </div>

  <!-- Modals & Toasts Container -->
  <div class="fixed bottom-6 left-6 z-50 flex flex-col gap-2 pointer-events-none" id="toast-container"></div>

  <!-- Modal: App Switcher -->
  <div class="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center hidden" id="app-switcher-modal">
    <div class="bg-white rounded-2xl border border-slate-200 p-6 w-full max-w-md shadow-2xl text-right">
      <div class="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
        <span class="text-base text-slate-900 font-extrabold">انتخاب برنامه فعال (Workspace)</span>
        <button class="text-slate-400 hover:text-slate-700" onclick="closeAppModal()" type="button">
          <span class="material-symbols-outlined text-[20px]">close</span>
        </button>
      </div>
      <div class="flex flex-col gap-2.5 mb-4 max-h-80 overflow-y-auto" id="modal-apps-list">
        <!-- Rendered dynamically -->
      </div>
    </div>
  </div>

  <!-- Modal: New App -->
  <div class="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center hidden" id="new-app-modal">
    <div class="bg-white rounded-2xl border border-slate-200 p-6 w-full max-w-md shadow-2xl text-right">
      <div class="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
        <span class="text-base text-slate-900 font-extrabold">ثبت و اتصال برنامه فلاتر جدید</span>
        <button class="text-slate-400 hover:text-slate-700" onclick="closeNewAppModal()" type="button">
          <span class="material-symbols-outlined text-[20px]">close</span>
        </button>
      </div>
      <form class="flex flex-col gap-3.5" onsubmit="submitNewApp(event)">
        <div class="flex flex-col gap-1">
          <label class="text-xs text-slate-800 font-bold">شناسه برنامه (App ID)</label>
          <input class="w-full px-3 py-2 bg-slate-50 text-slate-900 text-xs font-mono rounded-lg border border-slate-200 focus:outline-none focus:border-blue-500" dir="ltr" id="input-new-app-id" placeholder="مثال: quran_app یا tafakor_app" required type="text">
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-xs text-slate-800 font-bold">نام نمایشی برنامه</label>
          <input class="w-full px-3 py-2 bg-slate-50 text-slate-900 text-xs rounded-lg border border-slate-200 focus:outline-none focus:border-blue-500" id="input-new-app-name" placeholder="مثال: اپلیکیشن قرآن و عترت" required type="text">
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-xs text-slate-800 font-bold">Package Name / Bundle ID</label>
          <input class="w-full px-3 py-2 bg-slate-50 text-slate-900 text-xs font-mono rounded-lg border border-slate-200 focus:outline-none focus:border-blue-500" dir="ltr" id="input-new-app-pkg" placeholder="ir.tafakormag.quran" required type="text">
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-xs text-slate-800 font-bold">توضیحات کوتاه</label>
          <input class="w-full px-3 py-2 bg-slate-50 text-slate-900 text-xs rounded-lg border border-slate-200 focus:outline-none focus:border-blue-500" id="input-new-app-desc" placeholder="توضیحات اختیاری" type="text">
        </div>
        <div class="flex justify-end gap-2 mt-2">
          <button class="px-4 py-2 bg-slate-100 text-slate-600 hover:bg-slate-200 rounded-lg text-xs font-semibold" onclick="closeNewAppModal()" type="button">انصراف</button>
          <button class="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold shadow-sm" type="submit">ثبت و اتصال</button>
        </div>
      </form>
    </div>
  </div>

  <!-- Core JavaScript: Real Backend Wiring & Telemetry -->
  <script>
    const BASE_PATH = window.location.pathname.startsWith('/patcher') ? '/patcher' : '';

    let currentAppId = 'quran_app';
    let appsList = [];
    let selectedFile = null;
    let allPatchesData = [];
    let logsCache = [];
    let activeLogFilter = 'ALL';

    const VIEWS = {
      dashboard: { title: 'داشبورد و وضعیت زنده', icon: 'dashboard', pageTitle: 'داشبورد و وضعیت زنده' },
      publisher: { title: 'انتشار پچ جدید فلاتر', icon: 'cloud_upload', pageTitle: 'انتشار پچ جدید' },
      rollback: { title: 'تاریخچه نسخه‌ها و رول‌بک', icon: 'history', pageTitle: 'تاریخچه و رول‌بک' },
      logs: { title: 'کنسول لاگ‌های زنده کلاینت', icon: 'terminal', pageTitle: 'لاگ‌های زنده' },
      apps: { title: 'مدیریت اپلیکیشن‌ها', icon: 'apps', pageTitle: 'مدیریت اپلیکیشن‌ها' }
    };

    // Navigation View Switcher (Dedicated Page Presentation)
    function switchView(viewName, updateHistory = true) {
      if (!VIEWS[viewName]) viewName = 'dashboard';

      // 1. Hide all view containers
      document.querySelectorAll('.view-tab').forEach(el => {
        el.classList.add('hidden');
      });

      // 2. Show the targeted view
      const target = document.getElementById('view-' + viewName);
      if (target) {
        target.classList.remove('hidden');
      }

      // 3. Highlight the active link in the sidebar
      document.querySelectorAll('#sidebar-nav .nav-link').forEach(btn => {
        const v = btn.getAttribute('data-view');
        if (v === viewName) {
          btn.className = 'nav-link flex items-center justify-between px-3 py-2.5 rounded-xl bg-blue-600 text-white shadow-sm font-bold text-xs text-right w-full transition-all';
        } else {
          btn.className = 'nav-link flex items-center justify-between px-3 py-2.5 rounded-xl text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-all text-xs font-semibold text-right w-full';
        }
      });

      // 4. Update Header Badge & Document Title
      const pageBadge = document.getElementById('current-page-badge');
      if (pageBadge) {
        pageBadge.innerHTML = `<span class="material-symbols-outlined text-[17px]">${VIEWS[viewName].icon}</span><span>${VIEWS[viewName].title}</span>`;
      }
      document.title = `فلاتر او‌تی‌ای | ${VIEWS[viewName].pageTitle}`;

      // 5. Update URL Hash / History
      if (updateHistory) {
        try {
          history.replaceState(null, '', '#' + viewName);
        } catch (e) {
          window.location.hash = viewName;
        }
      }

      // 6. Close mobile drawer if opened
      const sb = document.getElementById('main-sidebar');
      if (sb && !sb.classList.contains('translate-x-full')) {
        sb.classList.add('translate-x-full');
      }

      // 7. Smoothly scroll to top
      window.scrollTo({ top: 0, behavior: 'smooth' });

      // 8. Refresh view-specific contents
      if (viewName === 'rollback') {
        loadPatches();
      } else if (viewName === 'logs') {
        pollLogs();
      } else if (viewName === 'apps') {
        renderAppsCards();
      }
    }

    function resolveInitialView() {
      const hash = window.location.hash.replace('#', '').trim();
      if (hash && VIEWS[hash]) return hash;

      const pathSegments = window.location.pathname.split('/').filter(Boolean);
      const last = pathSegments.length > 0 ? pathSegments[pathSegments.length - 1] : '';
      if (last && VIEWS[last]) return last;

      return 'dashboard';
    }

    // Toast Notification System
    function showToast(msg, type = 'info') {
      const container = document.getElementById('toast-container');
      if (!container) return;
      const t = document.createElement('div');
      const bg = type === 'success' 
        ? 'bg-slate-900 text-emerald-400 border-emerald-500/50' 
        : type === 'error' 
        ? 'bg-red-700 text-white border-red-800' 
        : 'bg-slate-900 text-white border-slate-700';
      const icon = type === 'success' ? 'check_circle' : type === 'error' ? 'error' : 'info';
      t.className = `pointer-events-auto px-4 py-2.5 rounded-xl shadow-lg border text-xs flex items-center gap-2 transition-all duration-300 ${bg}`;
      t.innerHTML = `<span class="material-symbols-outlined text-[18px]">${icon}</span><span>${msg}</span>`;
      container.appendChild(t);
      setTimeout(() => {
        t.style.opacity = '0';
        setTimeout(() => t.remove(), 300);
      }, 3500);
    }

    // Lifecycle Init
    window.addEventListener('DOMContentLoaded', () => {
      loadStatus();
      loadApps();
      pollLogs();
      setInterval(pollLogs, 3000);
      setupDragDrop();

      const initView = resolveInitialView();
      switchView(initView, false);

      window.addEventListener('hashchange', () => {
        const h = window.location.hash.replace('#', '').trim();
        if (h && VIEWS[h]) {
          switchView(h, false);
        }
      });
    });

    function setupDragDrop() {
      const dz = document.getElementById('drop-zone');
      if (!dz) return;
      dz.addEventListener('dragover', (e) => {
        e.preventDefault();
        dz.classList.add('bg-blue-50/70', 'border-blue-400');
      });
      dz.addEventListener('dragleave', () => {
        dz.classList.remove('bg-blue-50/70', 'border-blue-400');
      });
      dz.addEventListener('drop', (e) => {
        e.preventDefault();
        dz.classList.remove('bg-blue-50/70', 'border-blue-400');
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
          handleFileChange(e.dataTransfer.files);
        }
      });
    }

    function handleFileChange(files) {
      if (!files || files.length === 0) return;
      selectedFile = files[0];
      const badge = document.getElementById('selected-file-badge');
      const nameEl = document.getElementById('selected-file-name');
      const sizeEl = document.getElementById('selected-file-size');
      nameEl.textContent = selectedFile.name;
      sizeEl.textContent = `سایز: ${(selectedFile.size / (1024 * 1024)).toFixed(2)} مگابایت`;
      badge.style.display = 'flex';
      showToast(`فایل ${selectedFile.name} با موفقیت انتخاب شد.`, 'success');
    }

    async function loadStatus() {
      try {
        const res = await fetch(`${BASE_PATH}/api/status`);
        const data = await res.json();
        document.getElementById('stat-port').textContent = data.port;
        const hostIp = (data.ips && data.ips.length > 0) ? data.ips[0] : '127.0.0.1';
        document.getElementById('serverHostInfo').textContent = `Host: ${hostIp}`;
        document.getElementById('serverStatusInfo').textContent = `Port: ${data.port} | Status: Live`;
      } catch (e) {
        console.error('Failed to load status', e);
      }
    }

    async function loadApps() {
      try {
        const res = await fetch(`${BASE_PATH}/api/apps`);
        appsList = await res.json();
        
        // Ensure currentAppId exists
        if (!appsList.find(a => a.app_id === currentAppId) && appsList.length > 0) {
          currentAppId = appsList[0].app_id;
        }

        renderCurrentAppBanner();
        loadPatches();
        renderAppsCards();
      } catch (e) {
        showToast('خطا در دریافت لیست برنامه‌ها: ' + e, 'error');
      }
    }

    function renderCurrentAppBanner() {
      const app = appsList.find(a => a.app_id === currentAppId) || appsList[0];
      if (!app) return;

      document.getElementById('header-app-name').textContent = app.name;
      document.getElementById('header-app-pkg').textContent = app.package_name;
      document.getElementById('header-app-id').textContent = app.app_id;
      document.getElementById('active-app-avatar').textContent = app.name.substring(0, 2);
      document.getElementById('header-total-patches').textContent = `${app.total_patches || 0} پچ`;
      document.getElementById('stat-patch-count').textContent = app.total_patches || 0;

      // Update Sidebar App Info
      const sAvatar = document.getElementById('sidebar-app-avatar');
      if (sAvatar) sAvatar.textContent = app.name.substring(0, 2);
      const sName = document.getElementById('sidebar-app-name');
      if (sName) sName.textContent = app.name;
      const sPkg = document.getElementById('sidebar-app-pkg');
      if (sPkg) sPkg.textContent = app.package_name;

      // Update test link
      const testLink = document.getElementById('stat-test-link');
      testLink.href = `${BASE_PATH}/check?app_id=${app.app_id}`;
      testLink.textContent = `/check?app_id=${app.app_id}`;
    }

    function toggleSidebar() {
      const sb = document.getElementById('main-sidebar');
      if (!sb) return;
      sb.classList.toggle('translate-x-full');
    }

    function filterPatchesTable() {
      const q = (document.getElementById('search-patches')?.value || '').trim().toLowerCase();
      const filtered = allPatchesData.filter(p => {
        if (!q) return true;
        return (p.version && p.version.toLowerCase().includes(q)) ||
               (p.release_notes && p.release_notes.toLowerCase().includes(q)) ||
               (p.md5 && p.md5.toLowerCase().includes(q)) ||
               String(p.target_version_code).includes(q);
      });
      renderPatchesTable(filtered);
    }

    function renderDashboardRecentTable(patches) {
      const tbody = document.getElementById('dashboard-recent-table');
      if (!tbody) return;
      if (!patches || patches.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center py-6 text-slate-400">هنوز هیچ پچی برای این برنامه ثبت نشده است.</td></tr>';
        return;
      }
      const recents = patches.slice(0, 5);
      tbody.innerHTML = recents.map(p => {
        const isActive = p.is_active === 1;
        const statusBadge = isActive 
          ? `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">فعال (Live)</span>`
          : `<span class="px-2 py-0.5 rounded text-[10px] text-slate-500 bg-slate-100">آرشیو</span>`;
        const policyBadge = p.is_force === 1
          ? `<span class="text-red-600 font-bold">اجباری</span>`
          : `<span class="text-slate-500">اختیاری</span>`;
        const sizeKb = (p.size_bytes / 1024).toFixed(1);

        return `
          <tr class="hover:bg-slate-50/70 transition-colors">
            <td class="py-2.5 px-3 font-mono font-bold text-blue-600" dir="ltr">v${p.version}</td>
            <td class="py-2.5 px-3 text-center">${statusBadge}</td>
            <td class="py-2.5 px-3 text-center">${policyBadge}</td>
            <td class="py-2.5 px-3 text-center font-mono">${p.target_version_code} (${sizeKb} KB)</td>
            <td class="py-2.5 px-3 text-slate-500 whitespace-nowrap">${p.created_at}</td>
            <td class="py-2.5 px-3 text-slate-600 truncate max-w-xs">${p.release_notes || '-'}</td>
          </tr>
        `;
      }).join('');
    }

    function renderPatchesTable(patches) {
      const tbody = document.getElementById('patches-table-body');
      if (!tbody) return;

      if (!patches || patches.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center py-8 text-slate-400">هیچ پچی یافت نشد. از تب «انتشار پچ جدید» اولین پچ را بارگذاری کنید.</td></tr>';
        return;
      }

      tbody.innerHTML = patches.map(p => {
        const isActive = p.is_active === 1;
        const isForce = p.is_force === 1;
        const sizeKb = (p.size_bytes / 1024).toFixed(1);
        const rowClass = isActive ? "bg-blue-50/40 font-semibold" : "hover:bg-slate-50";

        const statusBadge = isActive 
          ? `<span class="px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200 inline-flex items-center gap-1"><span class="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse"></span>فعال</span>`
          : `<span class="px-2 py-0.5 rounded text-[11px] text-slate-500 bg-slate-100">آرشیو</span>`;

        const policyBadge = isForce 
          ? `<span class="px-2 py-0.5 rounded text-[11px] font-bold bg-red-100 text-red-700">اجباری</span>`
          : `<span class="px-2 py-0.5 rounded text-[11px] text-slate-600 bg-slate-100">اختیاری</span>`;

        return `
          <tr class="${rowClass} transition-colors">
            <td class="py-3 px-4">
              <div class="flex items-center gap-2">
                <span class="font-mono font-bold text-sm text-blue-600" dir="ltr">v${p.version}</span>
                ${statusBadge}
              </div>
            </td>
            <td class="py-3 px-3 text-center">
              <span class="font-mono text-slate-800">بیلد ${p.target_version_code}</span>
              <span class="text-slate-400 text-[11px] block font-mono" dir="ltr">${sizeKb} KB</span>
            </td>
            <td class="py-3 px-3 text-center">${policyBadge}</td>
            <td class="py-3 px-4">
              <span class="text-slate-400 text-[11px] block">${p.created_at}</span>
              <span class="text-slate-700 truncate max-w-sm block" title="${p.release_notes || ''}">${p.release_notes || '-'}</span>
            </td>
            <td class="py-3 px-4 text-left whitespace-nowrap" dir="ltr">
              <div class="flex items-center gap-1.5 justify-end">
                ${!isActive ? `
                  <button class="h-7 px-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold shadow-xs transition-colors" onclick="activatePatch(${p.id})">
                    رول‌بک (Rollback)
                  </button>
                ` : ''}
                <button class="h-7 px-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 rounded-lg text-xs transition-colors" onclick="toggleForce(${p.id})">
                  ${isForce ? 'اختیاری' : 'اجباری'}
                </button>
                <button class="h-7 px-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors" onclick="deletePatch(${p.id})" title="حذف">
                  <span class="material-symbols-outlined text-[17px]">delete</span>
                </button>
              </div>
            </td>
          </tr>
        `;
      }).join('');
    }

    async function loadPatches() {
      const tbody = document.getElementById('patches-table-body');
      if (tbody) tbody.innerHTML = '<tr><td colspan="5" class="text-center py-8 text-slate-400">در حال بارگذاری نسخه‌ها...</td></tr>';

      try {
        const res = await fetch(`${BASE_PATH}/api/patches?app_id=${currentAppId}`);
        const patches = await res.json();
        allPatchesData = patches;

        const countEl = document.getElementById('table-patch-count');
        if (countEl) countEl.textContent = `${patches.length} نسخه ثبت‌شده`;
        const statCount = document.getElementById('stat-patch-count');
        if (statCount) statCount.textContent = patches.length;

        const activePatch = patches.find(p => p.is_active === 1);

        // Update Hero/Card info
        const patchVerEl = document.getElementById('current-patch-version');
        const liveChip = document.getElementById('live-status-chip');
        const policyChip = document.getElementById('policy-chip');
        const metaTarget = document.getElementById('meta-target-code');
        const metaDate = document.getElementById('meta-date');
        const metaNotesText = document.getElementById('meta-notes-text');

        if (activePatch) {
          if (patchVerEl) patchVerEl.textContent = `v${activePatch.version}`;
          if (liveChip) {
            liveChip.className = "inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200";
            liveChip.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span><span>فعال در کلاینت‌ها</span>`;
          }
          if (policyChip) {
            policyChip.textContent = activePatch.is_force ? "اجباری (Force Update)" : "اختیاری (Optional)";
          }
          if (metaTarget) metaTarget.textContent = activePatch.target_version_code;
          if (metaDate) metaDate.textContent = activePatch.created_at;
          if (metaNotesText) metaNotesText.textContent = activePatch.release_notes || 'بدون یادداشت فنی';
        } else {
          if (patchVerEl) patchVerEl.textContent = "نسخه استور";
          if (liveChip) {
            liveChip.className = "inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-bold bg-slate-100 text-slate-500 border border-slate-200";
            liveChip.innerHTML = `<span>نسخه خام استور</span>`;
          }
          if (policyChip) policyChip.textContent = "پیش‌فرض استور";
          if (metaTarget) metaTarget.textContent = "-";
          if (metaDate) metaDate.textContent = "-";
          if (metaNotesText) metaNotesText.textContent = "تمامی کاربران هم‌اکنون به نسخه اصلی استور (Native APK/IPA) متصل هستند.";
        }

        renderDashboardRecentTable(patches);
        filterPatchesTable();

      } catch (e) {
        if (tbody) tbody.innerHTML = `<tr><td colspan="5" class="text-center py-6 text-red-600">خطا در بارگذاری جدول: ${e}</td></tr>`;
      }
    }

    async function uploadPatch() {
      if (!selectedFile) {
        showToast('لطفاً ابتدا فایل پچ (.zip یا .bundle) را انتخاب فرمایید.', 'error');
        return;
      }
      const version = document.getElementById('input-patch-version').value.trim();
      if (!version) {
        showToast('لطفاً شماره نسخه پچ (SemVer) را وارد کنید.', 'error');
        return;
      }
      const targetCode = document.getElementById('input-target-build').value || 1;
      const isForce = document.getElementById('select-policy').value === 'force' ? 1 : 0;
      const activate = document.getElementById('auto-deploy').checked ? 1 : 0;
      const notes = encodeURIComponent(document.getElementById('textarea-notes').value.trim());

      const btn = document.getElementById('btn-deploy-patch');
      const origText = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = `<span class="material-symbols-outlined text-[18px] animate-spin">refresh</span><span>در حال بارگذاری باینری و محاسبه هش MD5...</span>`;

      try {
        const url = `${BASE_PATH}/api/patches/upload?app_id=${currentAppId}&version=${version}&target_version_code=${targetCode}&is_force=${isForce}&activate=${activate}&notes=${notes}&filename=${encodeURIComponent(selectedFile.name)}`;
        
        const res = await fetch(url, {
          method: 'POST',
          body: selectedFile
        });
        const data = await res.json();

        if (data.ok) {
          showToast(`پچ نسخه ${version} با موفقیت بارگذاری و فعال گردید!`, 'success');
          document.getElementById('input-patch-version').value = '';
          document.getElementById('textarea-notes').value = '';
          selectedFile = null;
          document.getElementById('selected-file-badge').style.display = 'none';
          await loadApps();
          setTimeout(() => switchView('rollback'), 600);
        } else {
          showToast('خطا در سرور: ' + (data.error || 'ناشناخته'), 'error');
        }
      } catch (e) {
        showToast('خطای شبکه در هنگام آپلود: ' + e, 'error');
      } finally {
        btn.disabled = false;
        btn.innerHTML = origText;
      }
    }

    async function activatePatch(patchId) {
      if (!confirm('آیا از فعال‌سازی و رول‌بک به این نسخه اطمینان دارید؟ تمامی کلاینت‌ها فوراً این نسخه را دریافت خواهند کرد.')) return;
      try {
        const res = await fetch(`${BASE_PATH}/api/patches/activate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ app_id: currentAppId, patch_id: patchId })
        });
        const data = await res.json();
        if (data.ok) {
          showToast('نسخه پچ با موفقیت تغییر کرد.', 'success');
          await loadApps();
        }
      } catch (e) {
        showToast('خطا: ' + e, 'error');
      }
    }

    async function triggerKillSwitch() {
      if (!confirm('⚠️ هشدار بحرانی: آیا از قطع اضطراری تمام پچ‌ها اطمینان دارید؟ تمام کاربران به نسخه خام استور برمی‌گردند.')) return;
      try {
        const res = await fetch(`${BASE_PATH}/api/patches/activate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ app_id: currentAppId, patch_id: 0 })
        });
        const data = await res.json();
        if (data.ok) {
          showToast('دستور رول‌بک سراسری صادر شد. پچ‌ها غیرفعال شدند.', 'success');
          await loadApps();
        }
      } catch (e) {
        showToast('خطا: ' + e, 'error');
      }
    }

    async function toggleForce(patchId) {
      try {
        const res = await fetch(`${BASE_PATH}/api/patches/toggle_force`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ patch_id: patchId })
        });
        const data = await res.json();
        if (data.ok) {
          showToast('سیاست پچ به‌روزرسانی شد.', 'info');
          await loadPatches();
        }
      } catch (e) {
        showToast('خطا: ' + e, 'error');
      }
    }

    async function deletePatch(patchId) {
      if (!confirm('آیا از حذف دائمی این پچ از سرور اطمینان دارید؟')) return;
      try {
        const res = await fetch(`${BASE_PATH}/api/patches/delete`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ patch_id: patchId })
        });
        const data = await res.json();
        if (data.ok) {
          showToast('پچ با موفقیت حذف گردید.', 'info');
          await loadApps();
        }
      } catch (e) {
        showToast('خطا: ' + e, 'error');
      }
    }

    function setLogFilter(cat) {
      activeLogFilter = cat;
      document.querySelectorAll('.log-filter-btn').forEach(btn => {
        if (btn.getAttribute('data-filter') === cat) {
          btn.className = 'log-filter-btn h-7 px-2.5 bg-blue-600 text-white rounded text-xs font-bold transition-all';
        } else {
          btn.className = 'log-filter-btn h-7 px-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs transition-all border-none';
        }
      });
      renderLogsContainer();
    }

    function clearLogsConsole() {
      logsCache = [];
      renderLogsContainer();
      showToast('صفحه نمایش لاگ‌ها پاک‌سازی شد.', 'info');
    }

    function renderLogsContainer() {
      const container = document.getElementById('live-logs-container');
      if (!container) return;
      const filtered = logsCache.filter(l => activeLogFilter === 'ALL' || l.cat === activeLogFilter);
      if (filtered.length === 0) {
        container.innerHTML = '<div class="text-slate-500 italic">لاگی با این فیلتر ثبت نشده است.</div>';
        return;
      }
      container.innerHTML = filtered.map(l => {
        let catColor = "text-slate-400";
        if (l.cat === "CHECK") catColor = "text-blue-400";
        if (l.cat === "DOWNLOAD") catColor = "text-cyan-400";
        if (l.cat === "UPLOAD") catColor = "text-emerald-400";
        if (l.cat === "ROLLBACK") catColor = "text-amber-400";
        if (l.cat === "ERROR") catColor = "text-rose-400";
        return `<div class="leading-relaxed"><span class="text-slate-500">[${l.time}]</span> <span class="${catColor} font-bold">[${l.cat}]</span> <span class="text-slate-200">${l.msg}</span></div>`;
      }).join('');
      container.scrollTop = container.scrollHeight;
    }

    async function pollLogs() {
      try {
        const res = await fetch(`${BASE_PATH}/api/logs`);
        logsCache = await res.json();
        renderLogsContainer();
      } catch (e) {
        // Silent fail for polling
      }
    }

    function renderAppsCards() {
      const grid = document.getElementById('apps-cards-grid');
      if (!grid) return;
      if (!appsList || appsList.length === 0) {
        grid.innerHTML = '<div class="col-span-full text-center py-8 text-slate-400">هیچ برنامه‌ای یافت نشد.</div>';
        return;
      }
      grid.innerHTML = appsList.map(a => {
        const isCurrent = a.app_id === currentAppId;
        const activeVerText = a.active_version ? `v${a.active_version}` : 'بدون پچ فعال';
        const activeVerClass = a.active_version ? 'bg-emerald-100 text-emerald-800 border-emerald-200' : 'bg-slate-100 text-slate-600 border-slate-200';
        const cardBorder = isCurrent ? 'border-2 border-blue-500 shadow-md ring-4 ring-blue-50' : 'border border-slate-200 hover:border-slate-300 hover:shadow-sm';

        return `
          <div class="bg-white rounded-2xl p-5 ${cardBorder} flex flex-col justify-between transition-all">
            <div>
              <div class="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
                <div class="flex items-center gap-3">
                  <div class="w-11 h-11 rounded-xl bg-blue-600 text-white font-black flex items-center justify-center text-sm shadow-sm">${a.name.substring(0, 2)}</div>
                  <div>
                    <h3 class="text-sm font-bold text-slate-900">${a.name}</h3>
                    <span class="text-[11px] font-mono text-slate-400 block" dir="ltr">${a.package_name}</span>
                  </div>
                </div>
                ${isCurrent ? '<span class="text-[10px] bg-blue-600 text-white font-extrabold px-2.5 py-0.5 rounded-full">برنامه فعال</span>' : ''}
              </div>

              <div class="text-xs text-slate-600 mb-4 leading-relaxed">${a.description || 'بدون توضیحات ثبت‌شده'}</div>

              <div class="grid grid-cols-2 gap-2 text-xs bg-slate-50 p-3 rounded-xl border border-slate-100 mb-4">
                <div>
                  <span class="text-slate-400 block text-[10px]">شناسه:</span>
                  <span class="font-mono text-blue-600 font-bold" dir="ltr">${a.app_id}</span>
                </div>
                <div>
                  <span class="text-slate-400 block text-[10px]">کل پچ‌ها:</span>
                  <span class="font-bold text-slate-800">${a.total_patches || 0} نسخه</span>
                </div>
                <div class="col-span-2 pt-2 border-t border-slate-200/60 flex items-center justify-between">
                  <span class="text-slate-400 text-[10px]">نسخه جاری کلاینت‌ها:</span>
                  <span class="px-2 py-0.5 rounded text-[11px] font-mono font-bold border ${activeVerClass}">${activeVerText}</span>
                </div>
              </div>
            </div>

            <div class="pt-3 border-t border-slate-100 flex items-center justify-between">
              <span class="text-[10px] text-slate-400 font-mono" dir="ltr">${a.created_at}</span>
              ${!isCurrent ? `
                <button onclick="selectApp('${a.app_id}'); switchView('dashboard');" class="h-8 px-3.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold transition-all shadow-xs flex items-center gap-1">
                  <span>ورود به این برنامه</span>
                  <span class="material-symbols-outlined text-[15px]">arrow_back</span>
                </button>
              ` : `
                <button onclick="switchView('dashboard')" class="h-8 px-3.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-bold transition-all border border-slate-200 flex items-center gap-1">
                  <span>مشاهده داشبورد</span>
                  <span class="material-symbols-outlined text-[15px]">arrow_back</span>
                </button>
              `}
            </div>
          </div>
        `;
      }).join('');
    }

    // Modal Handlers
    function openAppModal() {
      const modal = document.getElementById('app-switcher-modal');
      const list = document.getElementById('modal-apps-list');
      list.innerHTML = appsList.map(a => {
        const isCurrent = a.app_id === currentAppId;
        const border = isCurrent ? "border-blue-500 bg-blue-50/50" : "border-slate-200 hover:bg-slate-50";
        const vText = a.active_version ? `v${a.active_version}` : 'بدون پچ';
        return `
          <div class="flex items-center justify-between p-3 rounded-xl border ${border} cursor-pointer transition-all" onclick="selectApp('${a.app_id}')">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-blue-600 text-white font-bold flex items-center justify-center text-sm shadow-xs">${a.name.substring(0, 2)}</div>
              <div>
                <div class="text-xs font-bold text-slate-900">${a.name}</div>
                <div class="font-mono text-[11px] text-slate-500" dir="ltr">${a.package_name}</div>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-[11px] text-slate-500 font-mono">${vText}</span>
              ${isCurrent ? '<span class="text-[11px] font-bold text-blue-700 bg-blue-100 px-2 py-0.5 rounded">انتخاب شده</span>' : ''}
            </div>
          </div>
        `;
      }).join('');
      modal.classList.remove('hidden');
    }

    function closeAppModal() {
      document.getElementById('app-switcher-modal').classList.add('hidden');
    }

    function selectApp(appId) {
      currentAppId = appId;
      closeAppModal();
      renderCurrentAppBanner();
      loadPatches();
      renderAppsCards();
      showToast(`برنامه به ${appId} تغییر یافت.`, 'info');
    }

    function openNewAppModal() {
      document.getElementById('new-app-modal').classList.remove('hidden');
    }

    function closeNewAppModal() {
      document.getElementById('new-app-modal').classList.add('hidden');
    }

    async function submitNewApp(e) {
      e.preventDefault();
      const appId = document.getElementById('input-new-app-id').value.trim();
      const name = document.getElementById('input-new-app-name').value.trim();
      const pkg = document.getElementById('input-new-app-pkg').value.trim();
      const desc = document.getElementById('input-new-app-desc').value.trim();

      if (!appId || !name || !pkg) {
        showToast('لطفاً فیلدهای الزامی را پر کنید.', 'error');
        return;
      }

      try {
        const res = await fetch(`${BASE_PATH}/api/apps`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ app_id: appId, name: name, package_name: pkg, description: desc })
        });
        const data = await res.json();
        if (data.ok) {
          showToast(`برنامه ${name} با موفقیت افزوده شد.`, 'success');
          closeNewAppModal();
          currentAppId = appId;
          await loadApps();
          switchView('apps');
        } else {
          showToast('خطا: ' + data.error, 'error');
        }
      } catch (e) {
        showToast('خطا در ثبت برنامه: ' + e, 'error');
      }
    }
  </script>
</body>
</html>
"""


# ==============================================================================
# Request Handler
# ==============================================================================
class PatchRequestHandler(BaseHTTPRequestHandler):

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        client_ip = self.client_address[0]

        # 1. Web Dashboard Root & Dedicated View Paths
        if parsed.path in ["/", "/index.html", "/dashboard", "/publisher", "/rollback", "/logs", "/apps"]:
            self.send_response(200)
            self.send_cors_headers()
            self.send_header("Content-Type", "text/html; charset=utf-8")
            body = DASHBOARD_HTML.encode("utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # 2. Status API
        if parsed.path == "/api/status":
            apps = db_get_apps()
            data = {
                "port": PORT,
                "ips": get_detected_ips(),
                "total_apps": len(apps)
            }
            self._send_json(data)
            return

        # 3. Apps API
        if parsed.path == "/api/apps":
            apps = db_get_apps()
            self._send_json(apps)
            return

        # 4. Patches API
        if parsed.path == "/api/patches":
            query = parse_qs(parsed.query)
            app_id = query.get("app_id", ["quran_app"])[0]
            patches = db_get_patches(app_id)
            self._send_json(patches)
            return

        # 5. Logs API
        if parsed.path == "/api/logs":
            self._send_json(SERVER_LOGS)
            return

        # 6. Check update endpoint for Flutter
        if parsed.path == "/check":
            query = parse_qs(parsed.query)
            app_id = query.get("app_id", ["quran_app"])[0]
            version_code = query.get("app_version_code", [None])[0]
            current_patch = query.get("current_patch", [None])[0]

            add_log("CHECK", f"Request from {client_ip} | app={app_id} | code={version_code} | current_patch={current_patch}")

            active_patch = db_get_active_patch(app_id)
            if not active_patch:
                add_log("CHECK", f"No active patch found for app '{app_id}'.")
                self._send_json({
                    "has_update": False,
                    "message": "No active patch available for this app"
                })
                return

            # Check if client already on this patch version
            if current_patch and str(current_patch).strip() == str(active_patch["version"]).strip():
                add_log("CHECK", f"Client {client_ip} already on latest patch ({current_patch}).")
                self._send_json({
                    "has_update": False,
                    "message": "Already up to date",
                    "current_version": current_patch
                })
                return

            host = self.headers.get("Host") or f"{get_detected_ips()[0]}:{PORT}"
            # Relative download URL
            download_url = f"http://{host}/patches/{app_id}/{active_patch['version']}/{active_patch['filename']}"

            response_data = {
                "has_update": True,
                "app_id": app_id,
                "version": active_patch["version"],
                "is_force": bool(active_patch["is_force"]),
                "target_version_code": active_patch["target_version_code"],
                "download_url": download_url,
                "md5": active_patch["md5"],
                "size_bytes": active_patch["size_bytes"],
                "release_notes": active_patch["release_notes"],
                "created_at": active_patch["created_at"]
            }
            add_log("CHECK", f"Offering update to {client_ip}: app={app_id} v={active_patch['version']} force={bool(active_patch['is_force'])}")
            self._send_json(response_data)
            return

        # 7. Static download of patch files (/patches/app_id/version/filename)
        if parsed.path.startswith("/patches/"):
            rel_path = unquote(parsed.path[len("/patches/"):])
            file_path = os.path.normpath(os.path.join(PATCH_DIR, rel_path))

            if not file_path.startswith(PATCH_DIR) or not os.path.isfile(file_path):
                self._send_json({"error": "File not found"}, status=404)
                return

            add_log("DOWNLOAD", f"{client_ip} downloaded {os.path.basename(file_path)}")
            file_size = os.path.getsize(file_path)
            content_type, _ = mimetypes.guess_type(file_path)

            self.send_response(200)
            self.send_cors_headers()
            self.send_header("Content-Type", content_type or "application/octet-stream")
            self.send_header("Content-Length", str(file_size))
            self.send_header("Content-Disposition", f'attachment; filename="{os.path.basename(file_path)}"')
            self.end_headers()

            with open(file_path, "rb") as f:
                while chunk := f.read(65536):
                    self.wfile.write(chunk)
            return

        self._send_json({"error": "Endpoint not found"}, status=404)

    def do_POST(self):
        parsed = urlparse(self.path)
        client_ip = self.client_address[0]

        # 1. Add new App
        if parsed.path == "/api/apps":
            try:
                content_len = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(content_len).decode("utf-8"))
                app_id = body.get("app_id", "").strip()
                name = body.get("name", "").strip()
                package_name = body.get("package_name", "").strip()
                desc = body.get("description", "").strip()

                if not app_id or not name or not package_name:
                    self._send_json({"ok": False, "error": "Missing fields"}, status=400)
                    return

                db_add_app(app_id, name, package_name, desc)
                add_log("APP", f"Created new app: {app_id} ({name})")
                self._send_json({"ok": True})
            except Exception as e:
                add_log("ERROR", f"Failed to create app: {e}")
                self._send_json({"ok": False, "error": str(e)}, status=500)
            return

        # 2. Activate / Rollback Patch
        if parsed.path == "/api/patches/activate":
            try:
                content_len = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(content_len).decode("utf-8"))
                app_id = body.get("app_id")
                patch_id = int(body.get("patch_id", 0))

                db_activate_patch(app_id, patch_id)
                action = f"Activated patch #{patch_id}" if patch_id > 0 else "Deactivated all patches (Rollback to store default)"
                add_log("ROLLBACK", f"{action} for app '{app_id}'")
                self._send_json({"ok": True})
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, status=500)
            return

        # 3. Toggle Force Update
        if parsed.path == "/api/patches/toggle_force":
            try:
                content_len = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(content_len).decode("utf-8"))
                patch_id = int(body.get("patch_id"))
                db_toggle_force(patch_id)
                add_log("POLICY", f"Toggled force flag for patch #{patch_id}")
                self._send_json({"ok": True})
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, status=500)
            return

        # 4. Delete Patch
        if parsed.path == "/api/patches/delete":
            try:
                content_len = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(content_len).decode("utf-8"))
                patch_id = int(body.get("patch_id"))
                db_delete_patch(patch_id)
                add_log("DELETE", f"Deleted patch #{patch_id}")
                self._send_json({"ok": True})
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, status=500)
            return

        # 5. Upload New Patch
        if parsed.path == "/api/patches/upload":
            query = parse_qs(parsed.query)
            app_id = query.get("app_id", ["quran_app"])[0]
            version = query.get("version", ["1.0.0"])[0].strip()
            target_version_code = int(query.get("target_version_code", [1])[0])
            is_force = query.get("is_force", ["0"])[0] in ["1", "true"]
            activate = query.get("activate", ["1"])[0] in ["1", "true"]
            release_notes = query.get("notes", [""])[0]
            filename = query.get("filename", ["patch.zip"])[0]
            filename = os.path.basename(filename) or "patch.zip"

            content_len = int(self.headers.get("Content-Length", 0))
            if content_len == 0:
                self._send_json({"ok": False, "error": "Empty file received"}, status=400)
                return

            target_dir = os.path.join(PATCH_DIR, app_id, version)
            os.makedirs(target_dir, exist_ok=True)
            target_file = os.path.join(target_dir, filename)

            add_log("UPLOAD", f"Uploading patch for {app_id} v{version} ({round(content_len/1024, 1)} KB)...")

            try:
                remaining = content_len
                with open(target_file, "wb") as f:
                    while remaining > 0:
                        chunk_size = min(remaining, 65536)
                        chunk = self.rfile.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        remaining -= len(chunk)

                md5 = compute_file_md5(target_file)
                file_size = os.path.getsize(target_file)

                patch_id = db_create_patch(
                    app_id=app_id,
                    version=version,
                    target_version_code=target_version_code,
                    is_force=is_force,
                    activate=activate,
                    filename=filename,
                    file_path=target_file,
                    size_bytes=file_size,
                    md5=md5,
                    release_notes=release_notes
                )

                add_log("UPLOAD", f"Saved patch #{patch_id} (v{version}) for {app_id}. MD5: {md5[:8]}")
                self._send_json({
                    "ok": True,
                    "patch_id": patch_id,
                    "version": version,
                    "size_bytes": file_size,
                    "md5": md5
                })
            except Exception as e:
                add_log("ERROR", f"Upload failed: {e}")
                self._send_json({"ok": False, "error": str(e)}, status=500)
            return

        self._send_json({"error": "Endpoint not found"}, status=404)

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # Suppress default console logs
        pass


def run_server():
    init_db()
    detected_ips = get_detected_ips()
    primary_ip = detected_ips[0] if detected_ips else "127.0.0.1"

    print("=" * 65)
    print("🚀 FLUTTER PATCH SERVER & OTA HUB IS RUNNING!")
    print(f"📡 Local Port : {PORT}")
    print(f"💻 Wi-Fi / LAN IP : {primary_ip}")
    print(f"🌐 Web Dashboard  : http://localhost:{PORT}")
    print(f"📱 Flutter Check  : http://{primary_ip}:{PORT}/check?app_id=quran_app")
    print(f"📂 Patches Folder : {PATCH_DIR}")
    print(f"💾 SQLite Database: {DB_PATH}")
    print("=" * 65)

    add_log("INFO", f"Server started on port {PORT}. Ready for requests.")
    server = HTTPServer(("0.0.0.0", PORT), PatchRequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.server_close()


if __name__ == "__main__":
    run_server()
