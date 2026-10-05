"""Submit lab-04 solutions to ejudge contest 204 via Selenium + FormData."""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / "screenshots"
SHOTS.mkdir(exist_ok=True)

LOGIN = os.environ.get("EJ_LOGIN", "ADS26_25B032234")
PASSWORD = os.environ.get("EJ_PASSWORD", "")
CONTEST = "204"
LANG_ID = "23"
letters = [x.lower() for x in (sys.argv[1:] or list("abcdefghij"))]


def make_driver() -> webdriver.Chrome:
    opts = Options()
    opts.add_argument("--window-size=1600,1000")
    opts.add_argument("--headless=new")
    return webdriver.Chrome(options=opts)


def login(driver: webdriver.Chrome) -> None:
    if not PASSWORD:
        raise SystemExit("Set EJ_PASSWORD environment variable")
    driver.get(f"https://ejudge.kz/new-client?contest_id={CONTEST}")
    time.sleep(1.2)
    driver.save_screenshot(str(SHOTS / "01_login_page.png"))
    driver.find_element(By.NAME, "login").clear()
    driver.find_element(By.NAME, "login").send_keys(LOGIN)
    driver.find_element(By.NAME, "password").clear()
    driver.find_element(By.NAME, "password").send_keys(PASSWORD)
    for sel in ("input[name=action_2]", "input[type=submit]"):
        btns = driver.find_elements(By.CSS_SELECTOR, sel)
        if btns:
            btns[0].click()
            break
    time.sleep(2.0)
    driver.save_screenshot(str(SHOTS / "02_after_login.png"))
    print("login", driver.title)


def get_sid(driver: webdriver.Chrome) -> str:
    sid = driver.execute_script(
        "var m=document.documentElement.innerHTML.match(/SID=([0-9a-fA-F]+)/); return m?m[1]:'';"
    )
    if not sid:
        sid = (parse_qs(urlparse(driver.current_url).query).get("SID") or [""])[0]
    return sid


def set_monaco(driver: webdriver.Chrome, code: str) -> str:
    return driver.execute_script(
        """
        const code = arguments[0];
        try {
          if (window.monaco && monaco.editor) {
            const models = monaco.editor.getModels();
            if (models.length) {
              models[0].setValue(code);
              return 'monaco:' + models[0].getValue().split('\\n').length;
            }
          }
        } catch (e) { return 'err:' + e; }
        return 'no-monaco';
        """,
        code,
    )


def submit_formdata(driver: webdriver.Chrome, sid: str, prob_id: int, code: str) -> str:
    return driver.execute_async_script(
        """
        const sid = arguments[0], prob = arguments[1], code = arguments[2], lang = arguments[3], done = arguments[4];
        const fd = new FormData();
        fd.append('SID', sid);
        fd.append('prob_id', String(prob));
        fd.append('lang_id', lang);
        fd.append('file', new Blob([code], {type: 'text/x-python'}), 'sol.py');
        fd.append('action_40', 'Send!');
        fetch('/new-client', {method: 'POST', body: fd, credentials: 'include'})
          .then(async r => {
            const t = await r.text();
            done(JSON.stringify({
              status: r.status,
              hasErr: /Error|Permission|denied|over/i.test(t),
              snippet: t.slice(0, 300)
            }));
          })
          .catch(e => done('ERR:' + e));
        """,
        sid,
        prob_id,
        code,
        LANG_ID,
    )


def main() -> None:
    driver = make_driver()
    try:
        login(driver)
        sid = get_sid(driver)
        print("SID", sid)
        if not sid:
            return

        driver.get(f"https://ejudge.kz/new-client?SID={sid}&action=137")
        time.sleep(1.5)
        driver.save_screenshot(str(SHOTS / "03_summary.png"))

        results = []
        for letter in letters:
            pid = ord(letter) - ord("a") + 1
            path = ROOT / letter / f"{letter}.py"
            code = path.read_text(encoding="utf-8")
            print(f"==== {letter.upper()} prob_id={pid} ====")
            driver.get(f"https://ejudge.kz/new-client?SID={sid}&action=139&prob_id={pid}")
            time.sleep(1.8)
            try:
                Select(driver.find_element(By.NAME, "lang_id")).select_by_value(LANG_ID)
            except Exception:
                pass
            inj = set_monaco(driver, code)
            fd_res = submit_formdata(driver, sid, pid, code)
            print("inject", inj, "submit", fd_res)
            driver.save_screenshot(str(SHOTS / f"04_submit_{letter}.png"))
            results.append((letter, inj, fd_res))
            time.sleep(1.0)

        driver.get(f"https://ejudge.kz/new-client?SID={sid}&action=137")
        time.sleep(2.0)
        driver.save_screenshot(str(SHOTS / "05_summary_after.png"))
        print("==== RESULTS ====")
        for row in results:
            print(row)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
