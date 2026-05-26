import os
import asyncio
from datetime import datetime, timezone
from fastapi import Request
from fastapi.responses import RedirectResponse
from nicegui import app, ui

from api_client import APIClient

# تنظیم متغیرهای محیطی
PORT = int(os.getenv("FRONTEND_DEV_PORT", "8080"))
BALE_BOT_URL = os.getenv("VITE_BALE_OTP_BOT_URL", "https://ble.ir/tafakor_otp_bot")

# استایل‌های سراسری لایت تم بومی و انیمیشن‌های CSS منطبق با تلویند Vue
ui.add_head_html("""
<link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css" rel="stylesheet" type="text/css" />
<style>
    body {
        font-family: 'Vazirmatn', sans-serif !important;
        background-color: #f3f4f6 !important; /* bg-gray-100 */
        color: #1f2937 !important; /* text-gray-900 */
        direction: rtl;
        margin: 0;
        padding: 0;
    }
    /* کانتینر مرکزی شبیه‌ساز موبایل دقیقا منطبق با max-w-md */
    .mobile-viewport {
        max-width: 448px; /* max-w-md */
        margin: 0 auto;
        background-color: #f9fafb !important; /* bg-gray-50 */
        box-shadow: 0 25px 50px -12px rgb(0 0 0 / 0.25) !important; /* shadow-2xl */
        min-height: 100vh;
        border-left: 1px solid #e5e7eb;
        border-right: 1px solid #e5e7eb;
        position: relative;
    }
    .base-card {
        background-color: #ffffff !important;
        border: 1px solid #f3f4f6 !important;
        border-radius: 16px !important;
        box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.05), 0 1px 2px -1px rgb(0 0 0 / 0.05) !important; /* shadow-sm */
        transition: all 0.2s ease-in-out;
    }
    .base-card:hover {
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1) !important; /* shadow-md */
    }
    .btn-primary {
        background-color: #4f46e5 !important; /* bg-indigo-600 */
        color: #ffffff !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease;
    }
    .btn-primary:hover {
        background-color: #4338ca !important; /* bg-indigo-700 */
    }
    .btn-outline {
        border: 1px solid #e5e7eb !important;
        background-color: #ffffff !important;
        color: #4f46e5 !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
    }
    .btn-outline:hover {
        background-color: #f5f3ff !important; /* bg-indigo-50 */
    }
    .btn-danger {
        background-color: #ef4444 !important; /* bg-red-500 */
        color: #ffffff !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
    }
    .btn-danger:hover {
        background-color: #dc2626 !important; /* bg-red-600 */
    }
    .fab-btn {
        background-color: #4f46e5 !important;
        color: #ffffff !important;
        width: 56px !important;
        height: 56px !important;
        border-radius: 9999px !important;
        box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1) !important; /* shadow-lg */
        transition: all 0.2s ease;
        position: fixed;
        bottom: 80px;
        left: calc(50% - 200px); /* تنظیم نسبت به viewport مرکزی */
        z-index: 40;
    }
    @media (max-width: 448px) {
        .fab-btn {
            left: auto !important;
            right: 24px !important;
        }
    }
    .fab-btn:active {
        transform: scale(0.95);
    }
    /* حذف حاشیه‌ها و استایل پیش‌فرض اینپوت‌ها */
    .base-input {
        background-color: #ffffff !important;
    }
</style>
""", shared=True)

# ----------------- Helper Functions -----------------
def get_api_client() -> APIClient:
    token = app.storage.user.get("auth_token")
    return APIClient(token=token)

def logout_user():
    app.storage.user.clear()
    ui.navigate.to('/login')

def get_relative_time(date_str):
    if not date_str:
        return ""
    try:
        clean_str = date_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_str)
        now = datetime.now(timezone.utc)
        diff = now - dt
        seconds = int(diff.total_seconds())
        if seconds < 0:
            seconds = 0
            
        if seconds < 60:
            return "چند ثانیه پیش"
        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes} دقیقه پیش"
        hours = minutes // 60
        if hours < 24:
            return f"{hours} ساعت پیش"
        days = hours // 24
        return f"{days} روز پیش"
    except Exception:
        return date_str[:10] if date_str else ""

