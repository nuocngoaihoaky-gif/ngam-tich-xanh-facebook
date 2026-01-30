import time
import random
import os
import sys
import requests
from datetime import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==============================================================================
# SECRETS CONFIG
# ==============================================================================
GAS_API_URL = os.environ.get("GAS_API_URL") # Link App Script

# ==============================================================================
# CÁC HÀM HỖ TRỢ
# ==============================================================================

def gui_anh_tele(driver, caption="Ảnh chụp màn hình"):
    try:
        token = os.environ.get("TELEGRAM_TOKEN")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        if not token or not chat_id: return
        filename = "temp_screenshot.png"
        driver.save_screenshot(filename)
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        with open(filename, 'rb') as photo:
            requests.post(url, files={'photo': photo}, data={'chat_id': chat_id, 'caption': caption})
    except: pass

def get_code_from_email():
    if not GAS_API_URL:
        print(">>> ❌ CHƯA CÓ LINK API GOOGLE APPS SCRIPT!", flush=True)
        return None
        
    print(">>> 📧 Đang gọi API lấy mã từ Gmail...", flush=True)
    for i in range(6):
        try:
            response = requests.get(GAS_API_URL)
            code = response.text.strip()
            if code and code != "NO_CODE":
                print(f"   + ✅ Đã tìm thấy mã: {code}", flush=True)
                return code
            else:
                print(f"   - ⏳ Chưa có mail mới... ({i+1}/6)", flush=True)
                time.sleep(10)
        except Exception as e:
            print(f"   ! Lỗi gọi API: {e}")
            time.sleep(5)
    return None

def xu_ly_sau_login(driver):
    print(">>> 🛡️ Đang kiểm tra nút 'Save Browser'...", flush=True)
    try:
        check_xpaths = [
            "//span[contains(text(), 'Save')]", "//div[@role='button' and contains(., 'Save')]",
            "//span[contains(text(), 'Continue')]", "//div[@role='button' and contains(., 'Continue')]",
            "//span[contains(text(), 'OK')]"
        ]
        for _ in range(3):
            for xp in check_xpaths:
                try:
                    btns = driver.find_elements(By.XPATH, xp)
                    for btn in btns:
                        if btn.is_displayed():
                            print(f"   🔨 Bấm nút: {btn.text}", flush=True)
                            driver.execute_script("arguments[0].click();", btn)
                            time.sleep(5) 
                            return 
                except: pass
            time.sleep(2)
    except: pass

