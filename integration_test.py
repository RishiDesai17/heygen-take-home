import pytest
import asyncio
import logging
import subprocess
import time
from translation_client import TranslationClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Test Logger")

@pytest.fixture(scope="module")
def server_process():
    """Start the server as a subprocess."""
    process = subprocess.Popen(["python", "server.py"])
    time.sleep(2)  # Give the server time to start
    yield process
    process.terminate()  # Gracefully stop the server
    process.wait()  # Ensure it has stopped

def async_callback(response):
    """Asynchronous callback function for the status check."""
    if response.get("error"):
        logger.error(f"Error in fetching the task completion status: {response.get('message')}")
        return
    logger.info(f"Result: {response.get('task_completion_status')}")
    assert response.get("task_completion_status") in ("completed", "error")

def test_asynchronous_status_check(server_process):
    """Test the asynchronous status check."""
    logger.info("Testing asynchronous check_status_async...")
    client = TranslationClient()

    # Initiate the asynchronous status check
    client.check_status_async(async_callback)

    # Customer can add additional code here without needing to wait for the status update to finish

    time.sleep(20)  # Adding this for the test the callback output once complete

if __name__ == '__main__':
    pytest.main()
