import json
import logging
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

def run_test():
    with open('config/config.json') as config_file:
        config = json.load(config_file)
    
    uat_configs = config["uat"]
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--headless')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.binary_location = '/usr/bin/google-chrome'  # Asegúrate de que la ruta sea correcta

    driver = webdriver.Chrome(options=options)
    results = []

    for uat_config in uat_configs:
        logging.info(f"Iniciando prueba en {uat_config['url']} - {uat_config['comment']}")
        results.append(f"Iniciando prueba en {uat_config['url']} - {uat_config['comment']}")
        driver.get(uat_config["url"])
        driver.maximize_window()

        try:
            # Iniciar sesión
            username_field = driver.find_element_by_name("username")
            password_field = driver.find_element_by_name("password")
            login_button = driver.find_element_by_css_selector('input[type="submit"][value="Log in"]')
            
            username_field.send_keys(uat_config["username"])
            password_field.send_keys(uat_config["password"])
            login_button.click()

            # Capturar todos los enlaces
            all_links = driver.find_elements_by_tag_name('a')
            links_to_test = []
            logging.info(f"Encontrados {len(all_links)} enlaces en la página.")
            for link in all_links:
                href = link.get_attribute('href')
                link_text = link.text
                if href:
                    links_to_test.append((link_text, href))
                    logging.info(f"Enlace encontrado: texto='{link_text}', href='{href}'")

            # Interactuar con los enlaces capturados
            for link_text, href in links_to_test:
                try:
                    logging.info(f"Clic en el enlace con texto '{link_text}' y href: {href}")
                    results.append(f"Clic en el enlace con texto '{link_text}' y href: {href}")
                    driver.get(href)
                    driver.back()
                    results.append(f"Link '{href}' tested successfully.")
                except Exception as e:
                    error_message = f"Error al probar el enlace con texto '{link_text}' y href: {href}: {e}"
                    logging.error(error_message)
                    results.append(error_message)

            logging.info(f"Prueba completada con éxito para {uat_config['url']}")
            results.append(f"Prueba completada con éxito para {uat_config['url']}")

        except Exception as e:
            error_message = f"Error durante la prueba en {uat_config['url']}: {e}"
            logging.error(error_message)
            results.append(error_message)
        
    driver.quit()
    return results

# Ejecutar la prueba manualmente
if __name__ == "__main__":
    result = run_test()
    for line in result:
        print(line)
