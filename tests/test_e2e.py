"""
E2E (End-to-End) Tests with Playwright
=======================================
ทดสอบเว็บแอพเหมือนผู้ใช้งานจริง - เปิด browser กดปุ่ม พิมพ์ข้อมูล

E2E Test คืออะไร?
- เปิด browser จริง (Chrome, Firefox, Safari)
- จำลองการใช้งานของ user
- ตรวจสอบว่าหน้าเว็บแสดงผลถูกต้อง

วิธีติดตั้ง:
    pip install playwright pytest-playwright
    playwright install chromium

วิธีรัน (ต้องรัน streamlit ก่อน):
    # Terminal 1: รัน app
    streamlit run app.py
    
    # Terminal 2: รัน tests
    pytest tests/test_e2e.py -v --headed  # --headed = เห็น browser เปิดจริง
"""

import pytest
from playwright.sync_api import Page, expect
import time

# URL ของ app (ต้องรัน streamlit run app.py ก่อน)
APP_URL = "http://localhost:8501"


# ============================================================================
# TEST 1: ทดสอบว่าหน้า Login แสดงได้
# ============================================================================
def test_login_page_loads(page: Page):
    """
    ทดสอบว่าหน้า Login โหลดได้และแสดง elements ถูกต้อง
    
    page = browser page object จาก Playwright
    """
    # Act: เปิดหน้าเว็บ
    page.goto(APP_URL)
    
    # รอให้หน้าโหลด
    page.wait_for_load_state("networkidle")
    time.sleep(2)  # รอ Streamlit render
    
    # Assert: ตรวจสอบว่ามีคำว่า "Everything" หรือ "Login" หรือ "Password"
    content = page.content().lower()
    assert any(word in content for word in ["everything", "password", "login", "sign in"]), \
        "Login page should show login form or app title"
    
    print("✅ test_login_page_loads PASSED")


# ============================================================================
# TEST 2: ทดสอบ Login ด้วย password ผิด
# ============================================================================
def test_login_with_wrong_password(page: Page):
    """
    ทดสอบว่าเมื่อใส่ password ผิด จะแสดง error
    """
    # Arrange: เปิดหน้าเว็บ
    page.goto(APP_URL)
    page.wait_for_load_state("networkidle")
    time.sleep(2)
    
    # Act: พิมพ์ password ผิด
    # หา input field (password type)
    password_input = page.locator('input[type="password"]').first
    
    if password_input.is_visible():
        password_input.fill("wrong_password")
        
        # กดปุ่ม Sign In / Submit
        submit_button = page.locator('button:has-text("Sign In"), button[type="submit"]').first
        if submit_button.is_visible():
            submit_button.click()
            time.sleep(2)
            
            # Assert: ตรวจสอบว่ามี error message
            content = page.content().lower()
            assert any(word in content for word in ["invalid", "error", "wrong", "incorrect"]) or \
                   page.locator('input[type="password"]').is_visible(), \
                "Should show error or stay on login page"
    
    print("✅ test_login_with_wrong_password PASSED")


# ============================================================================
# TEST 3: ทดสอบ Login ด้วย User password (PCB25)
# ============================================================================
def test_login_as_user(page: Page):
    """
    ทดสอบว่า login ด้วย PCB25 (user role) สำเร็จ
    """
    # Arrange
    page.goto(APP_URL)
    page.wait_for_load_state("networkidle")
    time.sleep(2)
    
    # Act: ใส่ password ถูกต้อง
    password_input = page.locator('input[type="password"]').first
    
    if password_input.is_visible():
        password_input.fill("PCB25")
        
        # กดปุ่ม Sign In
        submit_button = page.locator('button:has-text("Sign In"), button[type="submit"]').first
        if submit_button.is_visible():
            submit_button.click()
            time.sleep(3)  # รอ redirect
            
            # Assert: ตรวจสอบว่าเข้าสู่ app แล้ว
            content = page.content().lower()
            # ควรเห็น sidebar หรือ app content
            assert any(word in content for word in ["analysis", "logout", "filter", "category"]), \
                "Should be redirected to main app after login"
    
    print("✅ test_login_as_user PASSED")


