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
            try:
                actions = ActionChains(driver)
                actions.move_to_element(element).click().perform()
                return True
            except:
                return False

def xu_ly_sau_login(driver):
    print(">>> 🛡️ Đang dọn dẹp popup sau login...", flush=True)
    try:
        # Xpath tổng hợp cả Mobile lẫn Desktop
        check_xpaths = [
            "//span[contains(text(), 'Save')]", "//div[@role='button' and contains(., 'Save')]",
            "//span[contains(text(), 'Continue')]", "//div[@role='button' and contains(., 'Continue')]",
            "//span[contains(text(), 'OK')]", "//span[contains(text(), 'Lưu')]", "//span[contains(text(), 'Tiếp tục')]",
            "//div[@aria-label='Close']", "//div[@aria-label='Đóng']",
            "//span[contains(text(), 'Remember Password')]"
        ]
        for _ in range(3):
            for xp in check_xpaths:
                try:
                    btns = driver.find_elements(By.XPATH, xp)
                    for btn in btns:
                        if btn.is_displayed():
                            print(f"   🔨 Bấm nút: {btn.text}", flush=True)
                            force_click(driver, btn)
                            time.sleep(3) 
                            return 
                except: pass
            time.sleep(1)
    except: pass

def setup_driver():
    print(">>> 🛠️ Đang khởi tạo Driver (PROFILE: WINDOWS LAPTOP)...", flush=True)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # 🔥 1. Cấu hình màn hình Desktop Full HD
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--start-maximized")
    
    # 🔥 2. Fake User Agent (Windows 10 - Edge/Chrome Like)
    # Lưu ý: Dùng version 120+ cho ổn định, 144 sợ hơi ảo (vì chưa ra mắt chính thức), 
    # nhưng tôi sẽ để cấu trúc giống hệt bác yêu cầu.
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0"
    chrome_options.add_argument(f"--user-agent={ua}")
    chrome_options.add_argument("--lang=en-US")

    # 🔥 3. Anti-Detection
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)

    # 🔥 4. Bơm Headers xịn (Client Hints) để vượt qua bộ lọc check device
    # Đây là bước quan trọng để Facebook tin đây là Laptop thật
    driver.execute_cdp_cmd("Network.setUserAgentOverride", {
        "userAgent": ua,
        "platform": "Windows",
        "userAgentMetadata": {
            "brands": [
                {"brand": "Chromium", "version": "122"},
                {"brand": "Microsoft Edge", "version": "122"},
                {"brand": "Not(A:Brand", "version": "24"}
            ],
            "fullVersion": "122.0.0.0",
            "platform": "Windows",
            "platformVersion": "10.0.0",
            "architecture": "x86",
            "model": "",
            "mobile": False  # QUAN TRỌNG: ?0 nghĩa là False (Desktop)
        }
    })

    # 🔥 5. Fake Hardware (Giống Laptop)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8}); // Laptop thường 4-8 nhân
            Object.defineProperty(navigator, 'deviceMemory', {get: () => 8}); // 8GB RAM
            Object.defineProperty(navigator, 'platform', {get: () => 'Win32'}); // Windows luôn báo là Win32
            Object.defineProperty(navigator, 'maxTouchPoints', {get: () => 0}); // Laptop ko cảm ứng
        """
    })
    
    # 6. Fake IP/Timezone (New York)
    driver.execute_cdp_cmd("Emulation.setTimezoneOverride", { "timezoneId": "America/New_York" })
    driver.execute_cdp_cmd("Emulation.setGeolocationOverride", { "latitude": 40.7128, "longitude": -74.0060, "accuracy": 100 })
    
    return driver

# ==============================================================================
# MAIN LOOP
# ==============================================================================
def main():
    print(">>> 🚀 BOT LAPTOP (V39) KHỞI ĐỘNG...", flush=True)
    email = os.environ.get("FB_EMAIL")
    password = os.environ.get("FB_PASS")
    
    if not email or not password: return

    driver = setup_driver()
    wait = WebDriverWait(driver, 40)

    try:
        # --- LOGIN (Vẫn dùng m.facebook.com vì nhẹ và dễ bot, nhưng UserAgent là Desktop) ---
        print(">>> 💻 Vào Facebook (Desktop Mode)...", flush=True)
        driver.get("https://m.facebook.com/?locale=en_US") 
        # Lưu ý: Dù vào 'm.' nhưng với UserAgent Laptop, FB có thể tự redirect sang 'www.' hoặc giao diện mbasic.
        # Code dưới đây được thiết kế để xử lý linh hoạt cả 2 trường hợp.

        # 0. Check CAPTCHA
        if "I'm not a robot" in driver.page_source:
            gui_anh_tele(driver, "❌ DÍNH CAPTCHA NGAY ĐẦU!")
            return

        # 1. Nhập Email
        print(">>> 🔐 Nhập Email...", flush=True)
        try:
            email_box = wait.until(EC.presence_of_element_located((By.NAME, "email")))
            email_box.clear(); email_box.send_keys(email)
        except Exception as e:
            gui_anh_tele(driver, f"❌ Lỗi tìm ô Email: {e}")
            return

        time.sleep(2)

        # 2. Xử lý nút Continue (Vét cạn)
        # Kiểm tra xem có phải login 2 bước (nhập mail -> continue -> nhập pass)
        if len(driver.find_elements(By.NAME, "pass")) == 0:
            print("   Login 2 bước: Đang xử lý nút Continue...", flush=True)
            targets = [
                "//div[@role='button' and @aria-label='Continue']",
                "//div[contains(text(), 'Continue')]",
                "//button[contains(text(), 'Continue')]",
                "//button[@id='loginbutton']", # Desktop layout thường dùng id này
                "//input[@type='submit']"
            ]
            for xp in targets:
                try:
                    elms = driver.find_elements(By.XPATH, xp)
                    for elm in elms:
                        if elm.is_displayed():
                            print(f"   👉 Bấm nút: {xp}", flush=True)
                            force_click(driver, elm); time.sleep(1)
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
                clicked_login = False
                login_targets = [
                    "//div[@role='button' and @aria-label='Log in']", 
                    "//button[@name='login']", # Chuẩn Desktop
                    "//div[contains(text(), 'Log in')]",
                    "//button[@id='loginbutton']",
                    "//input[@value='Log In']"
                ]
                for xp in login_targets:
                    try:
                        btns = driver.find_elements(By.XPATH, xp)
                        for btn in btns:
                            if btn.is_displayed():
                                force_click(driver, btn); clicked_login = True; time.sleep(1)
                    except: pass
                
                if not clicked_login: pass_box.send_keys(Keys.ENTER)
            else:
                gui_anh_tele(driver, "❌ Mất tích ô Password"); return
        except Exception as e: return

        time.sleep(10)

        # --- XỬ LÝ 2FA (LOGIC THÔNG MINH) ---
        print(">>> 🕵️ Kiểm tra 2FA...", flush=True)
        
        # Check "Try another way"
        try:
            try_btn = driver.find_elements(By.XPATH, "//span[contains(text(), 'Try another way')]") or driver.find_elements(By.XPATH, "//div[contains(., 'Try another way')]") or driver.find_elements(By.XPATH, "//a[contains(text(), 'Try another way')]")
            if try_btn and try_btn[0].is_displayed():
                force_click(driver, try_btn[0]); time.sleep(5)
                # Chọn Email
                email_opts = driver.find_elements(By.XPATH, "//span[contains(text(), 'Email')]")
                if email_opts and email_opts[0].is_displayed():
                    force_click(driver, email_opts[0]); time.sleep(2)
                    c_btns = driver.find_elements(By.XPATH, "//div[@aria-label='Continue']") or driver.find_elements(By.XPATH, "//span[contains(text(), 'Continue')]") or driver.find_elements(By.XPATH, "//button[contains(text(), 'Continue')]")
                    if c_btns: force_click(driver, c_btns[0]); time.sleep(10)
        except: pass

        # === TÌM Ô NHẬP MÃ (VÉT CẠN MỌI LOẠI INPUT) ===
        # Vì là Desktop layout có thể khác Mobile, nên chiến thuật "vét cạn" là an toàn nhất
        code_input = None
        for attempt in range(5): 
            print(f">>> ⏳ Quét ô nhập mã lần {attempt+1}/5...", flush=True)
            
            # 1. Tìm theo Placeholder
            try: 
                inps = driver.find_elements(By.XPATH, "//input[@placeholder='Enter code']") or driver.find_elements(By.XPATH, "//input[@placeholder='Code']")
                if inps: code_input = inps[0]
            except: pass
            
            # 2. Tìm theo name
            if not code_input:
                try:
                    inps = driver.find_elements(By.XPATH, "//input[@name='n']") or driver.find_elements(By.XPATH, "//input[@name='approvals_code']")
                    if inps: code_input = inps[0]
                except: pass
            
            # 3. Chiến thuật VÉT CẠN (Laptop hay dùng): Tìm tất cả input text/number
            if not code_input:
                all_inputs = driver.find_elements(By.TAG_NAME, "input")
                for inp in all_inputs:
                    try:
                        inp_type = inp.get_attribute("type")
                        # Lọc các input không phải mã (ẩn, checkbox, email, password...)
                        if inp.is_displayed() and inp_type in ["text", "number", "tel"] and inp.get_attribute("name") != "email":
                            code_input = inp
                            print(f"   👉 Phát hiện ô input lạ (Có thể là ô mã): Type={inp_type}", flush=True)
                            break
                    except: pass
            
            if code_input: break
            time.sleep(3) 

        if code_input:
            print(">>> ❗ Đang lấy mã từ Email...", flush=True)
            otp_code = get_code_from_email()
            
            if otp_code:
                print(f">>> ✍️ Nhập mã: {otp_code}", flush=True)
                code_input.send_keys(otp_code)
                time.sleep(2)
                code_input.send_keys(Keys.ENTER)
                time.sleep(10)
                
                # Bấm Continue nếu cần
                try:
                    s_btns = driver.find_elements(By.XPATH, "//button[@type='submit']") or driver.find_elements(By.XPATH, "//span[contains(text(), 'Continue')]")
                    if s_btns: force_click(driver, s_btns[0])
                except: pass
            else:
                print(">>> ❌ Không có mã. Dừng.", flush=True); return
        else:
            print(">>> ⚠️ Không thấy ô nhập Code. (Hy vọng đã login thẳng hoặc bị kẹt)")

        # --- CHECK LOG FINAL ---
        if len(driver.find_elements(By.NAME, "email")) > 0:
            print(">>> ❌ Vẫn thấy ô nhập Email -> LOGIN THẤT BẠI!", flush=True)
            gui_anh_tele(driver, "❌ LOGIN FAILED (Vẫn ở trang chủ)")
            return
        
        if "I'm not a robot" in driver.page_source:
             gui_anh_tele(driver, "❌ DÍNH CAPTCHA CUỐI CÙNG!")
             return

        # --- NẾU QUA ĐƯỢC ĐÂY LÀ NGON ---
        xu_ly_sau_login(driver)
        gui_anh_tele(driver, "✅ LOGIN THÀNH CÔNG (PC MODE)! ĐANG NGÂM...")

        # NGÂM 6 TIẾNG
        total_time = 21600 
        check_interval = 1800 
        loops = int(total_time / check_interval)
        
        for i in range(loops):
            print(f"   💤 Treo máy... (Chu kỳ {i+1}/{loops})", flush=True)
            time.sleep(check_interval)
            try:
                print("   🔄 Refresh nhẹ...", flush=True)
                driver.get("https://m.facebook.com/?locale=en_US")
                time.sleep(10)
            except: pass

        print(">>> ✅ XONG 6 TIẾNG.", flush=True)

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
