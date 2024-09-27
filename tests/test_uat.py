import json
import os
import logging
import pandas as pd
from datetime import datetime
from selenium import webdriver
from flask_socketio import SocketIO, emit
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

def run_test(socketio, stop_event):
    with open('config/config.json') as config_file:
        config = json.load(config_file)

    prd_configs = config["uat"]
    selenium_url = os.getenv('SELENIUM_URL', 'http://localhost:4444/wd/hub')

    download_dir = os.path.join(os.getcwd(), 'downloads')  # Set your download directory

    # Set Chrome options to enable automatic downloads
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--headless')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')

    # Configure download settings
    prefs = {
        "download.default_directory": download_dir,  # Set the download directory
        "download.prompt_for_download": False,        # Disable download prompt
        "directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    options.add_experimental_option("prefs", prefs)

    # Connect to Selenium service
    driver = webdriver.Remote(
        command_executor=selenium_url,
        options=options
    )
    results = []

    try:
        for prd_config in prd_configs:
            if stop_event.is_set():  # Check if the test should be stopped
                log_message = "Test execution has been stopped."
                logging.info(log_message)
                socketio.emit('log_message', {'message': log_message})
                break

            log_message = f"Starting test in: {prd_config['url']} - {prd_config['comment']}"
            logging.info(log_message)
            socketio.emit('log_message', {'message': log_message})
            results.append(log_message)

            driver.get(prd_config["url"])
            driver.maximize_window()

            try:
                username_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "username"))
                )
                password_field = driver.find_element(By.NAME, "password")
                login_button = driver.find_element(By.CSS_SELECTOR, 'input[type="submit"][value="Log in"]')

                username_field.send_keys(prd_config["username"])
                password_field.send_keys(prd_config["password"])
                login_button.click()

                # Save all the links on a list
                all_links = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.TAG_NAME, 'a'))
                )

                links_to_test = []
                for link in all_links:
                    href = link.get_attribute('href')
                    if href:
                        links_to_test.append((link.text, href))

                for index, (link_text, href) in enumerate(links_to_test):
                    if stop_event.is_set():
                        log_message = "Test execution has been stopped."
                        logging.info(log_message)
                        socketio.emit('log_message', {'message': log_message})
                        break

                    log_message = f"Clicking on link: '{link_text}' with href: '{href}'"
                    logging.info(log_message)
                    socketio.emit('log_message', {'message': log_message})
                    driver.get(href)

                    # Wait for the page to fully load before checking for elements
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

                    # Emit progress update
                    progress = (index + 1) / len(links_to_test) * 100
                    socketio.emit('update_progress', {'progress': progress})

            except Exception as e:
                error_message = f"Error during test: {e}"
                logging.error(error_message)
                socketio.emit('log_message', {'message': error_message})
                results.append(error_message)

    finally:
        # Save results
        df = pd.DataFrame(results)
        results_dir = os.path.join(os.getcwd(), 'resultsUAT')
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)

        # Save results to CSV
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'results_{timestamp}.csv'
        file_path = os.path.join(results_dir, filename)

        df.to_csv(file_path, index=False)
        log_message = f"Results saved to {file_path}"
        logging.info(log_message)
        socketio.emit('log_message', {'message': log_message})

        # Send the filename back to the client to allow download
        socketio.emit('file_ready', {'filename': filename})

        driver.quit()  # Ensure driver quits when done
        log_message = "Test completed."
        logging.info(log_message)
        socketio.emit('log_message', {'message': log_message})

    return results
