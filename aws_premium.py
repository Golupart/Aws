import os
import time
import random
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

# Load tokens from .env file or Environment Variables
load_dotenv()

# --- SECURITY SYSTEM ---
API_KEY = os.getenv("API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# --- TARGET CONFIG ---
TARGET_EMAIL = "hrdxew@telegmail.com"
PASSWORD = "Primex@Admin123"
DOC_NAME = "Prime.png"

# --- UI COLORS ---
GOLD = "\033[1;33m"
CYAN = "\033[1;36m"
RED = "\033[1;31m"
RESET = "\033[0m"

def show_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{GOLD}" + "="*60)
    print(f"   PRIMEXARMY | AWS VVIP AUTOMATOR V4")
    print(f"   API STATUS: {'[ACTIVE]' if API_KEY else '[MISSING]'}")
    print(f"   BOT TOKEN: {'[LOADED]' if BOT_TOKEN else '[ERROR]'}")
    print("="*60 + f"{RESET}")

class AWSBot:
    def __init__(self):
        self.options = uc.ChromeOptions()
        self.options.add_argument('--start-maximized')
        self.driver = None

    def type_like_human(self, element, text):
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.08, 0.15))

    def run(self):
        show_banner()
        if not BOT_TOKEN:
            print(f"{RED}[!] Error: BOT_TOKEN nahi mila! .env check karein.{RESET}")
            return

        print(f"[{GOLD}*{RESET}] Starting Stealth Chrome Engine...")
        self.driver = uc.Chrome(options=self.options, use_subprocess=True)
        
        try:
            self.driver.get("https://portal.aws.amazon.com/billing/signup")
            wait = WebDriverWait(self.driver, 20)

            # --- PHASE 1: LOGIN ---
            print(f"[{GOLD}1{RESET}] Filling Email: {TARGET_EMAIL}")
            email_field = wait.until(EC.element_to_be_clickable((By.ID, "awsui-input-0")))
            self.type_like_human(email_field, TARGET_EMAIL)
            
            print(f"[{GOLD}!{RESET}] OTP verify karke ENTER dabayein...")
            input()

            # --- PHASE 2: PASSWORD ---
            print(f"[{GOLD}2{RESET}] Injecting Secure Password...")
            pass_field = wait.until(EC.presence_of_element_located((By.ID, "awsui-input-2")))
            self.type_like_human(pass_field, PASSWORD)
            
            print(f"[{GOLD}!{RESET}] KYC Page par pahuche hi ENTER dabayein...")
            input()

            # --- PHASE 3: KYC INJECTION ---
            self.inject_document()

        except Exception as e:
            print(f"{RED}[ERROR] {str(e)}{RESET}")
        finally:
            print(f"\n{GOLD}Process Complete. Manual check karein.{RESET}")
            input("Close karne ke liye ENTER dabayein...")
            if self.driver: self.driver.quit()

    def inject_document(self):
        print(f"[{GOLD}3{RESET}] Detecting Prime.png system...")
        file_path = os.path.abspath(DOC_NAME)
        
        if not os.path.exists(file_path):
            print(f"{RED}[ERR] {DOC_NAME} folder mein nahi mili!{RESET}")
            return

        try:
            wait = WebDriverWait(self.driver, 15)
            # AWS file input find and inject
            file_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='file']")))
            print(f"[{GOLD}✓{RESET}] Injecting Identity: {DOC_NAME}")
            file_input.send_keys(file_path)
            time.sleep(3)
            print(f"[{GOLD}DONE{RESET}] Document successfully uploaded!")
        except:
            print(f"{RED}[!] Upload field nahi mila. Manual karein.{RESET}")

if __name__ == "__main__":
    AWSBot().run()