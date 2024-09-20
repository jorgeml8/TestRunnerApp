import os
import json
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException
from flask_socketio import SocketIO

# Load credentials once at startup
CREDENTIALS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials.json')

def load_credentials():
    try:
        with open(CREDENTIALS_FILE, 'r') as f:
            credentials = json.load(f)
        return credentials['pages']
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Error loading credentials: {e}")
        return []

def log_and_emit(socketio, log_message):
    logging.info(log_message)
    socketio.emit('log_message', {'message': log_message})

def click_element(driver, locator, socketio, action_desc, timeout=10):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable(locator)
        )
        element.click()
        log_and_emit(socketio, f"{action_desc} clicked successfully")
    except (TimeoutException, ElementNotInteractableException) as e:
        log_and_emit(socketio, f"Error clicking {action_desc}: {e}")
        return False
    return True

def terminal_login(driver, url, username, password, socketio):
    driver.get(url)
    log_and_emit(socketio, "Starting terminal station test. Waiting for page to load.")
    
    try:
        element = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, 'locked-btn-kblogin')))
        log_and_emit(socketio, "Found window lock element")
        
        if "Keyboard Login [ALT-L]" in element.text:
            log_and_emit(socketio, "AMS is locked, proceeding with login attempt")
            element.click()

            username_field = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "badgeno-login-input")))
            password_field = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "badgeno-login-check")))
            username_field.send_keys(username)
            password_field.send_keys(password)
            log_and_emit(socketio, "Entered username and password")

            if not click_element(driver, (By.XPATH, "//button[.//span[text()='Go']]"), socketio, "Submit button"):
                return

            if not click_element(driver, (By.XPATH, "//button[span[text()='Yes']]"), socketio, "Confirmation button"):
                return
        else:
            log_and_emit(socketio, "AMS is not locked, no login required")
    
    except TimeoutException:
        log_and_emit(socketio, "Timed out while checking AMS lock, [not found]")
        return

    try:
        title_element = driver.find_element(By.ID, "terminal_title_header")
        if "Match" in title_element.text:
            terminal_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "terminal_input")))
            terminal_input.send_keys("Error-triggering content" + Keys.ENTER)

            WebDriverWait(driver, 4).until(EC.presence_of_element_located((By.ID, "terminal_x")))
            log_and_emit(socketio, "Parts match logic working fine!")
    except TimeoutException:
        log_and_emit(socketio, "Timed out during terminal input")


def run_test(socketio):
    pages = load_credentials()
    selenium_url = os.getenv('SELENIUM_URL', 'http://localhost:4444/wd/hub')

    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--incognito')

    with webdriver.Remote(command_executor=selenium_url, options=options) as driver:
        for page in pages:
            log_and_emit(socketio, f"Testing page: {page['url']}")
            terminal_login(driver, page['url'], page['username'], page['password'], socketio)

if __name__ == "__main__":
    socketio = SocketIO(message_queue='redis://')
    run_test(socketio)
