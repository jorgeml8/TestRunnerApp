from flask import Flask, render_template, request
from selenium import webdriver
from tests import test_uat, test_prod

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run_test', methods=['POST'])
def run_test():
    environment = request.form['environment']
    result = ""

    if environment == 'uat':
        result = test_uat.run_test()
    elif environment == 'prod':
        result = test_prod.run_test()

    return f"Resultado de la prueba en {environment.upper()}: {result}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
