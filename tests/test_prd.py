import json
import os
import logging
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

def run_test():
    with open('config/config.json') as config_file:
        config = json.load(config_file)
    
    prd_configs = config["prd"]

    # Obtener la URL del Selenium Server del entorno
    selenium_url = os.getenv('SELENIUM_URL', 'http://localhost:4444/wd/hub')

    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--headless')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    #options.binary_location = '/usr/bin/google-chrome'  # Asegurarse que la ruta sea correcta

    #driver = webdriver.Chrome(options=options) # No se usa cuando se usa el container de Selenium
      # Conectar al Selenium Server remoto
    driver = webdriver.Remote(
        command_executor=selenium_url,
        options=options
    )
    results = []

    for prd_config in prd_configs:
        logging.info(f"Starting test on {prd_config['url']} - {prd_config['comment']}")
        results.append(f"Starting test on {prd_config['url']} - {prd_config['comment']}")
        driver.get(prd_config["url"])
        driver.maximize_window()

        try:
            # Iniciar sesión
            username_field = driver.find_element_by_name("username")
            password_field = driver.find_element_by_name("password")
            login_button = driver.find_element_by_css_selector('input[type="submit"][value="Log in"]')
            
            username_field.send_keys(prd_config["username"])
            password_field.send_keys(prd_config["password"])
            login_button.click()

            # Capturar todos los enlaces
            all_links = driver.find_elements_by_tag_name('a')
            links_to_test = []
            logging.info(f"Links {len(all_links)} found on the page.")
            for link in all_links:
                href = link.get_attribute('href')
                link_text = link.text
                if href:
                    links_to_test.append((link_text, href))
                    logging.info(f"Link found: texto='{link_text}', href='{href}'")

            # Interactuar con los enlaces capturados
            for link_text, href in links_to_test:
                try:
                    logging.info(f"Click on the link with text '{link_text}' and href: {href}")
                    results.append(f"Click on the link with text '{link_text}' and href: {href}")
                    driver.get(href)
                    driver.back()
                    results.append(f"Link '{href}' tested successfully.")
                except Exception as e:
                    error_message = f"Error testing the link with text '{link_text}' and href: {href}: {e}"
                    logging.error(error_message)
                    results.append(error_message)

            logging.info(f"Starting test onTest successfully completed for {prd_config['url']}")
            results.append(f"Starting test onTest successfully completed for {prd_config['url']}")

        except Exception as e:
            error_message = f"Error during the test on {prd_config['url']}: {e}"
            logging.error(error_message)
            results.append(error_message)
        
    driver.quit()
    return results

# Ejecutar la prueba manualmente
if __name__ == "__main__":
    result = run_test()
    for line in result:
        print(line)
