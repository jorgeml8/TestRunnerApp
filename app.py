# Import necessary libraries
import logging
import json
import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO
from tests import test_uat, test_prd, test2_uat  # Assuming test_uat is modified accordingly
from threading import Event
import time

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

# Event to control test execution (used for stopping the test)
stop_event = Event()

# Load app version from version.json
with open(os.path.join(script_dir, 'version.json'), 'r') as file:
    version_data = json.load(file)
    app_version = version_data.get('version', '1.0.0')

# Routes
@app.route('/testrunner/')
def index():
    return render_template('index.html', version=app_version)

# Route to start the test
@app.route('/testrunner/run_test', methods=['POST'])
def run_test():
    stop_event.clear()  # Clear any existing stop signal
    environment = request.form.get('environment')
    
    logging.info(f"Starting test in: {environment.upper()}")
    socketio.start_background_task(run_test_task, environment)  # Run the test in the background
    
    return jsonify({'status': 'Test started'}), 200

# Route to stop the test
@app.route('/testrunner/stop_test', methods=['POST'])
def stop_test():
    # Set the stop event to signal the test to stop
    stop_event.set()
    logging.info('Stop signal received')
    return jsonify({'status': 'Test stopping'}), 200

# Route to download a test result file
@app.route('/download/<filename>')
def download_file(filename):
    try:
        return send_from_directory(RESULTS_DIR, filename, as_attachment=True)
    except Exception as e:
        logging.error(f"Error downloading file: {e}")
        return jsonify({"error": str(e)}), 404

# Function to run the test task
def run_test_task(environment):
    try:
        # Ensure the stop event is cleared before starting
        stop_event.clear()

        # Running tests for UAT environment
        if environment == 'uat':
            for test in [test_uat, test2_uat]:
                if stop_event.is_set():  # Check if the stop event was set
                    logging.info("Test stopped during UAT")
                    socketio.emit('test_result', {'result': 'Test stopped'})
                    return

                result = test.run_test(socketio, stop_event)  # Pass the stop_event to the test function
                logging.info(f"Completed {test.__name__} in UAT: {result}")

        # Running tests for PRD environment
        elif environment == 'prd':
            if stop_event.is_set():
                logging.info("Test stopped before PRD test")
                socketio.emit('test_result', {'result': 'Test stopped'})
                return

            result = test_prd.run_test(socketio, stop_event)  # Pass the stop_event to the PRD test function
            logging.info(f"Test in PRD completed: {result}")

        # Emit a message indicating that all tests completed successfully
        socketio.emit('test_result', {'result': 'All tests completed'})

    except Exception as e:
        logging.error(f"Error running test for {environment.upper()}: {e}")
        socketio.emit('test_result', {'error': str(e)})

# Main entry point for the Flask app
if __name__ == '__main__':
    # Start the Flask app with SocketIO support
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
