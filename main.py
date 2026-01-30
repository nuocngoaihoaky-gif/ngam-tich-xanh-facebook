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

def force_click(driver, element, method_name="Unknown"):
    """Hàm click cưỡng bức có chụp ảnh báo cáo"""
    try:
        # Cách 1: Click thường
        element.click()
        print(f"   👉 Click thường vào {method_name}", flush=True)
        return True
    except:
        try:
            # Cách 2: JS Click
            driver.execute_script("arguments[0].click();", element)
            print(f"   👉 JS Click vào {method_name}", flush=True)
            return True
        except:
            try:
                # Cách 3: ActionChains
                actions = ActionChains(driver)
                actions.move_to_element(element).click().perform()
                print(f"   👉 ActionChains Click vào {method_name}", flush=True)
                return True
            except:
                return False

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
# MAIN LOOP (DEBUG MODE)
# ==============================================================================
def main():
    print(">>> 🚀 BOT KHỞI ĐỘNG (DEBUG STEP 1)...", flush=True)
    email = os.environ.get("FB_EMAIL")
    
    if not email: return

    driver = setup_driver()
    wait = WebDriverWait(driver, 40) # Tăng timeout lên 40s

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

        time.sleep(3)

        # 2. KIỂM TRA & DEBUG CÁC NÚT CONTINUE
        # Thử tìm ô Pass trước
        if len(driver.find_elements(By.NAME, "pass")) > 0:
            print("   ✅ Đã thấy ô Pass ngay từ đầu!", flush=True)
            gui_anh_tele(driver, "✅ Đã thấy ô Pass. DỪNG.")
            return

        print("   🔍 Bắt đầu thử từng cách để bấm Continue...", flush=True)
        
        # Danh sách các chiêu thức
        methods = [
            # 1. Enter vào ô Email
            ("ENTER Key", lambda: email_box.send_keys(Keys.ENTER)),
            
            # 2. Bấm div (Theo ảnh của bác)
            ("Div Button", lambda: force_click(driver, driver.find_element(By.XPATH, "//div[@role='button' and @aria-label='Continue']"), "Div Button")),
            
            # 3. Bấm span chữ (Theo ảnh của bác)
            ("Span Text", lambda: force_click(driver, driver.find_element(By.XPATH, "//span[contains(text(), 'Continue')]"), "Span Text")),
            
            # 4. Bấm button thường
            ("Tag Button", lambda: force_click(driver, driver.find_element(By.XPATH, "//button[contains(text(), 'Continue')]"), "Tag Button")),
            
            # 5. Bấm nút Login (trường hợp nó là nút login)
            ("Login Btn", lambda: force_click(driver, driver.find_element(By.NAME, "login"), "Login Btn"))
        ]

        success = False
        
        for name, action in methods:
            print(f"\n--- 🧪 Đang thử cách: {name} ---", flush=True)
            try:
                # Thực hiện hành động
                action()
                
                # Chờ 10s xem có chuyển trang không
                print("   ⏳ Đang chờ 10s xem trang có load không...", flush=True)
                time.sleep(10)
                
                # CHỤP ẢNH BÁO CÁO NGAY LẬP TỨC
                gui_anh_tele(driver, f"📸 Sau khi thử {name}")
                
                # Kiểm tra xem có ô Pass chưa
                if len(driver.find_elements(By.NAME, "pass")) > 0:
                    print("   🎉 THÀNH CÔNG! Đã thấy ô Password.", flush=True)
                    gui_anh_tele(driver, f"✅ KẾT QUẢ: Cách '{name}' ĐÃ HIỆU QUẢ! DỪNG BOT.")
                    success = True
                    break # Thoát vòng lặp
                else:
                    print("   ❌ Vẫn chưa thấy ô Pass.", flush=True)
                    
            except Exception as e:
                print(f"   ⚠️ Cách {name} bị lỗi: {e}", flush=True)

        if not success:
            print(">>> ❌ Đã thử hết cách mà không qua được.", flush=True)
            gui_anh_tele(driver, "❌ THẤT BẠI TOÀN TẬP")

    except Exception as e:
        gui_anh_tele(driver, f"❌ Lỗi Bot: {e}")

    finally:
        print(">>> 🛑 Dừng Bot để kiểm tra.", flush=True)
        driver.quit()

if __name__ == "__main__":
    main()