# ----------------- Layout Wrapper (Decorator) -----------------
def with_layout(current_tab: str = 'home'):
    def decorator(func):
        async def wrapper(request: Request = None):
            # منوی کشویی سمت راست (SidebarDrawer) - این یک المان تاپ‌لول است و باید خارج از کانتینرها باشد
            with ui.right_drawer(value=False).props('width=280') as sidebar_drawer:
                with ui.row().classes("w-full justify-between items-center px-4 h-14 border-b border-gray-200"):
                    ui.label("منو").classes("text-lg font-bold text-indigo-700")
                    ui.button(icon="close", on_click=sidebar_drawer.hide).classes("text-gray-500 flat round").props('dense')
                with ui.column().classes("w-full p-6 items-center justify-center min-h-[200px] text-gray-400"):
                    ui.label("به زودی...").classes("text-lg font-medium")

            # کانتینر اصلی موبایل‌فرست کاملا منطبق با سبک Vue
            with ui.column().classes("w-full min-h-screen mobile-viewport p-0 gap-0") as container:
                # هدر ثابت بالایی (AppHeader)
                with ui.row().classes("w-full h-14 bg-white/80 backdrop-blur border-b border-gray-200 justify-between items-center px-4 sticky top-0 z-40"):
                    # منوی همبرگر سمت راست
                    ui.button(
                        icon="menu",
                        on_click=lambda: sidebar_drawer.toggle()
                    ).classes("text-gray-600 flat round").props('dense')
                    
                    # عنوان در وسط
                    ui.label("تفکر").classes("text-lg font-bold text-indigo-700 absolute-center")
                    
                    # دکمه توخالی سمت چپ برای تعادل در فاصله
                    ui.label("").classes("w-8 h-8")

                # محتوای اصلی صفحه با کلاس‌های Vue
                with ui.column().classes("w-full flex-grow px-4 pt-4 pb-24 gap-4"):
                    await func()
                
                # نویگیشن بار پایین ثابت (BottomNav)
                with ui.row().classes("w-full h-14 bg-white border-t border-gray-200 justify-around items-center sticky bottom-0 z-40 shadow-lg py-1"):
                    # تب خانه
                    home_color = "text-indigo-600" if current_tab == 'home' else "text-gray-400 hover:text-gray-600"
                    with ui.column().classes("items-center cursor-pointer gap-0.5").on("click", lambda: ui.navigate.to('/')):
                        ui.icon("home", size="24px").classes(home_color)
                        ui.label("خانه").classes(f"text-[11px] {home_color} font-medium")
                    
                    # تب پروفایل
                    profile_color = "text-indigo-600" if current_tab == 'profile' else "text-gray-400 hover:text-gray-600"
                    with ui.column().classes("items-center cursor-pointer gap-0.5").on("click", lambda: ui.navigate.to('/profile')):
                        ui.icon("person", size="24px").classes(profile_color)
                        ui.label("پروفایل").classes(f"text-[11px] {profile_color} font-medium")
            return container
        return wrapper
    return decorator

# ----------------- Auth Pages -----------------

