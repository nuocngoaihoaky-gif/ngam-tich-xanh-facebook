import time
import random
import os
import sys
import requests
from datetime import datetime
import pytz
# Thư viện chống phát hiện (Bắt buộc)
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==============================================================================
# CẤU HÌNH
# ==============================================================================
GAS_API_URL = os.environ.get("GAS_API_URL")

# ==============================================================================
# HÀM HỖ TRỢ
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
    if not GAS_API_URL: return None
    print(">>> 📧 Đang gọi API lấy mã...", flush=True)
    for i in range(6):
        try:
            response = requests.get(GAS_API_URL)
            code = response.text.strip()
            if code and code != "NO_CODE":
                print(f"   + ✅ Code: {code}", flush=True)
                return code
            time.sleep(10)
        except: time.sleep(5)
    return None

def setup_driver():
    print(">>> 🛠️ Khởi tạo Driver (Desktop V44 - Fix 144 + Anti-Captcha)...", flush=True)
    options = uc.ChromeOptions()
    # Chế độ headless mới (ổn định hơn cho undetected)
    options.add_argument("--headless=new") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=en-US")
    
    # Fake User Agent Windows 10 chuẩn
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")

    # 🔥 FIX QUAN TRỌNG: Ép dùng Driver 144 để khớp với Browser 144 trên Server
    driver = uc.Chrome(options=options, version_main=144)
    return driver

