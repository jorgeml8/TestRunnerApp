import logging
import json
import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from tests import test_uat, test_prd, test2_uat  # Updated import for tests
import threading

# Configure logging
logging.basicConfig(
    filename='logs/test_runner.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

# Flask app setup
app = Flask(__name__, static_folder='public', static_url_path='/testrunner/static')
socketio = SocketIO(app, cors_allowed_origins="*")

# Directory for results
RESULTS_DIR = os.path.join(os.getcwd(), 'resultsUAT')

# Path to the version.json file and credentials.json
script_dir = os.path.dirname(os.path.abspath(__file__))
credentials_file = os.path.join(script_dir, 'credentials.json')

# Global variables to manage the test process
test_thread = None
stop_test_flag = False

# Load app version from version.json
with open(os.path.join(script_dir, 'version.json'), 'r') as file:
    version_data = json.load(file)
    app_version = version_data.get('version', '1.3.0')

# Routes
@app.route('/testrunner/')
def index():
    return render_template('index.html', version=app_version)

@app.route('/testrunner/run_test', methods=['POST'])
def start_test():
    environment = request.form.get('environment', '').lower()
    global stop_test_flag
    stop_test_flag = False  # Reset the stop flag at the start of a new test
    if environment not in ['uat', 'prd']:
        return jsonify({'error': 'Invalid environment'}), 400

    logging.info(f"Starting test in: {environment.upper()}")

    # Run the test in the background
    socketio.start_background_task(run_test_task, environment)

    return jsonify({'status': f'Test in {environment.upper()} started'})

# Function that runs the test and checks the stop flag periodically
def run_test_task(environment):
    global stop_test_flag

    try:
        # Run test and periodically check if the test was stopped
        if environment == 'uat':
            result = test_uat.run_test(socketio, stop_test_flag_callback)
        elif environment == 'prd':
            result = test_prd.run_test(socketio, stop_test_flag_callback)

        # Only emit completion message if not stopped
        if not stop_test_flag:
            logging.info(f"Test in {environment.upper()} completed: {result}")
            socketio.emit('test_result', {'result': result})

    except Exception as e:
        logging.error(f"Error running test for {environment.upper()}: {e}")
        socketio.emit('test_result', {'error': str(e)})
    finally:
        if stop_test_flag:
            logging.info(f"Test in {environment.upper()} was stopped.")
            socketio.emit('test_result', {'error': 'Test was stopped by the user.'})

# A callback function that can be passed to the tests to stop them
def stop_test_flag_callback():
    global stop_test_flag
    return stop_test_flag

# Socket.IO event for stopping the test
@socketio.on('stop_test')
def handle_stop_test():
    global stop_test_flag
    stop_test_flag = True  # Set the flag to stop the test
    logging.info("Stop signal received via Socket.IO, stopping the test...")
    emit('log_message', {'message': 'Stop test signal received.'})

# HTTP route for stopping the test
@app.route('/stop_test', methods=['POST'])
def stop_test():
    global stop_test_flag
    stop_test_flag = True  # Set the flag to stop the test
    logging.info("Stop signal received via HTTP, stopping the test...")
    return jsonify({'status': 'Test stopped'})

@app.route('/download/<filename>')
def download_file(filename):
    try:
        return send_from_directory(RESULTS_DIR, filename, as_attachment=True)
    except Exception as e:
        logging.error(f"Error downloading file: {e}")
        return jsonify({"error": str(e)}), 404

if __name__ == '__main__':
    # Start the Flask app with SocketIO
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
