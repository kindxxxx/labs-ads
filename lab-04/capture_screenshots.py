"""Capture ejudge login + summary screenshots for lab-04."""
import os
import re
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / "screenshots"
SHOTS.mkdir(exist_ok=True)

LOGIN = os.environ.get("EJ_LOGIN", "ADS26_25B032234")
PASSWORD = os.environ.get("EJ_PASSWORD", "")
CONTEST = "204"

opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--window-size=1600,1000")
d = webdriver.Chrome(options=opts)
try:
    d.get(f"https://ejudge.kz/new-client?contest_id={CONTEST}")
    time.sleep(1)
    d.save_screenshot(str(SHOTS / "01_login_page.png"))
    d.find_element(By.NAME, "login").send_keys(LOGIN)
    d.find_element(By.NAME, "password").send_keys(PASSWORD)
    d.find_element(By.NAME, "action_2").click()
    time.sleep(2)
    d.save_screenshot(str(SHOTS / "02_after_login.png"))
    sid = re.search(r'var SID="([0-9a-f]+)"', d.page_source).group(1)
    d.get(f"https://ejudge.kz/new-client?SID={sid}&action=137")
    time.sleep(1.5)
    d.save_screenshot(str(SHOTS / "03_problem_summary.png"))
    for i, letter in enumerate("abcdefghij", start=1):
        d.get(f"https://ejudge.kz/new-client?SID={sid}&action=139&prob_id={i}")
        time.sleep(1.2)
        d.save_screenshot(str(SHOTS / f"04_submit_page_{letter}.png"))
finally:
    d.quit()
print("saved to", SHOTS)
