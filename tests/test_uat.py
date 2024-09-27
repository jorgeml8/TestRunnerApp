import json
import os
import logging
import time
from datetime import datetime
from selenium import webdriver
from flask_socketio import SocketIO
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

def run_test(socketio, stop_test_flag):
    """
    Run the UAT test using Selenium and Flask-SocketIO.
    :param socketio: The SocketIO instance for emitting events.
    :param stop_test_flag: A callable that returns True if the test should stop.
    :return: List of results from the test execution.
    """
    
    # Load configuration
    with open('config/config.json') as config_file:
        config = json.load(config_file)

    uat_configs = config["uat"]
    selenium_url = os.getenv('SELENIUM_URL', 'http://localhost:4444/wd/hub')

    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--headless')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')

    driver = webdriver.Remote(command_executor=selenium_url, options=options)

    results = []

    try:
        for uat_config in uat_configs:
            if stop_test_flag():  # Check if the test should stop
                logging.info("Test stopped by user.")
                socketio.emit('log_message', {'message': "Test stopped by user."})
                break  # Exit loop if stop is requested

            log_message = f"Starting test in: {uat_config['url']} - {uat_config['comment']}"
            logging.info(log_message)
            socketio.emit('log_message', {'message': log_message})
            results.append(log_message)

            driver.get(uat_config["url"])
            driver.maximize_window()

            # Log in process
            if stop_test_flag(): break  # Stop before login
            username_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            password_field = driver.find_element(By.NAME, "password")
            login_button = driver.find_element(By.CSS_SELECTOR, 'input[type="submit"][value="Log in"]')

            username_field.send_keys(uat_config["username"])
            password_field.send_keys(uat_config["password"])
            login_button.click()

            if stop_test_flag(): break  # Stop after login

            # Save all the links on a list
            all_links = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, 'a'))
            )
            if stop_test_flag(): break
            links_to_test = []
            log_message = f"{len(all_links)} clickable links found."
            logging.info(log_message)
            socketio.emit('log_message', {'message': log_message})
            results.append(log_message)

            for link in all_links:
                if stop_test_flag(): break
                href = link.get_attribute('href')
                link_text = link.text
                if href:
                    links_to_test.append((link_text, href))
                    log_message = f"Link found: text='{link_text}', href='{href}'"
                    logging.info(log_message)
                    socketio.emit('log_message', {'message': log_message})

            total_links = len(links_to_test)

            for index, (link_text, href) in enumerate(links_to_test):
                if stop_test_flag():
                    break

                try:
                    log_message = f"Clicking on '{link_text}' with 'href': {href}"
                    logging.info(log_message)
                    socketio.emit('log_message', {'message': log_message})
                    results.append(log_message)
                    driver.get(href)

                    # Wait for the page to fully load before checking for elements
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, 'body'))
                    )
                    if stop_test_flag():
                        break

                    # Check for breadcrumbs and content status
                    breadcrumbs_status = 'NOT FOUND'
                    content_status = 'NOT FOUND'
                    h1_status = 'NOT FOUND'

                    # Check for breadcrumbs
                    try:
                        breadcrumbs = driver.find_element(By.CLASS_NAME, 'breadcrumbs')
                        breadcrumbs_status = 'FOUND'
                    except NoSuchElementException:
                        breadcrumbs_status = 'NOT FOUND'

                    # Check for content div
                    try:
                        content_div = driver.find_element(By.ID, 'content')
                        content_status = 'FOUND'
                        try:
                            h1_header = content_div.find_element(By.TAG_NAME, 'h1')
                            h1_status = 'FOUND'
                        except NoSuchElementException:
                            h1_status = 'NOT FOUND'
                    except NoSuchElementException:
                        content_status = 'NOT FOUND'

                    # Log the results
                    results.append({
                        'Link': href,
                        'Status': 'SUCCESS',
                        'Breadcrumbs': breadcrumbs_status,
                        'Content Div': content_status,
                        'H1 Header': h1_status,
                        'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })

                except Exception as e:
                    error_message = f"Error clicking on '{link_text}' with 'href': {href}: {e}"
                    logging.error(error_message)
                    socketio.emit('log_message', {'message': error_message})
                    results.append({
                        'Link': href,
                        'Status': 'FAIL',
                        'Breadcrumbs': 'N/A',
                        'Content Div': 'N/A',
                        'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })

                # Emit progress update
                progress = (index + 1) / total_links * 100
                socketio.emit('update_progress', {'progress': progress})

                # Go back to the previous page
                driver.back()

    except Exception as e:
        logging.error(f"Unexpected error occurred: {e}")
        socketio.emit('log_message', {'message': f"Unexpected error occurred: {e}"})

    finally:
        driver.quit()  # Ensure the WebDriver is quit even if the test is stopped

    return results

if __name__ == "__main__":
    socketio = SocketIO(message_queue='redis://')
    result = run_test(socketio, lambda: False)  # Replace lambda with a proper stop flag if needed
    for line in result:
        print(line)
