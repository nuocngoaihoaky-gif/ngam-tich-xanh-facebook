import time
import random
import os
import sys
import requests
from datetime import datetime
import pytz
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==============================================================================
# CẤU HÌNH API
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
    try:
        element.click()
        return True
    except:
        try:
            driver.execute_script("arguments[0].click();", element)
            return True
        except:
            return False

def xu_ly_sau_login(driver):
    print(">>> 🛡️ Đang dọn dẹp popup...", flush=True)
    try:
        check_xpaths = [
            "//span[contains(text(), 'Save')]", "//div[@role='button' and contains(., 'Save')]",
            "//span[contains(text(), 'Continue')]", "//div[@role='button' and contains(., 'Continue')]",
            "//span[contains(text(), 'OK')]", "//div[@aria-label='Close']"
        ]
        for _ in range(3):
            for xp in check_xpaths:
                try:
                    btns = driver.find_elements(By.XPATH, xp)
                    for btn in btns:
                        if btn.is_displayed():
                            driver.execute_script("arguments[0].click();", btn)
                            time.sleep(2)
                except: pass
            time.sleep(1)
    except: pass

def setup_driver():
    print(">>> 🛠️ Đang khởi tạo Driver (FIX VERSION 144)...", flush=True)
    
    options = uc.ChromeOptions()
    # Anti-Detect + Headless
    options.add_argument("--headless=new") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=en-US")
    
    # Fake User Agent (Windows 10 Chrome)
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")

    # 🔥 FIX QUAN TRỌNG: ÉP PHIÊN BẢN 144 ĐỂ KHỚP VỚI MÁY CHỦ
    # version_main=144 sẽ bắt nó tải đúng bản 144 thay vì 145
    driver = uc.Chrome(options=options, version_main=144)
    
    return driver

# ==============================================================================
# MAIN LOOP
# ==============================================================================
def main():
    print(">>> 🚀 BOT KHỞI ĐỘNG (V42 - FIX VER 144)...", flush=True)
    email = os.environ.get("FB_EMAIL")
    password = os.environ.get("FB_PASS")
    
    if not email or not password: return

    try:
        driver = setup_driver()
    except Exception as e:
        print(f"❌ Lỗi khởi tạo Driver: {e}")
        return

    wait = WebDriverWait(driver, 40)

    try:
        # --- LOGIN ---
        print(">>> 💻 Vào Facebook (Desktop)...", flush=True)
        driver.get("https://www.facebook.com/login/?locale=en_US")
        time.sleep(5)

        # 0. Check CAPTCHA
        if "recaptcha" in driver.page_source.lower():
            gui_anh_tele(driver, "❌ DÍNH CAPTCHA NGAY ĐẦU (IP BAD)")
            return

        # 1. Nhập Email
        print(">>> 🔐 Nhập Email...", flush=True)
        try:
            email_box = wait.until(EC.presence_of_element_located((By.ID, "email")))
            email_box.clear(); email_box.send_keys(email)
            time.sleep(2)
            
            pass_box = driver.find_element(By.ID, "pass")
            pass_box.clear(); pass_box.send_keys(password)
            time.sleep(2)
            
            login_btn = driver.find_element(By.NAME, "login")
            force_click(driver, login_btn)
            
        except Exception as e:
            gui_anh_tele(driver, f"❌ Lỗi điền form: {e}")
            return

        time.sleep(10)

        # 2. CHECK 2FA
        print(">>> 🕵️ Kiểm tra trạng thái...", flush=True)
        
        is_2fa = False
        if "checkpoint" in driver.current_url or "two_step_verification" in driver.page_source:
            is_2fa = True
            print(">>> ⚠️ Phát hiện 2FA.", flush=True)
        
        if is_2fa:
            code_input = None
            # Vét cạn ô input
            for i in range(5):
                inputs = driver.find_elements(By.TAG_NAME, "input")
                for inp in inputs:
                    try:
                        if inp.is_displayed() and inp.get_attribute("type") in ["text", "number", "tel"]:
                            if "search" not in inp.get_attribute("name") and "email" not in inp.get_attribute("name"):
                                code_input = inp
                                break
                    except: pass
                if code_input: break
                time.sleep(2)
            
            if code_input:
                print(">>> ✅ Thấy ô 2FA.", flush=True)
                otp_code = get_code_from_email()
                if otp_code:
                    print(f">>> ✍️ Nhập mã: {otp_code}", flush=True)
                    code_input.send_keys(otp_code)
                    time.sleep(2)
                    code_input.send_keys(Keys.ENTER)
                    
                    try: # Tìm nút Continue
                        btns = driver.find_elements(By.XPATH, "//div[@role='button']//span[contains(text(), 'Continue')]")
                        if not btns: btns = driver.find_elements(By.XPATH, "//button[@type='submit']")
                        if btns: force_click(driver, btns[0])
                    except: pass
                    
                    time.sleep(10)
                else:
                    print(">>> ❌ Không có mã.", flush=True); return
            else:
                gui_anh_tele(driver, "⚠️ Không thấy ô nhập mã 2FA")

        # 3. HOÀN TẤT
        if len(driver.find_elements(By.ID, "email")) == 0:
            xu_ly_sau_login(driver)
            gui_anh_tele(driver, "✅ LOGIN THÀNH CÔNG! ĐANG NGÂM...")
            
            total_time = 21600 
            check_interval = 1800 
            loops = int(total_time / check_interval)
            
            for i in range(loops):
                print(f"   💤 Treo máy... (Chu kỳ {i+1}/{loops})", flush=True)
                time.sleep(check_interval)
                try: driver.get("https://www.facebook.com/login/?locale=en_US")
                except: pass
            print(">>> ✅ XONG.", flush=True)
        else:
            gui_anh_tele(driver, "❌ LOGIN FAILED (Vẫn ở Login Page)")

    except Exception as e:
        print(f"❌ Lỗi Fatal: {e}")
    finally:
        try: driver.quit()
        except: pass

if __name__ == "__main__":
    main()