# ==============================================================================
# MAIN LOOP
# ==============================================================================
def main():
    print(">>> 🚀 BOT DESKTOP KHỞI ĐỘNG...", flush=True)
    email = os.environ.get("FB_EMAIL")
    password = os.environ.get("FB_PASS")
    if not email or not password: return

    try:
        driver = setup_driver()
    except Exception as e:
        print(f"❌ Lỗi Driver: {e}"); return

    wait = WebDriverWait(driver, 30)

    try:
        # --- 1. VÀO FACEBOOK DESKTOP ---
        print(">>> 💻 Truy cập www.facebook.com...", flush=True)
        driver.get("https://www.facebook.com/login/?locale=en_US")
        time.sleep(5)

        # Kiểm tra CAPTCHA Arkose (Cái bảng xếp hình)
        if "arkoselabs" in driver.page_source or "challenge" in driver.title.lower():
            gui_anh_tele(driver, "❌ DÍNH CAPTCHA ARKOSE (XẾP HÌNH)!")
            return

        # --- 2. ĐĂNG NHẬP (CHUẨN HÓA THEO ẢNH BÁC GỬI) ---
        print(">>> 🔐 Nhập thông tin...", flush=True)
        try:
            # ẢNH 1: Ô Email có ID="email"
            email_box = wait.until(EC.presence_of_element_located((By.ID, "email")))
            email_box.clear(); email_box.send_keys(email)
            time.sleep(1)
            
            # ẢNH 2: Ô Pass có ID="pass"
            pass_box = driver.find_element(By.ID, "pass")
            pass_box.clear(); pass_box.send_keys(password)
            time.sleep(1)
            
            # ẢNH 3: Nút Login có Name="login"
            print(">>> 🖱️ Bấm Login...", flush=True)
            login_btn = driver.find_element(By.NAME, "login")
            driver.execute_script("arguments[0].click();", login_btn)
            
        except Exception as e:
            gui_anh_tele(driver, f"❌ Lỗi tìm ô nhập (Desktop): {e}")
            return

        time.sleep(10)

        # --- 3. XỬ LÝ SAU LOGIN & CAPTCHA ---
        print(">>> 🕵️ Kiểm tra trạng thái...", flush=True)
        
        # 🔥 TÍNH NĂNG MỚI: TỰ ĐỘNG CLICK RECAPTCHA
        if "recaptcha" in driver.page_source.lower() or "not a robot" in driver.page_source.lower():
            print(">>> ⚠️ Phát hiện reCAPTCHA! Đang thử vận may...", flush=True)
            gui_anh_tele(driver, "⚠️ Dính reCAPTCHA, đang thử Click...")
            
            try:
                # Chuyển vào iframe của reCAPTCHA (Vì checkbox nằm trong iframe)
                frames = driver.find_elements(By.TAG_NAME, "iframe")
                for frame in frames:
                    try:
                        if "recaptcha" in frame.get_attribute("src") or "recaptcha" in frame.get_attribute("name"):
                            driver.switch_to.frame(frame)
                            # Tìm checkbox và click
                            checkbox = driver.find_element(By.CLASS_NAME, "recaptcha-checkbox-border")
                            driver.execute_script("arguments[0].click();", checkbox)
                            print("   ✅ Đã Click vào Checkbox!", flush=True)
                            driver.switch_to.default_content() # Thoát khỏi iframe
                            time.sleep(5)
                            break
                    except: 
                        driver.switch_to.default_content()
                        continue
            except Exception as e:
                print(f"   ❌ Lỗi xử lý Captcha: {e}")

        # Check 2FA (Checkpoint)
        if "checkpoint" in driver.current_url or "two_step_verification" in driver.page_source:
            print(">>> ⚠️ Đang ở màn hình 2FA.", flush=True)
            
            # Tìm ô nhập code (Desktop input thường rõ ràng hơn)
            code_input = None
            try:
                # Ưu tiên tìm ô input nào đang active/visible
                inputs = driver.find_elements(By.TAG_NAME, "input")
                for inp in inputs:
                    # Lọc input text/number, bỏ qua ô search/email ẩn
                    if inp.is_displayed() and inp.get_attribute("type") in ["text", "number", "tel"]:
                        # Loại trừ ô email nếu nó còn dính lại (name='email')
                        if "email" not in str(inp.get_attribute("name")) and "search" not in str(inp.get_attribute("name")):
                            code_input = inp
                            break
            except: pass

            if code_input:
                print(">>> ✅ Đã thấy ô 2FA Desktop.", flush=True)
                otp_code = get_code_from_email()
                if otp_code:
                    code_input.send_keys(otp_code)
                    time.sleep(2)
                    code_input.send_keys(Keys.ENTER)
                    
                    # Bấm nút Continue (Trên Desktop thường là nút màu xanh)
                    time.sleep(3)
                    try:
                        # Tìm nút submit chính
                        confirm_btns = driver.find_elements(By.XPATH, "//div[@role='button']//span[contains(text(), 'Continue')]")
                        if not confirm_btns: confirm_btns = driver.find_elements(By.XPATH, "//button[@type='submit']") # Nút Gửi mã
                        if not confirm_btns: confirm_btns = driver.find_elements(By.XPATH, "//div[@aria-label='Continue']") # Nút Continue div
                        
                        if confirm_btns:
                            driver.execute_script("arguments[0].click();", confirm_btns[0])
                    except: pass
                    time.sleep(10)
                else:
                    gui_anh_tele(driver, "❌ Không lấy được mã 2FA")
                    return
            else:
                print(">>> ⚠️ Không thấy ô nhập 2FA (Có thể phải bấm 'Try another way' trước)")

        # --- 4. CHECK FINAL ---
        # Nếu vẫn còn ô email (ID='email') -> Thất bại
        if len(driver.find_elements(By.ID, "email")) > 0:
            gui_anh_tele(driver, "❌ LOGIN FAILED (Vẫn ở trang chủ)")
            return

        gui_anh_tele(driver, "✅ LOGIN THÀNH CÔNG (DESKTOP)! ĐANG NGÂM 6H...")
        
        # NGÂM (Giữ kết nối)
        total_time = 21600
        check_interval = 1800
        loops = int(total_time / check_interval)
        for i in range(loops):
            print(f"   💤 Treo máy... ({i+1}/{loops})", flush=True)
            time.sleep(check_interval)
            try: driver.get("https://www.facebook.com/")
            except: pass

        print(">>> ✅ HOÀN TẤT.", flush=True)

    except Exception as e:
        print(f"❌ Lỗi Fatal: {e}")
    finally:
        try: driver.quit()
        except: pass

if __name__ == "__main__":
    main()