@ui.page('/login')
def login_page():
    if app.storage.user.get("auth_token"):
        return RedirectResponse('/')

    state = {
        'phone': '',
        'otp': '',
        'step': 'phone', # phone | otp
        'sent_channel': 'sms',
        'timer': 120,
        'timer_active': False
    }

    async def run_countdown():
        state['timer_active'] = True
        while state['timer'] > 0 and state['step'] == 'otp':
            await asyncio.sleep(1)
            state['timer'] -= 1
            timer_label.set_text(f"ارسال مجدد کد پس از: {state['timer']} ثانیه")
            if state['timer'] == 0:
                resend_btn.set_visibility(True)
                timer_label.set_text("")
                break

    async def handle_request_otp(force_sms=False):
        phone = state['phone'].strip()
        if not phone.startswith("09") or len(phone) != 11:
            ui.notify("❌ شماره موبایل نامعتبر است. نمونه صحیح: 09123456789", type="warning")
            return
            
        loading_spinner.set_visibility(True)
        try:
            client = get_api_client()
            status_code, data = await client.request_otp(phone, force_sms=force_sms)
            if status_code == 200:
                state['sent_channel'] = data.get("channel", "sms")
                state['step'] = 'otp'
                state['timer'] = 120
                
                # نمایش اعلان منطبق با کانال ارسال
                if state['sent_channel'] == 'sms':
                    ui.notify("کد تایید ورود با موفقیت پیامک شد.", type="success")
                    badge.set_text("📱 کد تأیید پیامکی به شماره شما ارسال شد.")
                    badge.classes("bg-indigo-50 border-indigo-100 text-indigo-800")
                elif state['sent_channel'] == 'bale':
                    ui.notify("کد تایید با موفقیت در ربات بله شما صادر شد.", type="success")
                    badge.set_text("💬 کد تأیید در پیام‌رسان بله برای شما صادر شد.")
                    badge.classes("bg-emerald-50 border-emerald-100 text-emerald-800")
                else:
                    ui.notify("حالت شبیه‌سازی فعال است.", type="info")
                    badge.set_text(f"🛠️ [توسعه] کد تستی: {data.get('otp')}")
                    badge.classes("bg-amber-50 border-amber-100 text-amber-800")

                phone_form.set_visibility(False)
                otp_form.set_visibility(True)
                resend_btn.set_visibility(False)
                badge.set_visibility(True)
                
                asyncio.create_task(run_countdown())
            else:
                # فال‌بک هوشمند در صورت خرابی وب‌سرویس پیامکی (دقیقا شبیه منطق PhoneForm.vue)
                ui.notify("سامانه پیامکی با اختلال مواجه شد. در مرحله بعد می‌توانید کد را از ربات بله دریافت کنید.", type="warning")
                state['sent_channel'] = 'sms'
                state['step'] = 'otp'
                state['timer'] = 120
                
                badge.set_text("📱 سامانه پیامکی مختل است. لطفا از ربات بله استفاده کنید.")
                badge.classes("bg-red-50 border-red-100 text-red-800")
                
                phone_form.set_visibility(False)
                otp_form.set_visibility(True)
                resend_btn.set_visibility(True)
                badge.set_visibility(True)
                
                asyncio.create_task(run_countdown())
        finally:
            loading_spinner.set_visibility(False)

    async def handle_verify_otp():
        otp = state['otp'].strip()
        if len(otp) != 4:
            ui.notify("❌ کد تایید باید ۴ رقم باشد.", type="warning")
            return
            
        loading_spinner.set_visibility(True)
        try:
            client = get_api_client()
            status_code, data = await client.verify_otp(state['phone'], otp)
            if status_code == 200:
                app.storage.user['auth_token'] = data.get("token")
                app.storage.user['phone'] = data.get("user", {}).get("phone")
                ui.notify("👋 ورود موفقیت‌آمیز بود! خوش آمدید.", type="success")
                await asyncio.sleep(0.5)
                ui.navigate.to('/')
            else:
                ui.notify(data.get("error", "کد تأیید نادرست یا منقضی شده است"), type="negative")
        finally:
            loading_spinner.set_visibility(False)

    def handle_back():
        state['step'] = 'phone'
        otp_form.set_visibility(False)
        phone_form.set_visibility(True)
        badge.set_visibility(False)

    def open_bale_bot():
        ui.navigate.to(BALE_BOT_URL, new_tab=True)
        state['sent_channel'] = 'bale'
        badge.set_text("💬 کد تأیید در پیام‌رسان بله برای شما صادر شد.")
        badge.classes("bg-emerald-50 border-emerald-100 text-emerald-800")
        ui.notify("ربات بله در تب جدید باز شد. شماره خود را به اشتراک بگذارید تا کد را دریافت کنید.", type="info")

    with ui.column().classes("w-full min-h-screen items-center justify-center p-4 bg-gray-50"):
        # کارت تراز شده موبایل فرست
        with ui.column().classes("w-full max-w-sm gap-6"):
            # هدر کارت ورود
            with ui.column().classes("w-full items-center gap-2 mb-4 text-center"):
                ui.label("تفکر").classes("text-3xl font-bold text-indigo-700 mb-1")
                ui.label("یادداشت‌های خود را همگام در تلگرام و بله منتشر کنید").classes("text-sm text-gray-500 max-w-[280px] leading-relaxed")
            
            # اسپینر لودینگ
            loading_spinner = ui.spinner(size='lg', color='indigo').classes("self-center")
            loading_spinner.set_visibility(False)

            # جعبه زیبای نمایش وضعیت و مقصد ارسال کد تایید (OtpForm.vue)
            badge = ui.label("").classes("p-3.5 border rounded-xl text-xs font-semibold text-center w-full transition-all duration-300")
            badge.set_visibility(False)

            # ۱. فرم ورود شماره تلفن (PhoneForm)
            with ui.column().classes("w-full gap-4 base-card p-6") as phone_form:
                phone_input = ui.input(
                    label="شماره موبایل", 
                    placeholder="۰۹xxxxxxxxx", 
                    on_change=lambda e: state.update(phone=e.value)
                ).classes("w-full base-input text-center font-semibold tracking-wider text-base").props('outlined rounded maxlength="11" inputmode="numeric"')
                
                # دکمه با استایل Vue
                phone_btn = ui.button("ارسال کد تأیید ورود", on_click=lambda: handle_request_otp(False)).classes("w-full btn-primary py-3 text-sm")

            # ۲. فرم ورود کد تایید (OtpForm)
            with ui.column().classes("w-full gap-4 base-card p-6") as otp_form:
                otp_form.set_visibility(False)
                
                otp_input = ui.input(
                    label="کد تایید ورود", 
                    placeholder="۴ رقم",
                    on_change=lambda e: state.update(otp=e.value)
                ).classes("w-full base-input text-center font-bold tracking-widest text-lg").props('outlined rounded maxlength="4" inputmode="numeric"')
                
                ui.button("ورود به تفکر", on_click=handle_verify_otp).classes("w-full btn-primary py-3 text-sm")
                
                # تایمر و دکمه ارسال مجدد
                with ui.column().classes("w-full items-center gap-2 py-1 text-sm"):
                    timer_label = ui.label("").classes("text-gray-500 font-medium")
                    resend_btn = ui.button("ارسال مجدد کد تأیید (پیامک)", on_click=lambda: handle_request_otp(True)).classes("text-xs text-indigo-600 hover:text-indigo-800 font-medium flat").props('dense')
                    resend_btn.set_visibility(False)

                # دکمه Fallback بله (OtpForm.vue)
                with ui.column().classes("w-full border-t border-gray-100 pt-4 items-center gap-2"):
                    ui.button("💬 دریافت کد ورود در ربات بله", on_click=open_bale_bot).classes("px-4 py-2 text-xs font-semibold text-gray-600 bg-gray-50 border border-gray-200 hover:bg-gray-100 rounded-xl transition-all shadow-sm")
                    ui.label("در صورت عدم دریافت پیامک، ربات بله را استارت کرده و دکمه ارسال شماره را بزنید.").classes("text-[10px] text-gray-400 text-center max-w-[250px] leading-relaxed")

                # دکمه بازگشت و اصلاح شماره
                ui.button("اصلاح شماره موبایل", on_click=handle_back).classes("w-full text-center text-xs text-gray-400 hover:text-indigo-600 transition-colors duration-200 mt-2 flat").props('dense')

