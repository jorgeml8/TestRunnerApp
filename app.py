import logging
import json
import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from tests import test_uat, test_prd, test2_uat

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

# Read the version.json file
with open('version.json', 'r') as file:
    version_data = json.load(file)
    app_version = version_data['version']

@app.route('/testrunner/')
def index():
    return render_template('index.html', version=app_version)

@app.route('/testrunner/run_test', methods=['POST'])
def start_test():
    environment = request.form['environment']

    logging.info(f"Starting test in: {environment.upper()}")
    # Start the test in a background task to avoid blocking the main thread
    socketio.start_background_task(run_test_task, environment)

    return jsonify({'status': 'Test started'})

@app.route('/download/<filename>')
def download_file(filename):
    try:
        return send_from_directory(RESULTS_DIR, filename, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 404

def run_test_task(environment):
    result = None
    if environment == 'uat':
        result = test_uat.run_test(socketio)
    elif environment == 'prd':
        result = test_prd.run_test(socketio)

    logging.info(f"Test results in: {environment.upper()}: {result}")
    # Optionally, emit the final result
    socketio.emit('test_result', {'result': result})

if __name__ == '__main__':
    # Run the app with SocketIO
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
