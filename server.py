from flask import Flask, jsonify
import logging

app = Flask()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Server")

if __name__ == '__main__':
    try:
        app.run(port=5000)
    except Exception as e:
        logger.exception("Failed to start the server: %s", str(e))
