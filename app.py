import logging
import json
from flask import Flask, render_template, request
from tests import test_uat, test_prd

# Configurar el logging
logging.basicConfig(
    filename='logs/test_runner.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

# Crear la aplicación Flask y especificar la carpeta para archivos estáticos
app = Flask(__name__, static_folder='public', static_url_path='/testrunner/static')

# Leer el archivo version.json
with open('version.json', 'r') as file:
    version_data = json.load(file)
    app_version = version_data['version']

@app.route('/testrunner/')
def index():
    return render_template('index.html', version=app_version)

@app.route('/testrunner/run_test', methods=['POST'])
def run_test():
    environment = request.form['environment']
    result = []

    logging.info(f"Iniciando prueba en el entorno {environment.upper()}")

    if environment == 'uat':
        result = test_uat.run_test()
    elif environment == 'prd':
        result = test_prd.run_test()

    logging.info(f"Resultado de la prueba en {environment.upper()}: {result}")

    return render_template('index.html', results=result, version=app_version)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
