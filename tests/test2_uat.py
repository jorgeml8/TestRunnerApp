import os
import json
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException
import time

# Set up logging
logging.basicConfig(level=logging.INFO)

# Current directory of the script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Path to the JSON credentials file (same directory as the script)
credentials_file = os.path.join(script_dir, 'credentials.json')

## This test focuses on login into a terminal, inputting a random value, and expecting the terminal to reject the input data.

# Function to load credentials from JSON file
def load_credentials(file_path):
    with open(file_path, 'r') as f:
        credentials = json.load(f)
    return credentials['pages']

def terminal_login(driver, url, username, password):
    driver.get(url)
    time.sleep(2)
    log_message = "Starting terminal station test"
    logging.info(log_message)

    try:
        element = driver.find_element(By.XPATH, '//span[@id="ui-id-2" and @class="ui-dialog-title"]')
        if element.text == "AMS is locked":
            logging.info("AMS is locked, proceeding with login attempt")

            # Handle login button click
            try:
                login_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "ui-button-text"))
                )
                login_button.click()
                logging.info("Login button clicked")
            except (TimeoutException, ElementNotInteractableException) as e:
                logging.error(f"Error with login button: {e}")
                return

            # Input credentials
            try:
                username_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "badgeno-login-input"))
                )
                password_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "badgeno-login-check"))
                )

                username_field.send_keys(username)
                password_field.send_keys(password)
                logging.info("Entered username and password")

            except TimeoutException:
                logging.error("Timed out waiting for username or password field")
                return

            # Handle submit button click
            try:
                submit_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='Go']]"))
                )
                submit_button.click()
                logging.info("Submit button clicked")

            except TimeoutException:
                logging.error("Timed out waiting for submit button")
                return

            # Handle confirmation button click
            try:
                confirm_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[span[text()='Yes']]"))
                )
                confirm_button.click()
                logging.info("User confirmation button clicked. Log in successful")

            except TimeoutException:
                logging.error("Timed out waiting for confirmation button")
                return

        # Now that we are in the terminal, look for terminal content
        title_element = driver.find_element(By.ID, "terminal_title_header")
        terminal_content = "This should create an error when being input in the terminal"
        if "Match" in title_element.text:
            terminal_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "terminal_input"))
            )
            terminal_input.send_keys(terminal_content + Keys.ENTER)
            # Wait for the 'X' to appear
            try:
                x_element = WebDriverWait(driver, 4).until(
                    EC.presence_of_element_located((By.ID, "terminal_x"))
                )
                if x_element:
                    logging.info("Parts match logic working fine!")
            except TimeoutException:
                logging.error("Timed out waiting for 'X' element")
    except Exception as e:
        logging.error(f"Error occurred during terminal login process: {e}")

    # Wait for the table to load
    try:
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table.table.tableFixHead.table-bordered.mb-0"))
        )
        logging.info("Table found successfully!")
    except TimeoutException:
        logging.error("Timed out waiting for the table to load")
    except Exception as e:
        logging.error(f"Error occurred on page: {url}: {e}")
        
def run_test(driver, credentials_file):
    pages = load_credentials(credentials_file)

    for page in pages:
        try:
            print(f"Testing page: {page['url']}")
            terminal_login(driver, page['url'], page['username'], page['password'])
            time.sleep(5)  # Add a delay between pages for stability
        except:
            print("error")

if __name__ == "__main__":
    # Set up the webdriver (e.g., ChromeDriver)
    options = Options()
    options.add_argument('--headless')  # Run headless if you don't need a GUI
    driver = webdriver.Chrome(options=options)
    
    try:
        # Run the bot
        run_test(driver, credentials_file)
    finally:
        driver.quit()  # Ensure to close the browser once done
