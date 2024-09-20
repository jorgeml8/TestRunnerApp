import logging
import json
import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO
from tests import test_uat, test_prd, test2_uat

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

# Load app version from version.json
with open(os.path.join(script_dir, 'version.json'), 'r') as file:
    version_data = json.load(file)
    app_version = version_data.get('version', '1.0.0')

# Routes
@app.route('/testrunner/')
def index():
    return render_template('index.html', version=app_version)

@app.route('/testrunner/run_test', methods=['POST'])
def start_test():
    environment = request.form.get('environment', '').lower()
    
    if environment not in ['uat', 'prd']:
        return jsonify({'error': 'Invalid environment'}), 400

    logging.info(f"Starting test in: {environment.upper()}")
    # Run the test in the background
    socketio.start_background_task(run_test_task, environment)

    return jsonify({'status': f'Test in {environment.upper()} started'})

@app.route('/download/<filename>')
def download_file(filename):
    try:
        return send_from_directory(RESULTS_DIR, filename, as_attachment=True)
    except Exception as e:
        logging.error(f"Error downloading file: {e}")
        return jsonify({"error": str(e)}), 404

def run_test_task(environment):
    try:
        if environment == 'uat':
            result = test_uat.run_test(socketio)   # UAT test 1
            result = test2_uat.run_test(socketio)  # UAT test 2
        elif environment == 'prd':
            result = test_prd.run_test(socketio)   # PRD test

        logging.info(f"Test in {environment.upper()} completed: {result}")
        # Emit result back to the client
        socketio.emit('test_result', {'result': result})

    except Exception as e:
        logging.error(f"Error running test for {environment.upper()}: {e}")
        socketio.emit('test_result', {'error': str(e)})

if __name__ == '__main__':
    # Start the Flask app with SocketIO
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
