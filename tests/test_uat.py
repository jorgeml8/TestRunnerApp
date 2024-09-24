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
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException

# Global variable to control the test execution
stop_test = False

# Create SocketIO instance
socketio = SocketIO(message_queue='redis://')

def run_test(socketio):
    global stop_test  # Use the global variable to control execution
    with open('config/config.json') as config_file:
        config = json.load(config_file)

    prd_configs = config["uat"]
    selenium_url = os.getenv('SELENIUM_URL', 'http://localhost:4444/wd/hub')

    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--headless')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')

    # Connect to Selenium service
    driver = webdriver.Remote(
        command_executor=selenium_url,
        options=options
    )
    results = []

    for prd_config in prd_configs:
        if stop_test:  # Check if the test should be stopped
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
            # Log in process
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
            log_message = f"{len(all_links)} clickable links found."
            logging.info(log_message)
            socketio.emit('log_message', {'message': log_message})
            results.append(log_message)
            for link in all_links:
                href = link.get_attribute('href')
                link_text = link.text
                if href:
                    links_to_test.append((link_text, href))
                    log_message = f"Link found: texto='{link_text}', href='{href}'"
                    logging.info(log_message)
                    socketio.emit('log_message', {'message': log_message})

            total_links = len(links_to_test)
            data = []  # List to store row data

            for index, (link_text, href) in enumerate(links_to_test):
                if stop_test:  # Check if the test should be stopped
                    log_message = "Test execution has been stopped."
                    logging.info(log_message)
                    socketio.emit('log_message', {'message': log_message})
                    break

                try:
                    log_message = f"Click on  '{link_text}' with 'href': {href}"
                    logging.info(log_message)
                    socketio.emit('log_message', {'message': log_message})
                    results.append(log_message)
                    driver.get(href)

                    # Wait for the page to fully load before checking for elements
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, 'body'))
                    )

                    # Check for breadcrumbs
                    breadcrumbs_status = 'NOT FOUND'
                    content_status = 'NOT FOUND'
                    try:
                        breadcrumbs = driver.find_element(By.CLASS_NAME, 'breadcrumbs')
                        breadcrumbs_status = 'FOUND'
                    except NoSuchElementException:
                        breadcrumbs_status = 'NOT FOUND'

                    # Check for content div
                    try:
                        content_div = driver.find_element(By.ID, 'content')
                        content_status = 'FOUND'
                        # Check for header
                        try:
                            h1_header = content_div.find_element(By.TAG_NAME, 'h1')
                            h1_status = 'FOUND'
                        except NoSuchElementException:
                            h1_status = 'NOT FOUND'

                    except NoSuchElementException:
                        content_status = 'NOT FOUND'

                    data.append({
                        'Link': href,
                        'Status': 'SUCCESS',
                        'Breadcrumbs': breadcrumbs_status,
                        'Content Div': content_status,
                        'H1 Header': h1_status,
                        'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })

                except Exception as e:
                    error_message = f"Error when clicking on '{link_text}' with 'href': {href}: {e}"
                    logging.error(error_message)
                    socketio.emit('log_message', {'message': error_message})
                    results.append(error_message)
                    data.append({
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
            error_message = f"Testing error in: {prd_config['url']}: {e}"
            logging.error(error_message)
            socketio.emit('log_message', {'message': error_message})
            results.append(error_message)

    # Save results
    df = pd.DataFrame(data)
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

    driver.quit()
    return results

@socketio.on('reset')
def handle_reset():
    global stop_test  # Use the global variable to control execution
    stop_test = True
    logging.info("Test reset initiated.")

if __name__ == "__main__":
    socketio = SocketIO(message_queue='redis://')
    run_test(socketio)  # Call the test function to start execution
