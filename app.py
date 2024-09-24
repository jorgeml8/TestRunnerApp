import logging
import json
import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from tests import test_uat, test_prd, test2_uat
<<<<<<< HEAD
from threading import Event
=======
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
>>>>>>> parent of 0f9e21b (100% functional)

# Configure logging
logging.basicConfig(
    filename='logs/test_runner.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

# Create the Flask app and set up the static folder
app = Flask(__name__, static_folder='public', static_url_path='/testrunner/static')
socketio = SocketIO(app, cors_allowed_origins="*")

# Define the results directory
RESULTS_DIR = os.path.join(os.getcwd(), 'resultsUAT')

<<<<<<< HEAD
# Path to the version.json file and credentials.json
script_dir = os.path.dirname(os.path.abspath(__file__))
credentials_file = os.path.join(script_dir, 'credentials.json')

# Event to control test execution
stop_event = Event()

# Load app version from version.json
with open(os.path.join(script_dir, 'version.json'), 'r') as file:
=======
# Read the version.json file
with open('version.json', 'r') as file:
>>>>>>> parent of 0f9e21b (100% functional)
    version_data = json.load(file)
    app_version = version_data['version']

@app.route('/testrunner/')
def index():
    return render_template('index.html', version=app_version)

@app.route('/testrunner/run_test', methods=['POST'])
<<<<<<< HEAD
def run_test():
    stop_event.clear()
    environment = request.form.get('environment')
    
    logging.info(f"Starting test in: {environment.upper()}")
=======
def start_test():
    environment = request.form['environment']

    logging.info(f"Starting test in: {environment.upper()}")
    # Start the test in a background task to avoid blocking the main thread
>>>>>>> parent of 0f9e21b (100% functional)
    socketio.start_background_task(run_test_task, environment)
    
    return jsonify({'status': 'Test completed'}), 200

@app.route('/testrunner/stop_test', methods=['POST'])
def stop_test():
    # Set the stop event to signal the test to stop
    stop_event.set()
    logging.info('Stop signal received')
    return jsonify({'status': 'Test stopping'}), 200

<<<<<<< HEAD
=======
    return jsonify({'status': 'Test started'})
>>>>>>> parent of 0f9e21b (100% functional)

@app.route('/download/<filename>')
def download_file(filename):
    try:
        return send_from_directory(RESULTS_DIR, filename, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 404

def run_test_task(environment):
<<<<<<< HEAD
    try:
        # Clear any previous stop signal before starting the test
        stop_event.clear()

        if environment == 'uat':
            # Check if stop_event is set before starting each test
            if stop_event.is_set():
                logging.info("Test stopped in UAT")
                socketio.emit('test_result', {'result': 'Test stopped'})
                return
            
            result = test_uat.run_test(socketio)   # UAT test 1
            
            if stop_event.is_set():
                logging.info("Test stopped after UAT test 1")
                socketio.emit('test_result', {'result': 'Test stopped'})
                return
            
            result = test2_uat.run_test(socketio)  # UAT test 2
            
        elif environment == 'prd':
            if stop_event.is_set():
                logging.info("Test stopped in PRD")
                socketio.emit('test_result', {'result': 'Test stopped'})
                return
            
            result = test_prd.run_test(socketio)   # PRD test
=======
    result = None
    if environment == 'uat':
        result = test_uat.run_test(socketio)
        result2 = test2_uat.run_test(socketio)
    elif environment == 'prd':
        result = test_prd.run_test(socketio)
>>>>>>> parent of 0f9e21b (100% functional)

    logging.info(f"Test results in: {environment.upper()}: {result}")
    logging.info(f"Test results in: {environment.upper()}: {result2}")
    # Optionally, emit the final result
    socketio.emit('test_result', {'result': result})
    socketio.emit('test_result', {'result': result2})


if __name__ == '__main__':
    # Run the app with SocketIO
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
