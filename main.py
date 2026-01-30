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
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



# ==============================================================================

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



def get_2fa_code():
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
    print(">>> 🛡️ Đang kiểm tra các bước xác minh/lưu trình duyệt...", flush=True)
    try:
        check_xpaths = ["//span[contains(text(), 'Lưu')]", "//span[contains(text(), 'Tiếp tục')]", "//div[@role='button' and contains(., 'Lưu')]", "//div[@role='button' and contains(., 'Tiếp tục')]", "//button[@value='OK']"]
        for _ in range(3):
            for xp in check_xpaths:
                try:
                    btns = driver.find_elements(By.XPATH, xp)
                    for btn in btns:
                        if btn.is_displayed():
                            print(f"   🔨 Bấm nút cản đường: {btn.text}", flush=True)
                            driver.execute_script("arguments[0].click();", btn)
                            time.sleep(5) 
                            return 
                except: pass
            time.sleep(2)
    except Exception as e: print(f"   ! Lỗi xử lý sau login: {e}", flush=True)

def diet_popup(driver):
    try:
        popup_xpaths = ["//span[contains(text(), 'Lúc khác')]", "//span[contains(text(), 'Not now')]", "//span[contains(text(), 'Để sau')]", "//div[@aria-label='Đóng']", "//div[@aria-label='Close']"]
        for xp in popup_xpaths:
            btns = driver.find_elements(By.XPATH, xp)
            if len(btns) > 0:
                for btn in btns:
                    if btn.is_displayed():
                        driver.execute_script("arguments[0].click();", btn)
                        time.sleep(1)
    except: pass

def setup_driver():
    print(">>> 🛠️ Đang khởi tạo Driver (Profile: Việt Kiều Mỹ)...", flush=True)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=375,812")
    chrome_options.add_argument("--lang=vi-VN")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
    mobile_emulation = { "deviceMetrics": { "width": 375, "height": 812, "pixelRatio": 3.0 }, "userAgent": ua }
    chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    params = { "timezoneId": "Asia/Ho_Chi_Minh" }
    driver.execute_cdp_cmd("Emulation.setTimezoneOverride", params)
    return driver

# ==============================================================================
# 3. TƯƠNG TÁC DẠO (MODE: NGHIỆN FACEBOOK)
# ==============================================================================


# ==============================================================================
# 4. MAIN LOOP (SAFE MODE + FIX 2FA TIẾNG VIỆT)
# ==============================================================================
def main():
    print(">>> 🚀 BOT KHỞI ĐỘNG...", flush=True)
    email = os.environ["FB_EMAIL"]
    password = os.environ["FB_PASS"]
    GAS_API_URL = os.environ.get("GAS_API_URL")
    driver = setup_driver()
    wait = WebDriverWait(driver, 30)

    try:
        # --- LOGIN ---
        print(">>> 📱 Vào Facebook...", flush=True)
        driver.get("https://m.facebook.com/")
        print(">>> 🔐 Nhập User/Pass...", flush=True)
        try:
            time.sleep(5)
            gui_anh_tele(driver, f"📱 Vào Facebook...")
            driver.get("https://m.facebook.com/")
            time.sleep(2)
            gui_anh_tele(driver, f"📱 Vào Facebook lần 2...")
            try: email_box = wait.until(EC.presence_of_element_located((By.NAME, "email")))
            except: email_box = driver.find_element(By.CSS_SELECTOR, "input[type='email']")
            email_box.clear(); email_box.send_keys(email)
            pass_box = driver.find_element(By.NAME, "pass")
            pass_box.clear(); pass_box.send_keys(password)
        except Exception as e: gui_anh_tele(driver, f"❌ Lỗi điền form: {e}")

        print(">>> 🔎 Bấm nút Login...", flush=True)
        login_clicked = False
        login_xpaths = ["//span[contains(text(), 'Log in')]", "//span[contains(text(), 'Log In')]", "//span[contains(text(), 'Đăng nhập')]", "//button[@name='login']", "//div[@role='button' and (contains(., 'Log In') or contains(., 'Đăng nhập'))]", "//input[@value='Log In']", "//input[@type='submit']"]
        for xpath in login_xpaths:
            try:
                btn = driver.find_element(By.XPATH, xpath)
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                time.sleep(1)
                btn.click()
                login_clicked = True
                break
            except: continue
        if not login_clicked:
            try: driver.find_element(By.NAME, "pass").send_keys(Keys.ENTER)
            except: pass
        time.sleep(15)

        # --- 2FA LOGIC (ĐÃ FIX: THÊM TỪ KHÓA TIẾNG VIỆT) ---
        print(">>> 🕵️ Kiểm tra 2FA...", flush=True)
        try_btn = None
        # Kiểm tra nút "Try another way" hoặc "Thử cách khác"
        try_xpaths = ["//div[@role='button' and contains(., 'Try another way')]", "//div[@role='button' and contains(., 'Thử cách khác')]"]
        for xp in try_xpaths:
            try:
                if len(driver.find_elements(By.XPATH, xp)) > 0:
                    try_btn = driver.find_element(By.XPATH, xp); break
            except: continue
            
        if try_btn:
            try_btn.click(); time.sleep(3)
            # 🔥 FIX: Thêm "Ứng dụng xác thực" để bot hiểu tiếng Việt
            auth_app_xpaths = [
                "//div[@role='radio' and contains(@aria-label, 'Email')]", 
                "//div[contains(., 'Email')]",
                "//div[contains(., 'Email')]",
                "//span[contains(text(), 'Email')]"
            ]
            for axp in auth_app_xpaths:
                try: driver.find_element(By.XPATH, axp).click(); break
                except: continue
            time.sleep(2)
            continue_xpaths = ["//div[@role='button' and @aria-label='Continue']", "//div[@role='button' and @aria-label='Tiếp tục']"]
            for cxp in continue_xpaths:
                try: driver.find_element(By.XPATH, cxp).click(); break
                except: continue
            time.sleep(5)

        fa_input = None
        try:
            inputs = driver.find_elements(By.TAG_NAME, "input")
            for inp in inputs:
                if inp.get_attribute("type") in ["tel", "number"]: fa_input = inp; break
        except: pass
        if not fa_input:
            fa_xpaths = ["//input[@name='approvals_code']", "//input[@placeholder='Code']", "//input[@aria-label='Code']"]
            for xp in fa_xpaths:
                try: fa_input = driver.find_element(By.XPATH, xp); break
                except: continue

        if fa_input:
            otp = get_2fa_code()
            print(f">>> 🔥 Nhập OTP: {otp}", flush=True)
            gui_anh_tele(driver, f"🔥 Nhập OTP: {otp}")
            fa_input.click(); fa_input.send_keys(otp); time.sleep(2)
            submit_xpaths = ["//div[@role='button' and @aria-label='Continue']", "//div[@role='button' and @aria-label='Tiếp tục']", "//button[@type='submit']", "//button[@id='checkpointSubmitButton']"]
            for btn_xp in submit_xpaths:
                try: driver.find_element(By.XPATH, btn_xp).click(); break
                except: continue
            fa_input.send_keys(Keys.ENTER); time.sleep(10)
        
        xu_ly_sau_login(driver)
        gui_anh_tele(driver, "✅ LOGIN OK! Vào chế độ HUMAN SCROLL...")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
