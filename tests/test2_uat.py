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

# Current directory of the script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Move up one directory level to acces the project root
project_root = os.path.abspath(os.path.join(script_dir, '..'))


## This test focuses on login into a terminal, inputting a random value and expecting the terminal to reject the input data.

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
    socketio.emit('log_message', {'message': log_message}) 

    ### This element tell us if AMS requires a password for showing the terminal content or 
    ### the cookies already did the job for us
    element = driver.find_element("xpath", '//span[@id="ui-id-2" and @class="ui-dialog-title"]')

    if element.text == "AMS is locked":
        log_message = "AMS is locked, proceeding with login attempt"
        logging.info(log_message)
        socketio.emit('log_message', {'message': log_message})
        try:
            # Find and click the login button
            login_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "ui-button-text"))
            )
            login_button.click()
            print("Login button clicked")
        except TimeoutException:
            log_message = "Timed out waiting for login button"
            logging.info(log_message)
            socketio.emit('log_message', {'message': log_message})
            return  # Exit the function if login button was not found
        except ElementNotInteractableException:
            log_message = print("Login button not interactable")
            logging.info(log_message)
            socketio.emit('log_message', {'message': log_message})
            return

        # Wait for the input fields to appear and interact with them
        try:
            username_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "badgeno-login-input"))
            )
            password_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "badgeno-login-check"))
            )

            username_field.send_keys(username)
            password_field.send_keys(password)
            log_message = "Entered username and password"
            logging.info(log_message)
            socketio.emit('log_message', {'message': log_message})

        except TimeoutException:
            log_message = "Timed out waiting for username or password field"
            logging.info(log_message)
            socketio.emit('log_message', {'message': log_message})
            return

        # Find and click the submit button
        try:
            submit_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='Go']]"))
            )
            submit_button.click()
            log_message = "Submit button clicked"
            logging.info(log_message)
            socketio.emit('log_message', {'message': log_message})

        except TimeoutException:
            log_message = "Timed out waiting for submit button"
            logging.info(log_message)
            socketio.emit('log_message', {'message': log_message})
            return

        # Confirm login by clicking the "Yes" button
        try:
            confirm_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[span[text()='Yes']]"))
            )
            confirm_button.click()
            log_message = "User confirmation button clicked. Log in successful"
            logging.info(log_message)
            socketio.emit('log_message', {'message': log_message})


        except TimeoutException:
            log_message = "Timed out waiting for confirmation button"
            logging.info(log_message)
            socketio.emit('log_message', {'message': log_message})
            return
    else:
        pass

    # Now that we are in the terminal, we start looking for any information regarding the content of the page
    # If it is a parts-match page: We will look for the word 'Match' in the terminal title
    title_element = driver.find_element("id","terminal_title_header")
    terminal_content = "This should create an error when being input in the terminal"
    if "Match" in title_element.text:
        terminal_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "terminal_input"))
        )
        terminal_input.send_keys(terminal_content + Keys.ENTER)
        # Now, we wait for the 'X' to show in the screen
        x_element = WebDriverWait(driver,4).until(
            EC.presence_of_element_located((By.ID, "terminal_x"))
        )
        if x_element:
            log_message = "Parts match logic working fine!"
            logging.info(log_message)
            socketio.emit('log_message', {'message': log_message})
    
    # Wait for the table to be loaded on the page
    try:
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table.table.tableFixHead.table-bordered.mb-0"))
        )
        print("Table found successfully !!")
    except TimeoutException:
        print("Timed out waiting for the table to load")
    except Exception as e:
        print(f"Error occurred on page: {url}: {e}")

def run_bot(driver, credentials_file):
    pages = load_credentials(credentials_file)

    for page in pages:
        print(f"Testing page: {page['url']}")
        terminal_login(driver, page['url'], page['username'], page['password'])
        time.sleep(5)  # Add a delay between pages for stability

        # You can add logic to close the browser or return to a starting point if necessary


if __name__ == "__main__":
    # Path to the JSON credentials file
    credentials_file = os.path.join(project_root, 'credentials', 'credentials.json')
    socketio = SocketIO(message_queue='redis://')
    result = run_test(socketio)
    for line in result:
        print(line)
