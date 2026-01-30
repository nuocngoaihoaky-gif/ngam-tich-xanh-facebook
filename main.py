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
from selenium.webdriver.common.action_chains import ActionChains
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
            "//span[contains(text(), 'OK')]", "//div[@aria-label='Close']", "//span[contains(text(), 'Lúc khác')]"
        ]
        for _ in range(3):
            for xp in check_xpaths:
                try:
                    btns = driver.find_elements(By.XPATH, xp)
                    for btn in btns:
                        if btn.is_displayed():
                            force_click(driver, btn)
                            time.sleep(2)
                except: pass
            time.sleep(1)
    except: pass

def handle_captcha_aggressive(driver):
    """
    Hàm xử lý CAPTCHA V50: Vét cạn Iframe tìm nút Checkbox
    """
    print(">>> 🛡️ Đang rà soát CAPTCHA...", flush=True)
    time.sleep(5) # Chờ iframe load

    try:
        frames = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"   + Tìm thấy {len(frames)} Iframe.", flush=True)

        for i, frame in enumerate(frames):
            try:
                src = frame.get_attribute("src") or ""
                name = frame.get_attribute("name") or ""
                
                # Chỉ chui vào iframe của Google/Recaptcha
                if "recaptcha" in src or "google.com" in src or "recaptcha" in name:
                    print(f"   👉 Iframe {i} nghi vấn. Đang chui vào...", flush=True)
                    driver.switch_to.frame(frame)
                    
                    targets = [
                        (By.CLASS_NAME, "recaptcha-checkbox-border"),
                        (By.ID, "recaptcha-anchor"),
                        (By.XPATH, "//div[@role='checkbox']")
                    ]
                    
                    clicked = False
                    for method, selector in targets:
                        try:
                            elm = driver.find_element(method, selector)
                            if elm:
                                print(f"   ✅ BINGO! Đã bấm vào nút CAPTCHA!", flush=True)
                                driver.execute_script("arguments[0].click();", elm)
                                clicked = True
                                break
                        except: pass
                    
                    if clicked:
                        gui_anh_tele(driver, "📸 Đã bấm CAPTCHA")
                        time.sleep(5)
                        driver.switch_to.default_content()
                        return True
                    
                    driver.switch_to.default_content()
                    
            except:
                driver.switch_to.default_content()
                
    except Exception as e:
        print(f"   ! Lỗi quét iframe: {e}")
    return False

def setup_driver():
    print(">>> 🛠️ Đang khởi tạo Driver (V50 - MANUAL IPHONE)...", flush=True)
    
    options = uc.ChromeOptions()
    options.add_argument("--headless=new") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # 🔥 FIX: THAY VÌ mobileEmulation, TA CẤU HÌNH THỦ CÔNG
    # 1. Ép kích thước màn hình điện thoại
    options.add_argument("--window-size=375,812")
    options.add_argument("--lang=en-US")
    
    # 2. Ép User Agent của iPhone trực tiếp
    ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
    options.add_argument(f"--user-agent={ua}")

    # Fix Version 144
    driver = uc.Chrome(options=options, version_main=144)
    return driver

