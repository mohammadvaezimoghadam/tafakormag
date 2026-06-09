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
    
    # 1. Open Vue frontend. Unauthenticated users should be redirected to /login
    print(f"\n[E2E] Navigating to: {frontend_url}")
    page.goto(frontend_url)
    
    # Wait for redirection to complete
    page.wait_for_url("**/login")
    assert "/login" in page.url
    print(f"[E2E] Redirected to login page: {page.url}")

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
    # Wait for the OTP digit inputs to render on the page
    otp_inputs = page.locator('input[inputmode="numeric"]')
    expect(otp_inputs.first).to_be_visible(timeout=5000)
    
    # Confirm there are 4 inputs
    assert otp_inputs.count() == 4, f"Expected 4 OTP input boxes, found {otp_inputs.count()}"

    # Fill each digit input
    for i, digit in enumerate(str(otp_code)):
        otp_inputs.nth(i).fill(digit)
        print(f"[E2E] Entered digit {i+1}: {digit}")

    # The frontend submits automatically when the last digit is filled, 
    # but we can also click the login button to be double safe.
    login_button = page.locator('button[type="submit"]')
    if login_button.is_enabled():
        login_button.click()
        print("[E2E] Clicked 'Login' submit button manually")

    # 5. Verify successful authentication and redirection to the root route
    print("[E2E] Waiting for redirect back to Home page...")
    # On login, the page sets localStorage token and does window.location.href = '/'
    # So we wait for the URL to change to the root path
    page.wait_for_url(f"{frontend_url}/")
    
    # Assert final URL is the root home view
    assert page.url == f"{frontend_url}/" or page.url == f"{frontend_url}"
    print(f"[E2E] Login successful! Current browser URL is: {page.url}")
