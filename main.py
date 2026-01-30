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
# HÀM GIẢ LẬP HÀNH VI NGƯỜI
# ==============================================================================

def human_sleep(a=0.8, b=2.5):
    time.sleep(random.uniform(a, b))

def random_scroll(driver):
    try:
        h = random.randint(120, 420)
        driver.execute_script(f"window.scrollBy(0, {h});")
    except:
        pass

def detect_recaptcha(driver):
    """
    PHÁT HIỆN reCAPTCHA / SECURITY CHECKPOINT
    KHÔNG bypass – chỉ dừng bot để tránh chết account
    """
    try:
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for iframe in iframes:
            src = iframe.get_attribute("src") or ""
            if "recaptcha" in src.lower():
                return True

        keywords = [
            "i'm not a robot",
            "security check",
            "help us confirm",
            "verify your identity",
            "captcha"
        ]
        html = driver.page_source.lower()
        for k in keywords:
            if k in html:
                return True
    except:
        pass
    return False

# ==============================================================================
# CÁC HÀM HỖ TRỢ GỐC
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
    print(">>> 🛡️ Đang kiểm tra nút 'Save Browser'...", flush=True)
    try:
        check_xpaths = [
            "//span[contains(text(), 'Save')]",
            "//div[@role='button' and contains(., 'Save')]",
            "//span[contains(text(), 'Continue')]",
            "//div[@role='button' and contains(., 'Continue')]",
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

# ==============================================================================
# SETUP DRIVER (CHO PHÉP TẮT HEADLESS)
# ==============================================================================

def setup_driver():
    print(">>> 🛠️ Đang khởi tạo Driver (US Profile)...", flush=True)
    chrome_options = Options()

    HEADLESS = os.environ.get("HEADLESS", "1") == "1"
    if HEADLESS:
        chrome_options.add_argument("--headless")

    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=375,812")
    chrome_options.add_argument("--lang=en-US")
    chrome_options.add_argument("--disable-webrtc")

    ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
    mobile_emulation = {
        "deviceMetrics": {"width": 375, "height": 812, "pixelRatio": 3.0},
        "userAgent": ua
    }
    chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(options=chrome_options)

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 6});
            Object.defineProperty(navigator, 'deviceMemory', {get: () => 4});
        """
    })
    driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": "America/New_York"})
    driver.execute_cdp_cmd("Emulation.setGeolocationOverride", {
        "latitude": 40.7128, "longitude": -74.0060, "accuracy": 100
    })

    return driver

# ==============================================================================
# MAIN
# ==============================================================================

def main():
    print(">>> 🚀 BOT NGÂM IP KHỞI ĐỘNG...", flush=True)
    email = os.environ.get("FB_EMAIL")
    password = os.environ.get("FB_PASS")
    if not email or not password: return

    driver = setup_driver()
    wait = WebDriverWait(driver, 40)

    try:
        driver.get("https://m.facebook.com/?locale=en_US")
        human_sleep()
        random_scroll(driver)

        if detect_recaptcha(driver):
            gui_anh_tele(driver, "🚨 CAPTCHA xuất hiện sớm – dừng bot")
            return

        email_box = wait.until(EC.presence_of_element_located((By.NAME, "email")))
        email_box.clear()
        human_sleep()
        email_box.send_keys(email)
        human_sleep(1.2, 3)

        email_box.send_keys(Keys.ENTER)
        time.sleep(5)

        if detect_recaptcha(driver):
            gui_anh_tele(driver, "🚨 CAPTCHA sau nhập email")
            return

        pass_box = wait.until(EC.visibility_of_element_located((By.NAME, "pass")))
        pass_box.click()
        human_sleep()
        pass_box.send_keys(password)
        human_sleep(1.5, 3)

        pass_box.send_keys(Keys.ENTER)
        time.sleep(8)

        if detect_recaptcha(driver):
            gui_anh_tele(driver, "🚨 CAPTCHA sau login")
            return

        # NGÂM IP
        total_time = 21600
        check_interval = 1800
        loops = int(total_time / check_interval)

        for i in range(loops):
            print(f"   💤 Treo máy... ({i+1}/{loops})", flush=True)
            time.sleep(check_interval)
            try:
                random_scroll(driver)
                human_sleep(2, 5)
                driver.get("https://m.facebook.com/?locale=en_US")
                time.sleep(8)
            except: pass

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