# ----------------- Home Page -----------------

@ui.page('/')
@with_layout(current_tab='home')
async def home_page():
    api = get_api_client()

    state = {
        'notes': [],
        'search_query': '',
        'loading': True
    }

    async def load_notes(query=''):
        state['loading'] = True
        render_page()
        try:
            if query:
                status_code, data = await api.search_notes(query)
            else:
                status_code, data = await api.fetch_notes()
                
            if status_code == 200:
                # سریالایزر جنگو داده‌ها را درون results یا به صورت آرایه مستقیم بازمی‌گرداند
                state['notes'] = data.get("results") if isinstance(data, dict) and "results" in data else data
            elif status_code == 401:
                logout_user()
                return
            else:
                state['notes'] = []
        except Exception:
            state['notes'] = []
        finally:
            state['loading'] = False
            render_page()

    async def handle_delete(note_id):
        # دیالوگ حذف تاییدیه منطبق با Vue
        with ui.dialog() as dialog, ui.card().classes("p-6 gap-4"):
            ui.label("یادداشت حذف شود؟").classes("text-base font-bold text-gray-800")
            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("انصراف", on_click=dialog.close).classes("text-slate-400 flat")
                async def confirm_delete():
                    dialog.close()
                    status_code, _ = await api.delete_note(note_id)
                    if status_code in (200, 204):
                        ui.notify("یادداشت حذف شد", type="success")
                        await load_notes(state['search_query'])
                ui.button("حذف", on_click=confirm_delete).classes("bg-red-500 text-white rounded-xl")
        dialog.open()

    def open_note_modal(note=None):
        # پیاده‌سازی پاپ‌آپ ساخت/ویرایش منطبق بر NoteModal.vue
        modal_form = {
            'id': note.get('id') if note else None,
            'title': note.get('title') or '' if note else '',
            'content': note.get('content') or '' if note else '',
            'send_to_telegram': note.get('send_to_telegram') or False if note else False,
            'send_to_bale': note.get('send_to_bale') or False if note else False,
            'saving': False
        }

        async def handle_save():
            content = modal_form['content'].strip()
            if not content:
                ui.notify("متن یادداشت نمی‌تواند خالی باشد", type="warning")
                return
            
            modal_form['saving'] = True
            payload = {
                "title": modal_form['title'] or None,
                "content": content,
                "send_to_telegram": modal_form['send_to_telegram'],
                "send_to_bale": modal_form['send_to_bale']
            }
            try:
                if modal_form['id']:
                    status_code, data = await api.update_note(modal_form['id'], payload)
                    if status_code == 200:
                        ui.notify("یادداشت ویرایش شد", type="success")
                        dialog.close()
                        await load_notes(state['search_query'])
                    else:
                        ui.notify(data.get("error", "خطا در ویرایش یادداشت"), type="negative")
                else:
                    status_code, data = await api.create_note(payload)
                    if status_code in (200, 201):
                        ui.notify("یادداشت جدید ایجاد شد", type="success")
                        dialog.close()
                        await load_notes(state['search_query'])
                    else:
                        ui.notify(data.get("error", "خطا در ایجاد یادداشت"), type="negative")
            finally:
                modal_form['saving'] = False

        with ui.dialog() as dialog, ui.card().classes("w-full max-w-md p-6 gap-4 bg-white rounded-t-3xl sm:rounded-2xl shadow-2xl"):
            with ui.row().classes("w-full justify-between items-center"):
                ui.label("ویرایش یادداشت" if note else "یادداشت جدید").classes("text-xl font-bold text-gray-800")
                ui.button(icon="close", on_click=dialog.close).classes("text-gray-400 flat round").props('dense')

            # فیلدهای فرم
            title_input = ui.input(
                label="عنوان (اختیاری)", 
                placeholder="عنوان یادداشت...",
                value=modal_form['title'],
                on_change=lambda e: modal_form.update(title=e.value)
            ).classes("w-full base-input").props('outlined rounded')

            content_input = ui.textarea(
                label="متن یادداشت",
                placeholder="متن خود را با **Markdown** بنویسید...",
                value=modal_form['content'],
                on_change=lambda e: modal_form.update(content=e.value)
            ).classes("w-full base-input").props('outlined rounded autogrow rows="6"')

            # سوئیچ‌ها (منطبق با NoteModal.vue)
            with ui.column().classes("w-full gap-3 pt-2"):
                with ui.row().classes("w-full justify-between items-center"):
                    ui.label("ارسال به تلگرام").classes("text-sm text-gray-700")
                    tg_switch = ui.switch(value=modal_form['send_to_telegram'], on_change=lambda e: modal_form.update(send_to_telegram=e.value))
                with ui.row().classes("w-full justify-between items-center"):
                    ui.label("ارسال به بله").classes("text-sm text-gray-700")
                    bale_switch = ui.switch(value=modal_form['send_to_bale'], on_change=lambda e: modal_form.update(send_to_bale=e.value))

            ui.button(
                "ویرایش" if note else "ذخیره", 
                on_click=handle_save
            ).classes("w-full btn-primary py-2.5 mt-2")

        dialog.open()

    def render_page():
        content_container.clear()
        with content_container:
            # ۱. نوار جستجو (SearchBar.vue)
            with ui.row().classes("w-full gap-2 items-center"):
                ui.input(
                    placeholder="🔍 جستجو...",
                    value=state['search_query'],
                    on_change=lambda e: state.update(search_query=e.value) or asyncio.create_task(load_notes(e.value))
                ).classes("w-full base-input").props('outlined rounded dense')

            # ۲. حالت در حال لودینگ (Skeleton)
            if state['loading']:
                with ui.column().classes("w-full gap-4 mt-6"):
                    for _ in range(3):
                        with ui.card().classes("w-full p-4 base-card animate-pulse gap-3"):
                            ui.label("").classes("h-4 bg-gray-200 rounded w-3/4")
                            ui.label("").classes("h-3 bg-gray-100 rounded w-full")
                            ui.label("").classes("h-3 bg-gray-100 rounded w-2/3")
                return

            # ۳. حالت خالی بودن
            if len(state['notes']) == 0:
                with ui.column().classes("w-full items-center py-20 text-gray-400 gap-2"):
                    ui.label("هنوز یادداشتی نداری!").classes("text-lg font-medium")
                    ui.label("روی دکمهٔ + کلیک کن و شروع کن").classes("text-sm")
                return

            # ۴. نمایش یادداشت‌ها (NoteCard.vue)
            with ui.column().classes("w-full gap-4 mt-4"):
                for note in state['notes']:
                    # کانتینر کارت
                    with ui.card().classes("w-full p-4 base-card cursor-pointer relative gap-2") as card:
                        # کلیک برای ویرایش
                        card.on("click", lambda _, n=note: open_note_modal(n))
                        
                        # هدر کارت
                        with ui.row().classes("w-full justify-between items-center"):
                            ui.label(note.get('title') or "بدون عنوان").classes("font-semibold text-gray-800 text-base line-clamp-1")
                            
                            # نمایش تگ ارسال تلگرام/بله بر اساس is_sent (منطبق بر NoteCard.vue)
                            with ui.row().classes("gap-1 items-center"):
                                if note.get('is_sent_to_telegram'):
                                    ui.label("✈️").classes("text-xs").props('title="ارسال شده در تلگرام"')
                                if note.get('is_sent_to_bale'):
                                    ui.label("💬").classes("text-xs").props('title="ارسال شده در بله"')

                        # متن یادداشت
                        ui.label(note.get('content', '')).classes("text-sm text-gray-600 line-clamp-2 leading-relaxed")

                        # فوتر کارت
                        with ui.row().classes("w-full justify-between items-center text-xs text-gray-400 mt-1"):
                            ui.label(get_relative_time(note.get('created_at'))).classes("font-medium")
                            
                            # دکمه حذف
                            ui.button(
                                icon="delete",
                                on_click=lambda _, n_id=note['id']: handle_delete(n_id)
                            ).classes("text-red-400 hover:text-red-600 flat round").props('dense')

    # کانتینر پویا
    content_container = ui.column().classes("w-full gap-4")
    
    # دکمه شناور Floating Action Button (FAB)
    ui.button(
        icon="add",
        on_click=lambda: open_note_modal()
    ).classes("fab-btn").props('round size="lg"')

    # اجرای لود اولیه کدهای جنگو
    await load_notes()

