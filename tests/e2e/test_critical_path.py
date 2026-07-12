import time
import pytest
from django.core.cache import cache
from playwright.sync_api import Page, expect

@pytest.mark.django_db(transaction=True)
def test_critical_path_login_flow(page: Page, frontend_url: str):
    """
    E2E test that validates the user registration/login flow on the Vue frontend.
    Bypasses OTP verification by reading the generated code directly from
    the database-backed cache table.
    """
    
    # 1. Open Vue frontend login page.
    login_url = f"{frontend_url.rstrip('/')}/login"
    print(f"\n[E2E] Navigating to: {login_url}")
    page.goto(login_url)
    
    # Wait for page to load
    page.wait_for_url("**/login")
    assert "/login" in page.url
    print(f"[E2E] Arrived at login page: {page.url}")

    # Close Changelog modal if it appears
    try:
        page.locator('button:has-text("متوجه شدم")').click(timeout=3000)
        print("[E2E] Closed Changelog modal")
    except Exception:
        print("[E2E] Changelog modal was not shown or already closed")

    # 2. Fill the phone form
    phone_number = "09123456789"
    phone_input = page.locator('input[type="tel"]')
    expect(phone_input).to_be_visible(timeout=5000)
    
    phone_input.fill(phone_number)
    print(f"[E2E] Entered phone number: {phone_number}")

    # Submit the phone number to trigger OTP generation
    submit_button = page.locator('button[type="submit"]')
    submit_button.click()
    print("[E2E] Clicked 'Send OTP' button")

    # 3. Retrieve the generated OTP from the shared PostgreSQL database cache
    print("[E2E] Waiting for OTP to be generated and saved to database cache...")
    otp_code = None
    
    # Poll cache for up to 3 seconds (30 iterations of 100ms)
    for _ in range(30):
        otp_code = cache.get(f"otp_{phone_number}")
        if otp_code:
            break
        time.sleep(0.1)

    assert otp_code is not None, f"OTP for {phone_number} was not found in the shared cache database!"
    print(f"[E2E] Retrieved OTP from shared cache: {otp_code}")

    # 4. Enter the 4-digit OTP code into the digit inputs
    # Wait for the OTP digit input to render on the page
    otp_input = page.locator('input[inputmode="numeric"]')
    expect(otp_input).to_be_visible(timeout=5000)
    
    # Fill the OTP input
    otp_input.fill(str(otp_code))
    print(f"[E2E] Entered OTP code: {otp_code}")

    # OTP is submitted automatically when 4 digits are filled. No need to click submit button manually.


    # 5. Verify successful authentication and redirection to the root route
    print("[E2E] Waiting for redirect back to Home page...")
    # On login, the page sets localStorage token and does window.location.href = '/'
    # So we wait for the URL to change to the root path
    expected_url = frontend_url.replace(":80", "").rstrip('/')
    page.wait_for_url(f"{expected_url}/")
    
    # Assert final URL is the root home view
    assert page.url.rstrip('/') == expected_url
    print(f"[E2E] Login successful! Current browser URL is: {page.url}")

    # 6. Click the FAB (+) button to open the Topic creation modal
    fab_button = page.locator('button.fixed.bottom-24.right-6')
    expect(fab_button).to_be_visible(timeout=5000)
    fab_button.click()
    print("[E2E] Clicked FAB (+) button")

    # 7. Fill out Topic Name and Short Description
    topic_name = "موضوع تستی E2E"
    topic_desc = "این یک موضوع تستی ایجاد شده توسط تست E2E Playwright است."
    
    name_input = page.locator('input#topic-title')
    expect(name_input).to_be_visible(timeout=5000)
    name_input.fill(topic_name)
    print(f"[E2E] Filled topic name: {topic_name}")
    
    desc_input = page.locator('input#topic-desc')
    expect(desc_input).to_be_visible(timeout=5000)
    desc_input.fill(topic_desc)
    print(f"[E2E] Filled topic description: {topic_desc}")
    
    # Click "ایجاد تاپیک" to submit the form
    submit_topic_button = page.locator('button:has-text("ایجاد تاپیک")')
    submit_topic_button.click()
    print("[E2E] Clicked 'ایجاد تاپیک' submit button")

    # 8. Click the newly created Topic card and wait for navigation
    topic_card = page.locator(f'span:has-text("{topic_name}")').first
    expect(topic_card).to_be_visible(timeout=5000)
    topic_card.click()
    print(f"[E2E] Clicked topic card: {topic_name}")
    
    # Wait for navigation to the Topic detail view
    page.wait_for_url("**/topic/*")
    assert "/topic/" in page.url
    print(f"[E2E] Navigated to topic detail page: {page.url}")

    # 9. Type a post and submit it
    post_text = "این اولین پست تستی من در این تاپیک است! #تفکر"
    post_input = page.locator('textarea[placeholder="یادداشت خود را بنویسید..."]')
    expect(post_input).to_be_visible(timeout=5000)
    post_input.fill(post_text)
    print(f"[E2E] Filled post content: {post_text}")
    
    # Click the send button
    send_button = page.locator('button[title="ارسال پیام"]')
    send_button.click()
    print("[E2E] Clicked send post button")

    # 10. Open comments drawer, type a comment, click send, and assert comment count updates
    comment_button = page.locator('button:has(svg.lucide-message-circle)').first
    expect(comment_button).to_be_visible(timeout=5000)
    
    # Let's get initial comment count (should be ۰)
    initial_text = comment_button.text_content()
    assert "۰" in initial_text
    print(f"[E2E] Initial comment button text: {initial_text}")
    
    # Open comments drawer
    comment_button.click()
    print("[E2E] Clicked comment button to open drawer")
    
    # Type a comment
    comment_input = page.locator('input[placeholder="دیدگاه خود را بنویسید..."]')
    expect(comment_input).to_be_visible(timeout=5000)
    comment_text = "این یک نظر تستی است."
    comment_input.fill(comment_text)
    print(f"[E2E] Filled comment text: {comment_text}")
    
    # Click comments submit button (inside comments input container)
    comment_submit = page.locator('div:has(> input[placeholder="دیدگاه خود را بنویسید..."]) > button')
    comment_submit.click()
    print("[E2E] Clicked comment send button")
    
    # Wait for comment count to update to "۱"
    expect(comment_button).to_contain_text("۱", timeout=5000)
    print(f"[E2E] Verified comment count updated: {comment_button.text_content()}")

    # 12. Delete the post by opening the context menu and clicking delete
    page.locator('button.size-7').first.click()
    print("[E2E] Opened context menu for deletion")
    
    delete_option = page.locator('button:has-text("حذف پست")').first
    expect(delete_option).to_be_visible(timeout=5000)
    
    delete_option.click()
    print("[E2E] Clicked delete post option to open confirm modal")
    
    # Click the confirm button in the custom confirm modal
    confirm_button = page.locator('button:has-text("تایید و حذف")')
    expect(confirm_button).to_be_visible(timeout=5000)
    confirm_button.click()
    print("[E2E] Clicked 'تایید و حذف' in custom confirm modal")
    
    # Wait for the post to disappear
    expect(page.locator(f'p:has-text("{post_text}")')).not_to_be_visible(timeout=5000)
    print("[E2E] Verified post was successfully deleted!")


