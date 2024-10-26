BASE_URL = "http://localhost:5000"

INITIAL_POLLING_INTERVAL = 1

# For now, the default value is float, we have no limit (infinite retries), we can change it if we want a limit on that
MAX_RETRIES = float("inf")

BACKOFF_FACTOR = 2

MAX_INTERVAL = 30

LOGGER_NAME = "Translation Client"