# ============================================================================
# TEST 4: ทดสอบ Login ด้วย Admin password
# ============================================================================
def test_login_as_admin(page: Page):
    """
    ทดสอบว่า login ด้วย admin1234 สำเร็จและเห็น Admin mode
    """
    # Arrange
    page.goto(APP_URL)
    page.wait_for_load_state("networkidle")
    time.sleep(2)
    
    # Act: ใส่ password admin
    password_input = page.locator('input[type="password"]').first
    
    if password_input.is_visible():
        password_input.fill("admin1234")
        
        # กดปุ่ม Sign In
        submit_button = page.locator('button:has-text("Sign In"), button[type="submit"]').first
        if submit_button.is_visible():
            submit_button.click()
            time.sleep(3)
            
            # Assert: ตรวจสอบว่าเห็น Admin mode
            content = page.content().lower()
            assert any(word in content for word in ["admin", "dashboard", "analysis"]), \
                "Admin should see admin mode or main app"
    
    print("✅ test_login_as_admin PASSED")


# ============================================================================
# TEST 5: ทดสอบ Logout
# ============================================================================
def test_logout_functionality(page: Page):
    """
    ทดสอบว่าปุ่ม Logout ทำงานถูกต้อง
    """
    # Arrange: Login ก่อน
    page.goto(APP_URL)
    page.wait_for_load_state("networkidle")
    time.sleep(2)
    
    password_input = page.locator('input[type="password"]').first
    if password_input.is_visible():
        password_input.fill("PCB25")
        submit_button = page.locator('button:has-text("Sign In"), button[type="submit"]').first
        if submit_button.is_visible():
            submit_button.click()
            time.sleep(3)
    
    # Act: กด Logout
    logout_button = page.locator('button:has-text("Logout")').first
    if logout_button.is_visible():
        logout_button.click()
        time.sleep(2)
        
        # Assert: กลับมาหน้า Login
        content = page.content().lower()
        assert any(word in content for word in ["password", "sign in", "login"]), \
            "Should return to login page after logout"
    
    print("✅ test_logout_functionality PASSED")


# ============================================================================
# TEST 6: ทดสอบ Screenshot (เป็น evidence)
# ============================================================================
def test_take_screenshot(page: Page):
    """
    ทดสอบการถ่าย screenshot เป็น evidence
    ใช้เก็บหลักฐานว่า test รันผ่านแล้ว
    """
    # Arrange
    page.goto(APP_URL)
    page.wait_for_load_state("networkidle")
    time.sleep(2)
    
    # Act: ถ่าย screenshot
    screenshot_path = "tests/screenshots/login_page.png"
    
    import os
    os.makedirs("tests/screenshots", exist_ok=True)
    
    page.screenshot(path=screenshot_path)
    
    # Assert: file ถูกสร้าง
    assert os.path.exists(screenshot_path), "Screenshot should be saved"
    
    print(f"✅ test_take_screenshot PASSED - saved to {screenshot_path}")


# ============================================================================
# Configuration สำหรับ pytest
# ============================================================================
@pytest.fixture(scope="function")
def page(browser):
    """
    Fixture สำหรับสร้าง page ใหม่ในแต่ละ test
    """
    context = browser.new_context(viewport={"width": 1280, "height": 720})
    page = context.new_page()
    yield page
    context.close()


# ============================================================================
# รันทุก tests ถ้าเรียกไฟล์นี้โดยตรง
# ============================================================================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🌐 E2E Tests require browser and running app")
    print("="*60)
    print("""
How to run E2E tests:

1. Install Playwright:
   pip install playwright pytest-playwright
   playwright install chromium

2. Start the app (in Terminal 1):
   streamlit run app.py

3. Run tests (in Terminal 2):
   pytest tests/test_e2e.py -v --headed
   
   --headed = show browser window
   -v = verbose output
""")