@pytest.mark.django_db(transaction=True)
def test_custom_bot_registration(page: Page, frontend_url: str):
    """
    E2E test that verifies the custom bot registration workflow in the user's profile connections tab.
    """
    # 1. Login
    login_url = f"{frontend_url.rstrip('/')}/login"
    print(f"\n[E2E] Navigating to login for custom bot test: {login_url}")
    page.goto(login_url)
    page.wait_for_url("**/login")

    # Close Changelog modal if it appears
    try:
        page.locator('button:has-text("متوجه شدم")').click(timeout=2000)
    except Exception:
        pass

    phone_number = "09999999999"
    phone_input = page.locator('input[type="tel"]')
    expect(phone_input).to_be_visible(timeout=5000)
    phone_input.fill(phone_number)
    
    submit_button = page.locator('button[type="submit"]')
    submit_button.click()

    # Retrieve OTP
    otp_code = None
    for _ in range(30):
        otp_code = cache.get(f"otp_{phone_number}")
        if otp_code:
            break
        time.sleep(0.1)

    assert otp_code is not None, "OTP not found"
    
    otp_input = page.locator('input[inputmode="numeric"]')
    expect(otp_input).to_be_visible(timeout=5000)
    otp_input.fill(str(otp_code))
    
    # OTP is submitted automatically when 4 digits are filled. No need to click submit button manually.


    expected_url = frontend_url.replace(":80", "").rstrip('/')
    page.wait_for_url(f"{expected_url}/")
    print("[E2E] Login successful, navigated to home.")

    # 2. Go to Profile Page
    profile_url = f"{expected_url}/profile"
    print(f"[E2E] Navigating to: {profile_url}")
    page.goto(profile_url)
    page.wait_for_url("**/profile")

    # 3. Switch to 'اتصالات' Option
    connections_tab = page.locator('button:has-text("اتصالات")').first
    expect(connections_tab).to_be_visible(timeout=5000)
    connections_tab.click()
    print("[E2E] Clicked on connections tab.")

    # 4. Fill in mock Telegram bot token
    token_input = page.locator('input#bot-token-input').first
    expect(token_input).to_be_visible(timeout=5000)
    mock_token = "mock_token_for_e2e_test"
    token_input.fill(mock_token)
    print(f"[E2E] Entered mock token: {mock_token}")

    # 5. Click "ذخیره و اتصال"
    submit_bot_btn = page.locator('button:has-text("ذخیره و اتصال")').first
    expect(submit_bot_btn).to_be_visible(timeout=5000)
    submit_bot_btn.click()
    print("[E2E] Clicked 'ذخیره و اتصال' button.")


    # 6. Verify that it connects successfully and shows the bot username badge
    expected_username = f"@{mock_token}_bot"
    username_display = page.locator(f'span:has-text("{expected_username}")').first
    expect(username_display).to_be_visible(timeout=10000)
    print(f"[E2E] Successfully registered custom bot and verified username display: {expected_username}")
