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
    """Click bất chấp mọi vật cản"""
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
    print(">>> 🛠️ Đang khởi tạo Driver (US Profile)...", flush=True)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=375,812")
    chrome_options.add_argument("--lang=en-US")
    
    # Fake Hardware & WebRTC (Giả lập iPhone)
    chrome_options.add_argument("--disable-webrtc")
    ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
    mobile_emulation = {
        "deviceMetrics": { "width": 375, "height": 812, "pixelRatio": 3.0 },
        "userAgent": ua
    }
    chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = webdriver.Chrome(options=chrome_options)

    # ===================== AUTO-ALLOW GPS (THÊM) =====================
    # Chỉ cấp quyền Location cho Facebook
    try:
        driver.execute_cdp_cmd(
            "Browser.grantPermissions",
            {
                "origin": "https://m.facebook.com",
                "permissions": ["geolocation"]
            }
        )
    except:
        pass

    # Fake CPU/GPU/Timezone/GPS (Boydton, VA)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 6});
            Object.defineProperty(navigator, 'deviceMemory', {get: () => 4});
        """
    })
    driver.execute_cdp_cmd(
        "Emulation.setTimezoneOverride",
        { "timezoneId": "America/New_York" }
    )
    driver.execute_cdp_cmd(
        "Emulation.setGeolocationOverride",
        {
            "latitude": 36.6676,
            "longitude": -78.3875,
            "accuracy": 150
        }
    )
    
    return driver

# ==============================================================================
# MAIN LOOP (CHẾ ĐỘ NGÂM IP)
# ==============================================================================
def main():
    print(">>> 🚀 BOT NGÂM IP KHỞI ĐỘNG...", flush=True)
    email = os.environ.get("FB_EMAIL")
    password = os.environ.get("FB_PASS")
    
    if not email or not password: return

    driver = setup_driver()
    wait = WebDriverWait(driver, 40)

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
            
            return

        time.sleep(2)

        # 2. Xử lý nút Continue (Vét cạn div/button/enter)
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
                    "//button[@name='login']",
                    "//div[contains(text(), 'Log in')]"
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
                return
        except Exception as e: return

        time.sleep(10)

        # --- XỬ LÝ 2FA (FIX MỚI NHẤT) ---
        print(">>> 🕵️ Kiểm tra 2FA...", flush=True)
        
        # 1. Bấm "Try another way" -> Chọn Email (Nếu bị hỏi)
        try:
            try_btn = driver.find_elements(By.XPATH, "//span[contains(text(), 'Try another way')]") or driver.find_elements(By.XPATH, "//div[contains(., 'Try another way')]")
            if try_btn and try_btn[0].is_displayed():
                force_click(driver, try_btn[0]); time.sleep(5)
        except: pass

        try:
            email_opts = driver.find_elements(By.XPATH, "//span[contains(text(), 'Email')]")
            if email_opts and email_opts[0].is_displayed():
                force_click(driver, email_opts[0]); time.sleep(2)
                c_btns = driver.find_elements(By.XPATH, "//div[@aria-label='Continue']") or driver.find_elements(By.XPATH, "//span[contains(text(), 'Continue')]")
                if c_btns: force_click(driver, c_btns[0]); time.sleep(10)
        except: pass

        # 2. TÌM Ô NHẬP MÃ (CHIẾN THUẬT: TÌM BẤT CỨ CÁI Ô NÀO HIỆN RA)
        # Vì bác bảo "cả màn hình có mỗi 1 ô", nên ta tìm tất cả input visible
        print(">>> ❗ Đang tìm ô nhập mã (Vét cạn)...", flush=True)
        code_input = None
        
        # Ưu tiên 1: Theo Placeholder (Chuẩn nhất theo ảnh bác gửi)
        try: code_input = driver.find_element(By.XPATH, "//input[@placeholder='Enter code']")
        except: pass
        
        # Ưu tiên 2: Nếu không thấy, tìm TẤT CẢ ô input và lấy cái đầu tiên hiện ra
        if not code_input:
            all_inputs = driver.find_elements(By.TAG_NAME, "input")
            for inp in all_inputs:
                if inp.is_displayed() and inp.get_attribute("type") != "hidden":
                    code_input = inp
                    print(f"   👉 Tìm thấy input lạ: type={inp.get_attribute('type')}", flush=True)
                    break

        if code_input:
            print(">>> ✅ Đã thấy ô nhập mã!", flush=True)
            otp_code = get_code_from_email()
            
            if otp_code:
                print(f">>> ✍️ Nhập mã: {otp_code}", flush=True)
                code_input.send_keys(otp_code)
                time.sleep(2)
                code_input.send_keys(Keys.ENTER)
                
                # Bấm Continue sau khi nhập
                try:
                    s_btns = driver.find_elements(By.XPATH, "//span[contains(text(), 'Continue')]") or driver.find_elements(By.XPATH, "//button[@type='submit']")
                    if s_btns: force_click(driver, s_btns[0])
                except: pass
                time.sleep(10)
            else:
                print(">>> ❌ Không có mã từ Email. Tắt Bot.", flush=True)
                return
        else:
            # Nếu vẫn không thấy thì bot chịu, chụp ảnh để bác chửi tiếp
            print(">>> ❌ Vẫn không tìm thấy ô nhập nào!", flush=True)
            

        # --- HOÀN TẤT & NGÂM ---
        xu_ly_sau_login(driver)
        
        try:
            driver.get("https://m.facebook.com/?locale=en_US")
            time.sleep(10)
            
            
            # SỬA LẠI THEO YÊU CẦU: KIỂM TRA XEM CÓ BỊ ĐÁ RA LOGIN KHÔNG
            if len(driver.find_elements(By.NAME, "email")) > 0:
                print(">>> ❌ Phát hiện ô nhập Email (Bị đá ra Login) -> Dừng chương trình.", flush=True)
                
                return
                
        except: pass
        # ==== LẤY GPS TỪ TRÌNH DUYỆT (TƯƠNG ĐƯƠNG console.log) ====
        gps_log = ""
        try:
            gps = driver.execute_async_script("""
                const cb = arguments[arguments.length - 1];
                navigator.geolocation.getCurrentPosition(
                    p => {
                        cb({
                            lat: p.coords.latitude,
                            lng: p.coords.longitude,
                            acc: p.coords.accuracy
                        });
                    },
                    e => {
                        cb({ error: "DENIED: " + e.message });
                    }
                );
            """)
            if gps and "lat" in gps:
                gps_log = f"📍 GPS: {gps['lat']}, {gps['lng']} | acc={gps['acc']}m"
            else:
                gps_log = f"⚠️ GPS ERROR: {gps}"
        except Exception as e:
            gps_log = f"⚠️ GPS EXCEPTION: {e}"
        gui_anh_tele(
            driver,
            "✅ LOGIN THÀNH CÔNG! BẮT ĐẦU NGÂM 6H...\n" + gps_log
        )

        # NGÂM 6 TIẾNG (KHÔNG TƯƠNG TÁC)
        total_time = 21600 
        check_interval = 1800 
        loops = int(total_time / check_interval)
        
        for i in range(loops):
            print(f"   💤 Treo máy... (Chu kỳ {i+1}/{loops})", flush=True)
            time.sleep(check_interval)
            try:
                # Refresh nhẹ để giữ session, không làm gì khác
                driver.get("https://m.facebook.com/?locale=en_US")
                time.sleep(10)
                gui_anh_tele(
                    driver,
                    "✅ VẪN SỐNG" + gps_log
                )
            except: pass

        print(">>> ✅ XONG 6 TIẾNG.", flush=True)

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