def setup_driver():
    print(">>> 🛠️ Đang khởi tạo Driver (Profile: Full US + Fake Hardware)...", flush=True)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=375,812")
    chrome_options.add_argument("--lang=en-US")
    
    # 🔥 1. Tắt WebRTC để tránh rò rỉ IP thật
    chrome_options.add_argument("--disable-webrtc")
    chrome_options.add_argument("--disable-webrtc-multiple-routes")

    # 🔥 2. Ngụy trang User Agent (iPhone 14 Pro Max)
    ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
    mobile_emulation = { 
        "deviceMetrics": { "width": 375, "height": 812, "pixelRatio": 3.0, "touch": True }, 
        "userAgent": ua 
    }
    chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
    
    # Chống bot detect
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = webdriver.Chrome(options=chrome_options)

    # 🔥 3. Fake Hardware (CPU/RAM) để giống điện thoại thật
    # iPhone thường có 6 nhân CPU và 4-6GB RAM. Server thường có nhiều nhân hơn -> Phải fake lại.
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 6});
            Object.defineProperty(navigator, 'deviceMemory', {get: () => 4});
            Object.defineProperty(navigator, 'platform', {get: () => 'iPhone'});
            
            // Fake GPU (Card đồ họa) để che giấu "Google SwiftShader"
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) { return 'Apple Inc.'; } // UNMASKED_VENDOR_WEBGL
                if (parameter === 37446) { return 'Apple GPU'; } // UNMASKED_RENDERER_WEBGL
                return getParameter(parameter);
            };
        """
    })
    
    # 4. Set Timezone & GPS New York
    driver.execute_cdp_cmd("Emulation.setTimezoneOverride", { "timezoneId": "America/New_York" })
    driver.execute_cdp_cmd("Emulation.setGeolocationOverride", { "latitude": 40.7128, "longitude": -74.0060, "accuracy": 100 })
    
    return driver

# ==============================================================================
# MAIN LOOP
# ==============================================================================
def main():
    print(">>> 🚀 BOT KHỞI ĐỘNG...", flush=True)
    
    email = os.environ.get("FB_EMAIL")
    password = os.environ.get("FB_PASS")
    
    if not email or not password:
        print(">>> ❌ LỖI: Thiếu Secret FB_EMAIL hoặc FB_PASS!", flush=True)
        return

    driver = setup_driver()
    wait = WebDriverWait(driver, 30)

    try:
        # --- LOGIN ---
        print(">>> 📱 Vào Facebook (US Locale)...", flush=True)
        driver.get("https://m.facebook.com/?locale=en_US")
        
        print(">>> 🔐 Nhập User/Pass...", flush=True)
        try:
            try: email_box = wait.until(EC.presence_of_element_located((By.NAME, "email")))
            except: email_box = driver.find_element(By.CSS_SELECTOR, "input[type='email']")
            email_box.clear(); email_box.send_keys(email)
            pass_box = driver.find_element(By.NAME, "pass")
            pass_box.clear(); pass_box.send_keys(password)
            
            login_btn = driver.find_element(By.NAME, "login")
            driver.execute_script("arguments[0].click();", login_btn)
        except Exception as e: gui_anh_tele(driver, f"❌ Lỗi login: {e}")
        time.sleep(10)

        # --- XỬ LÝ 2FA ---
        print(">>> 🕵️ Kiểm tra 2FA (Email)...", flush=True)
        
        # 1. Bấm "Try another way"
        try:
            try_btn = driver.find_elements(By.XPATH, "//span[contains(text(), 'Try another way')]")
            if not try_btn: try_btn = driver.find_elements(By.XPATH, "//div[contains(., 'Try another way')]")
            if try_btn and try_btn[0].is_displayed():
                driver.execute_script("arguments[0].click();", try_btn[0])
                time.sleep(5)
        except: pass

        # 2. Chọn Email
        try:
            email_option = driver.find_elements(By.XPATH, "//span[contains(text(), 'Email')]")
            if not email_option: email_option = driver.find_elements(By.XPATH, "//div[contains(., 'Email')]")
            if email_option and email_option[0].is_displayed():
                print("   + 📧 Chọn Email...", flush=True)
                driver.execute_script("arguments[0].click();", email_option[0])
                time.sleep(2)
                
                cont_btn = driver.find_elements(By.XPATH, "//span[contains(text(), 'Continue')]")
                if not cont_btn: cont_btn = driver.find_elements(By.XPATH, "//div[@role='button' and contains(., 'Continue')]")
                if cont_btn: driver.execute_script("arguments[0].click();", cont_btn[0]); time.sleep(10)
        except: pass

        # 3. Nhập mã
        code_input = None
        try:
            inps = driver.find_elements(By.XPATH, "//input[@type='number' or @type='tel' or @name='approvals_code']")
            if inps: code_input = inps[0]
        except: pass

        if code_input:
            print(">>> ❗ Đang lấy mã từ Email...", flush=True)
            otp_code = get_code_from_email()
            
            if otp_code:
                print(f">>> ✍️ Nhập mã: {otp_code}", flush=True)
                code_input.send_keys(otp_code)
                time.sleep(2)
                code_input.send_keys(Keys.ENTER)
                try:
                    s_btn = driver.find_elements(By.XPATH, "//span[contains(text(), 'Continue')]")
                    if not s_btn: s_btn = driver.find_elements(By.XPATH, "//button[@type='submit']")
                    if s_btn: driver.execute_script("arguments[0].click();", s_btn[0])
                except: pass
                time.sleep(10)
            else:
                print(">>> ❌ Không có mã. Tắt Bot.", flush=True)
                return

        xu_ly_sau_login(driver)
        gui_anh_tele(driver, "✅ LOGIN US OK! ĐANG NGÂM (6H)...")

        # NGÂM 6 TIẾNG (Không tương tác)
        total_time = 21600 
        check_interval = 1800 
        loops = int(total_time / check_interval)
        
        for i in range(loops):
            print(f"   💤 Treo máy... (Chu kỳ {i+1}/{loops})", flush=True)
            time.sleep(check_interval)
            try:
                driver.get("https://m.facebook.com/?locale=en_US") # Refresh giữ kết nối
                time.sleep(10)
            except: pass

        print(">>> ✅ XONG 6 TIẾNG.", flush=True)

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
