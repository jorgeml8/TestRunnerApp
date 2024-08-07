import logging
from flask import Flask, render_template, request
from tests import test_uat, test_prd

# Configurar el logging
logging.basicConfig(
    filename='test_runner.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run_test', methods=['POST'])
def run_test():
    environment = request.form['environment']
    result = []

    logging.info(f"Iniciando prueba en el entorno {environment.upper()}")

    if environment == 'uat':
        result = test_uat.run_test()
    elif environment == 'prd':
        result = test_prd.run_test()

    logging.info(f"Resultado de la prueba en {environment.upper()}: {result}")

    return render_template('index.html', results=result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
