from flask import Flask, jsonify
import time
import random
import logging
from datetime import datetime, timedelta

app = Flask()

# Configurable time for the job to complete
JOB_COMPLETION_TIME = datetime.now() + timedelta(seconds=10)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Server")

@app.route('/status', methods=['GET'])
def get_status():
    """
    Simulates the status of a translation job.
    Returns 'pending' until JOB_COMPLETION_TIME has passed.
    After that, it returns 'completed' or 'error' randomly.
    """
    
    try:
        current_time = datetime.now()
        if current_time < JOB_COMPLETION_TIME:
            return jsonify({ "result": "pending" }), 202

        # Randomly return 'completed' or 'error' after the we've reached completion time
        if random.choice([True, False]):
            return jsonify({"result": "completed"}), 200
        else:
            return jsonify({"result": "error"}), 200

    except Exception as e:
        logger.exception("An unexpected error occurred while processing the request: %s", str(e))
        return jsonify({"error": "Internal Server Error"}), 500

if __name__ == '__main__':
    try:
        app.run(port=5000)
    except Exception as e:
        logger.exception("Failed to start the server: %s", str(e))
