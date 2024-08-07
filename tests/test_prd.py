import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

def run_test():
    with open('/config/config.json') as config_file:
        config = json.load(config_file)
    
    uat_config = config["uat"]
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--headless')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Remote(
        command_executor='http://selenium-chrome:4444/wd/hub',
        options=options
    )
    driver.get(uat_config["url"])
    driver.maximize_window()

    try:
        for path in uat_config["paths"]:
            driver.get(f"{uat_config['url']}{path}")
            search_box = driver.find_element(By.NAME, "q")
            search_box.send_keys("Selenium testing")
            search_box.send_keys(Keys.RETURN)
            time.sleep(3)

            results = driver.find_elements(By.CSS_SELECTOR, ".result")
            assert len(results) > 0, f"No se encontraron resultados en {path}."

        return "Prueba completada con éxito."
    
    except Exception as e:
        return f"Error durante la prueba: {e}"
    
    finally:
        driver.quit()