# ==============================================================================
# MAIN LOOP
# ==============================================================================
def main():
    print(">>> 🚀 BOT KHỞI ĐỘNG...", flush=True)
    email = os.environ.get("FB_EMAIL")
    password = os.environ.get("FB_PASS")
    
    if not email or not password: return

    try:
        driver = setup_driver()
    except Exception as e:
        print(f"❌ Lỗi Driver: {e}"); return

    wait = WebDriverWait(driver, 40)

    try:
        # --- LOGIN ---
        print(">>> 📱 Vào Facebook...", flush=True)
        driver.get("https://m.facebook.com/?locale=en_US")
        
        # 0. Check CAPTCHA ĐẦU GAME
        handle_captcha_aggressive(driver)

        # 1. Nhập Email
        print(">>> 🔐 Nhập Email...", flush=True)
        try:
            email_box = wait.until(EC.presence_of_element_located((By.NAME, "email")))
            email_box.clear(); email_box.send_keys(email)
        except Exception as e:
            gui_anh_tele(driver, f"❌ Lỗi tìm ô Email: {e}")
            return

        time.sleep(2)

        # 2. Xử lý nút Continue
        if len(driver.find_elements(By.NAME, "pass")) == 0:
            print("   Login 2 bước...", flush=True)
            targets = ["//div[@role='button']", "//button"]
            for xp in targets:
                try:
                    elms = driver.find_elements(By.XPATH, xp)
                    for e in elms:
                        if "continue" in e.text.lower():
                            force_click(driver, e); time.sleep(1)
                except: pass
            
            try: email_box.send_keys(Keys.ENTER)
            except: pass
            time.sleep(5)

        # 3. NHẬP PASSWORD & BẤM LOGIN
        print(">>> 🔐 Đang đợi ô Password...", flush=True)
        try:
            pass_box = None
            try: pass_box = wait.until(EC.visibility_of_element_located((By.NAME, "pass")))
            except: 
                try: pass_box = driver.find_element(By.XPATH, "//input[@type='password']")
                except: pass

            if pass_box:
                pass_box.click(); pass_box.send_keys(password); time.sleep(1)
                
                # Bấm Login
                clicked = False
                try:
                    login_btn = driver.find_element(By.NAME, "login")
                    force_click(driver, login_btn); clicked = True
                except:
                    divs = driver.find_elements(By.XPATH, "//div[@role='button']")
                    for d in divs:
                        if "log in" in d.text.lower():
                            force_click(driver, d); clicked = True; break
                
                if not clicked: pass_box.send_keys(Keys.ENTER)
            else:
                gui_anh_tele(driver, "❌ Mất tích ô Password"); return
        except Exception as e: return

        # ==================================================================
        # 🔥 ĐIỂM CHÈN CAPTCHA SAU KHI BẤM LOGIN
        # ==================================================================
        print(">>> ⏳ Đợi chuyển trang...", flush=True)
        time.sleep(8) 
        
        handle_captcha_aggressive(driver)
        
        # Bấm Continue nếu sau captcha nó hiện ra
        try:
            con_btns = driver.find_elements(By.XPATH, "//button[contains(text(), 'Continue')] | //span[contains(text(), 'Continue')]")
            if con_btns and con_btns[0].is_displayed():
                force_click(driver, con_btns[0])
                time.sleep(5)
        except: pass
        # ==================================================================

        # --- 2FA ---
        print(">>> 🕵️ Kiểm tra 2FA...", flush=True)
        is_2fa = False
        if "checkpoint" in driver.current_url or "two_step" in driver.page_source or "code" in driver.page_source.lower():
            is_2fa = True
        
        if is_2fa:
            print(">>> ⚠️ Đang tìm ô nhập Code...", flush=True)
            code_input = None
            for i in range(5):
                inputs = driver.find_elements(By.TAG_NAME, "input")
                for inp in inputs:
                    try:
                        if inp.is_displayed():
                            t = inp.get_attribute("type")
                            p = inp.get_attribute("placeholder") or ""
                            n = inp.get_attribute("name") or ""
                            if t in ["number", "tel"] or "code" in p.lower() or "approvals_code" in n:
                                code_input = inp
                                break
                    except: pass
                if code_input: break
                time.sleep(2)

            if code_input:
                print(">>> ✅ Thấy ô nhập Code.", flush=True)
                otp_code = get_code_from_email()
                if otp_code:
                    code_input.send_keys(otp_code)
                    time.sleep(2)
                    code_input.send_keys(Keys.ENTER)
                    
                    try:
                        btns = driver.find_elements(By.XPATH, "//div[@role='button'] | //button")
                        for b in btns:
                            if "continue" in b.text.lower() or "submit" in b.text.lower():
                                force_click(driver, b); break
                    except: pass
                    time.sleep(10)
                else:
                    gui_anh_tele(driver, "❌ Không có mã 2FA"); return
            else:
                gui_anh_tele(driver, "⚠️ Không thấy ô nhập Code (Lag hoặc đã qua)")

        # --- HOÀN TẤT ---
        if len(driver.find_elements(By.NAME, "email")) > 0:
            gui_anh_tele(driver, "❌ LOGIN FAILED")
            return

        xu_ly_sau_login(driver)
        gui_anh_tele(driver, "✅ LOGIN THÀNH CÔNG! ĐANG NGÂM...")
        
        total_time = 21600 
        check_interval = 1800 
        loops = int(total_time / check_interval)
        for i in range(loops):
            print(f"   💤 Treo máy... ({i+1}/{loops})", flush=True)
            time.sleep(check_interval)
            try: driver.get("https://m.facebook.com/?locale=en_US")
            except: pass

        print(">>> ✅ XONG 6 TIẾNG.", flush=True)

    except Exception as e:
        print(f"❌ Lỗi Fatal: {e}")
    finally:
        try: driver.quit()
        except: pass

if __name__ == "__main__":
    main()
