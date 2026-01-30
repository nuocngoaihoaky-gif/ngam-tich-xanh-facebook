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
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, NoSuchElementException

# ==============================================================================
# SECRETS CONFIG
# ==============================================================================
GAS_API_URL = os.environ.get("GAS_API_URL")

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

def force_click(driver, element):
    """Click bất chấp"""
    try:
        element.click()
        return True
    except:
        try:
            driver.execute_script("arguments[0].click();", element)
            return True
        except:
            try:
                actions = ActionChains(driver)
                actions.move_to_element(element).click().perform()
                return True
            except:
                return False

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
                            force_click(driver, btn)
                            time.sleep(5) 
                            return 
                except: pass
            time.sleep(2)
    except: pass

def setup_driver():
    print(">>> 🛠️ Đang khởi tạo Driver...", flush=True)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=375,812")
    chrome_options.add_argument("--lang=en-US")
    
    # Fake Hardware & WebRTC
    chrome_options.add_argument("--disable-webrtc")
    ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
    mobile_emulation = { "deviceMetrics": { "width": 375, "height": 812, "pixelRatio": 3.0 }, "userAgent": ua }
    chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = webdriver.Chrome(options=chrome_options)

    # Fake CPU/GPU/Timezone/GPS
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 6});
            Object.defineProperty(navigator, 'deviceMemory', {get: () => 4});
        """
    })
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
    
    if not email or not password: return

    driver = setup_driver()
    wait = WebDriverWait(driver, 40) # Timeout dài 40s

    try:
        # --- LOGIN ---
        print(">>> 📱 Vào Facebook...", flush=True)
        driver.get("https://m.facebook.com/?locale=en_US")
        
        # 1. Nhập Email
        print(">>> 🔐 Nhập Email...", flush=True)
        try:
            email_box = wait.until(EC.presence_of_element_located((By.NAME, "email")))
            email_box.clear(); email_box.send_keys(email)
        except Exception as e:
            gui_anh_tele(driver, f"❌ Lỗi tìm ô Email: {e}")
            return

        time.sleep(2)

        # 2. Xử lý nút Continue (VƯỢT QUA BƯỚC NÀY BẤT CHẤP)
        if len(driver.find_elements(By.NAME, "pass")) == 0:
            print("   Login 2 bước: Đang xử lý nút Continue...", flush=True)
            
            targets = [
                "//div[@role='button' and @aria-label='Continue']",
                "//div[contains(text(), 'Continue')]",
                "//button[contains(text(), 'Continue')]"
            ]
            
            for xp in targets:
                try:
                    elms = driver.find_elements(By.XPATH, xp)
                    for elm in elms:
                        if elm.is_displayed():
                            print(f"   👉 Bấm nút: {xp}", flush=True)
                            force_click(driver, elm)
                            time.sleep(1) 
                except: pass
            
            try:
                print("   👉 Bồi thêm phím ENTER...", flush=True)
                email_box.send_keys(Keys.ENTER)
            except: pass

            time.sleep(5)

        # 3. NHẬP PASSWORD & BẤM LOG IN (FIX BUTTON)
        print(">>> 🔐 Đang đợi ô Password hiện hình...", flush=True)
        try:
            pass_box = None
            try: pass_box = wait.until(EC.visibility_of_element_located((By.NAME, "pass")))
            except: 
                try: pass_box = driver.find_element(By.XPATH, "//input[@type='password']")
                except: pass

            if pass_box:
                print("   ✅ Đã thấy ô Pass! Nhập mật khẩu ngay...", flush=True)
                pass_box.click() 
                pass_box.send_keys(password)
                time.sleep(1)

                # --- CHIẾN THUẬT VÉT CẠN NÚT LOG IN ---
                print("   👉 Đang tìm nút Log in để bấm...", flush=True)
                login_targets = [
                    "//div[@role='button' and @aria-label='Log in']", # Div Button
                    "//div[contains(text(), 'Log in')]",             # Div Text
                    "//span[contains(text(), 'Log in')]",            # Span Text
                    "//button[@name='login']",                       # Standard Button
                    "//button[contains(text(), 'Log in')]"           # Button Text
                ]
                
                clicked_login = False
                for xp in login_targets:
                    try:
                        btns = driver.find_elements(By.XPATH, xp)
                        for btn in btns:
                            if btn.is_displayed():
                                print(f"   👉 Bấm thử nút Login: {xp}", flush=True)
                                force_click(driver, btn)
                                clicked_login = True
                                time.sleep(1)
                    except: pass
                
                # Bồi thêm cú Enter ở ô Password (Mạnh nhất)
                if not clicked_login:
                    print("   👉 Không thấy nút, BẤM ENTER TẠI Ô PASS...", flush=True)
                    pass_box.send_keys(Keys.ENTER)
                else:
                    # Kể cả bấm rồi cũng bồi thêm phát Enter cho chắc cốp
                    try: pass_box.send_keys(Keys.ENTER)
                    except: pass

            else:
                print("   ❌ Không tìm thấy ô nhập Password!", flush=True)
                gui_anh_tele(driver, "❌ Mất tích ô Password")
                return
            
        except Exception as e:
            gui_anh_tele(driver, f"❌ Lỗi đoạn nhập Pass: {e}")
            return

        time.sleep(10)

        # --- XỬ LÝ 2FA ---
        print(">>> 🕵️ Kiểm tra 2FA...", flush=True)
        
        # Click "Try another way"
        try:
            try_btn = driver.find_elements(By.XPATH, "//span[contains(text(), 'Try another way')]") or driver.find_elements(By.XPATH, "//div[contains(., 'Try another way')]")
            if try_btn and try_btn[0].is_displayed():
                force_click(driver, try_btn[0])
                time.sleep(5)
        except: pass

        # Chọn Email
        try:
            email_opts = driver.find_elements(By.XPATH, "//span[contains(text(), 'Email')]") or driver.find_elements(By.XPATH, "//div[contains(., 'Email')]")
            if email_opts and email_opts[0].is_displayed():
                print("   + Chọn Email...", flush=True)
                force_click(driver, email_opts[0])
                time.sleep(2)
                
                # Bấm Continue 2FA
                c_xpaths = ["//div[@role='button' and @aria-label='Continue']", "//span[contains(text(), 'Continue')]"]
                for cxp in c_xpaths:
                    c_btns = driver.find_elements(By.XPATH, cxp)
                    if c_btns and c_btns[0].is_displayed():
                        force_click(driver, c_btns[0])
                        time.sleep(10)
                        break
        except: pass

        # Nhập Code
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
                    s_btns = driver.find_elements(By.XPATH, "//span[contains(text(), 'Continue')]") or driver.find_elements(By.XPATH, "//button[@type='submit']")
                    if s_btns: force_click(driver, s_btns[0])
                except: pass
                time.sleep(10)
            else:
                print(">>> ❌ Không có mã. Tắt Bot.", flush=True)
                return

        # --- HOÀN TẤT & NGÂM ---
        xu_ly_sau_login(driver)
        gui_anh_tele(driver, "✅ LOGIN THÀNH CÔNG! BẮT ĐẦU NGÂM 6H...")

        # NGÂM 6 TIẾNG
        total_time = 21600 
        check_interval = 1800 
        loops = int(total_time / check_interval)
        
        for i in range(loops):
            print(f"   💤 Treo máy... (Chu kỳ {i+1}/{loops})", flush=True)
            time.sleep(check_interval)
            try:
                driver.get("https://m.facebook.com/?locale=en_US")
                time.sleep(10)
            except: pass

        print(">>> ✅ XONG 6 TIẾNG.", flush=True)

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
