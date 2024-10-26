import requests
import time
import logging
import threading
import random

class TranslationClient:
    def __init__(self, base_url="http://localhost:5000"):
        """
        Initialize the client library with configurable polling and number of retries.

        The purpose of these variables is to control the frequency of "/status" API calls,
        optimizing usage on behalf of the customer. By handling the polling logic internally,
        we abstract it away from the customer, allowing easier usage and reducing the risks they
        would face if they called the "/status" API directly.

        This also gives us room to implement a backoff/jitter mechanism if required.

        :param base_url: Base URL of the translation server (e.g., "http://localhost:5000").
        
        At this time, we are not offering these parameters for customers to modify. This decision is to
        maintain control over the frequency of server pings and to mitigate any associated risks.

        initial_polling_interval: Initial interval (in seconds) between status polls.
        max_retries: Maximum number of retries for polling.
        backoff_factor: Multiplier for backoff strategy (increases interval between polls).
        max_interval: Puts a limit on the max interval (in seconds) length when using backoff factor.

        _stop_event: Using it for thread management.
        current_thread: Keeps a reference to the thread to use it later for destroying if necessary.
        logger: Reference to the logger.
        """

        self.base_url = base_url
        self.initial_polling_interval = 1

        # For now, we have no limit (infinite retries), we can change it if we want a limit
        self.max_retries = float("inf")

        # Backoff factor implementation (with maximum possible interval) for when certain types of errors happen
        self.backoff_factor = 2
        self.max_interval = 30

        self.logger = logging.getLogger("Translation Client")
        self._stop_event = threading.Event()
        self.current_thread = None

    def _poll_status(self):
        """
        Poll the server for the status of the translation job until it has finished running.
        Implement a backoff mechanism for intervals when we come across potentially self-resolvable or short-lived errors in fetching the status.
        """
        retries = 0
        curr_interval = self.initial_polling_interval
        while retries < self.max_retries:
            response = self._get_status()

            if not response.get("error"):
                result = response.get("result")
                if result == "completed":
                    self.logger.info("Job completed successfully.\n")
                    self._stop_event.is_set()
                    return { "task_completion_status": result }
                elif result == "error":
                    self.logger.error("Job failed to complete due to an error.\n")
                    self._stop_event.is_set()
                    return { "task_completion_status": result }
                elif result == "pending":
                    self.logger.info("Job is still pending.\n")
                else:
                    self.logger.warning("Unexpected result: %s. Treating as an error.", result)
                    return { "task_completion_status": "error" }
            else:
                if not response.get("retry_with_backoff"):
                    return { "error": response.get("error"), "message": response.get("message") }
                curr_interval += min(self.backoff_factor * curr_interval, self.max_interval)

            # Wait before the next retry and apply the delay to prevent overly frequent polling
            time.sleep(curr_interval)
            curr_interval = self.initial_polling_interval + random.randint(1, 4)
            retries += 1

        self.logger.error("Max retries exceeded. Returning pending state.")
        return { "task_completion_status": "pending" }

    def _get_status(self):
        try:
            response = requests.get(f"{self.base_url}/status")
            response.raise_for_status()  # Raise an HTTPError for bad responses
            return response.json()
        except requests.Timeout:
            self.logger.warning("Request timed out. Retrying...")
            return {
                "error": True,
                "retry_with_backoff": True,
                "message": "An unexpected error occured. Please try again later"
            }
        except requests.ConnectionError as e:
            self.logger.warning("Connection error occurred: %s. Retrying...", str(e))
            curr_interval += min(self.backoff_factor * curr_interval, self.max_interval)
            return {
                "error": True,
                "retry_with_backoff": True,
                "message": "An unexpected error occured. Please try again later"
            }
        except ValueError:
            self.logger.error("Failed to decode JSON response.")
            curr_interval += min(self.backoff_factor * curr_interval, self.max_interval)
            return {
                "error": True,
                "retry_with_backoff": True,
                "message": "An unexpected error occured. Please try again later"
            }
        except requests.HTTPError as e:
            self.logger.error("HTTP error occurred: %s. Response: %s", str(e), response.content)
            return {
                "error": True,
                "retry_with_backoff": False,
                "message": "An unexpected error occured. Please try again later"
            }
        except Exception as e:
            self.logger.error("An unexpected error occurred: %s", str(e))
            return {
                "error": True,
                "retry_with_backoff": False,
                "message": "An unexpected error occured. Please try again later"
            }

    def wait_for_completion(self):
        """
        Blocking call to wait for job completion. Runs the status check in the same thread.
        """
        result = self._poll_status()
        return result

    def check_status_async(self, callback):
        """
        Asynchronous status checking with callback support. Runs the status check in a separate thread.
        """
        if self.current_thread and self.current_thread.is_alive():
            # Stop the previous thread to prevent any chances for the thundering herd problem or multiple callbacks getting fired.
            self._stop_event.set()

        # check once if task is in a pending state or not
        response = self._get_status()
        # If we could not fetch the status due to an unexpected error (in which case "retry_with_backoff" would be false), we return the appropriate error message
        if response.get("error") and not response.get("retry_with_backoff"):
            return { "error": response.get("error"), "message": response.get("message") }

        result = response.get("result")
        # If the task is already completed or threw an error, we can return that and we do not need to start the polling mechanism
        if result == "completed" or result == "error":
            return { "task_completion_status": result }

        # If the task is in a pending state, we need to start the polling mechanism.
        self._stop_event.clear()
        self.current_thread = threading.Thread(target=self._async_poll, args=(callback,))
        self.current_thread.start()

        # We return the current status (pending). The callback function provided by the customer will be called when the job is completed or throws an error.
        return { "task_completion_status": "pending" }

    def _async_poll(self, callback):
        """
        Poll the server for status in a background thread and trigger the callback on completion.
        """
        result = self._poll_status()
        if not self._stop_event.is_set():
            callback(result)