# ----------------- Profile Page -----------------

@ui.page('/profile')
@with_layout(current_tab='profile')
async def profile_page():
    api = get_api_client()

    state = {
        'phone': app.storage.user.get("phone") or "۰۹xxxxxxxxx",
        'tg_connected': False,
        'bale_connected': False,
        'tg_username': '',
        'bale_username': '',
        'tg_editing': False,
        'bale_editing': False,
        'loading': True
    }

    async def load_profile():
        state['loading'] = True
        try:
            status_code, data = await api.fetch_profile()
            if status_code == 200:
                state['phone'] = data.get("phone") or state['phone']
                state['tg_connected'] = data.get("is_telegram_bot_connected", False)
                state['bale_connected'] = data.get("is_bale_bot_connected", False)
                state['tg_username'] = data.get("telegram_bot_username") or ''
                state['bale_username'] = data.get("bale_bot_username") or ''
                
                # ذخیره لوکال
                app.storage.user['phone'] = state['phone']
            elif status_code == 401:
                logout_user()
                return
        except Exception:
            pass
        finally:
            state['loading'] = False
            render_profile()

    async def handle_save_bot(platform, token):
        if not token.strip():
            return
        ui.notify("در حال بررسی و اتصال ربات...", type="info")
        status_code, data = await api.update_custom_bot(platform, token.strip())
        if status_code == 200 and data.get("success"):
            ui.notify(data.get("message", "ربات اختصاصی با موفقیت متصل شد."), type="success")
            state[f"{platform}_editing"] = False
            await load_profile()
        else:
            ui.notify(data.get("error", "توکن نامعتبر است. مجددا تلاش کنید."), type="negative")

    async def handle_disconnect_bot(platform):
        with ui.dialog() as dialog, ui.card().classes("p-6 gap-4"):
            ui.label(f"آیا مطمئن هستید که می‌خواهید ربات اختصاصی {'تلگرام' if platform == 'telegram' else 'بله'} را قطع اتصال کنید؟").classes("text-sm font-bold text-gray-800")
            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("انصراف", on_click=dialog.close).classes("text-slate-400 flat")
                async def confirm_disconnect():
                    dialog.close()
                    status_code, data = await api.update_custom_bot(platform, '')
                    if status_code == 200 and data.get("success"):
                        ui.notify("ربات اختصاصی با موفقیت قطع اتصال شد.", type="success")
                        state[f"{platform}_editing"] = False
                        await load_profile()
                ui.button("قطع اتصال", on_click=confirm_disconnect).classes("bg-red-500 text-white rounded-xl")
        dialog.open()

    def render_platform_connect(platform):
        connected = state['tg_connected'] if platform == 'telegram' else state['bale_connected']
        username = state['tg_username'] if platform == 'telegram' else state['bale_username']
        platform_name = "تلگرام" if platform == 'telegram' else "بله"
        emoji = "✈️" if platform == 'telegram' else "💬"
        
        editing = state['tg_editing'] if platform == 'telegram' else state['bale_editing']

        # کانتینر کامپوننت PlatformConnect
        with ui.column().classes("w-full p-5 base-card gap-4 bg-white"):
            # سربرگ کارت
            with ui.row().classes("w-full justify-between items-center"):
                with ui.row().classes("items-center gap-2"):
                    ui.label(emoji).classes("text-2xl")
                    ui.label(f"ربات اختصاصی {platform_name}").classes("font-bold text-gray-800 text-base")
                
                # چیپس وضعیت (چیپس تلویند)
                if connected and not editing:
                    with ui.row().classes("px-3 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-semibold rounded-full items-center gap-1.5"):
                        ui.label("").classes("h-2 w-2 rounded-full bg-emerald-500 animate-pulse")
                        ui.label(username or "متصل")
                elif not connected or editing:
                    with ui.row().classes("px-3 py-1 bg-amber-50 text-amber-700 border border-amber-200 text-xs font-semibold rounded-full items-center gap-1.5"):
                        ui.label("").classes("h-2 w-2 rounded-full bg-amber-400")
                        ui.label("نامتصل" if not connected else "در حال ویرایش")

            # لاین راهنمایی
            if not connected or editing:
                ui.label(f"برای انتشار خودکار یادداشت‌ها، ابتدا در BotFather پیام‌رسان {platform_name} یک ربات اختصاصی بسازید و توکن API آن را در کادر زیر وارد کنید.").classes("text-sm text-gray-500 leading-relaxed")

                # فرم ورود توکن
                token_input = ui.input(
                    label="توکن API ربات اختصاصی:", 
                    placeholder="مثال: 123456:ABC-DEF1234ghIkl-zyx"
                ).classes("w-full base-input text-sm font-mono").props('outlined rounded')

                with ui.row().classes("w-full gap-2"):
                    ui.button(
                        "ثبت و اتصال ربات" if not editing else "ذخیره تغییرات",
                        on_click=lambda: handle_save_bot(platform, token_input.value)
                    ).classes("btn-primary py-2 flex-grow text-xs")
                    
                    if editing:
                        def cancel_edit():
                            state[f"{platform}_editing"] = False
                            render_profile()
                        ui.button("انصراف", on_click=cancel_edit).classes("btn-outline py-2 text-xs")
            
            else:
                # کارت متصل بودن ربات
                with ui.column().classes("w-full p-3 bg-gray-50 rounded-xl border border-gray-100 text-sm gap-1"):
                    with ui.row().classes("w-full justify-between items-center text-xs text-gray-400"):
                        ui.label("آدرس ربات شما:")
                        clean_user = username.replace("@", "") if username else ""
                        url = f"https://t.me/{clean_user}" if platform == 'telegram' else f"https://ble.ir/{clean_user}"
                        ui.button("باز کردن چت ربات ↗", on_click=lambda u=url: ui.navigate.to(u, new_tab=True)).classes("text-indigo-600 hover:underline font-semibold flat").props('dense')
                    ui.label(username).classes("font-mono text-gray-700 font-bold break-all text-center w-full py-1.5")

                with ui.row().classes("w-full gap-2"):
                    # دکمه ادیت توکن
                    def start_edit():
                        state[f"{platform}_editing"] = True
                        render_profile()

                    ui.button("🔧 ویرایش توکن", on_click=start_edit).classes("btn-outline py-2 flex-grow text-xs")
                    ui.button("🔌 قطع اتصال ربات", on_click=lambda: handle_disconnect_bot(platform)).classes("btn-danger py-2 flex-grow text-xs")

    def render_profile():
        profile_container.clear()
        with profile_container:
            # ۱. بخش هدر مشخصات کاربر (UserInfo.vue)
            with ui.row().classes("w-full p-5 bg-white rounded-2xl shadow-sm border border-gray-100 items-center gap-4"):
                ui.label("👤").classes("text-4xl")
                with ui.column().classes("gap-1"):
                    ui.label(state['phone']).classes("text-lg font-bold text-gray-800")
                    ui.label("کاربر فعال تفکر").classes("text-xs text-gray-400 font-medium")

            # ۲. اتصالات ربات‌های اختصاصی تلگرام و بله (PlatformConnect.vue)
            ui.label("تنظیمات ربات‌های انتشار اختصاصی شما").classes("text-xs font-bold text-gray-400 px-1 mt-2")
            
            render_platform_connect('telegram')
            render_platform_connect('bale')

            # ۳. دکمه خروج نهایی منطبق با ProfileView.vue
            ui.button("خروج از حساب", on_click=logout_user).classes("w-full btn-danger py-3 mt-6 text-sm")

    profile_container = ui.column().classes("w-full gap-6")
    
    # بارگذاری
    await load_profile()

# ----------------- Start Application -----------------

ui.run(
    title="Tafakor - تفکر",
    port=PORT,
    storage_secret="tafakor_super_secret_session_key_12345",
    reload=True
)
