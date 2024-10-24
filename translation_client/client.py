import requests
import time
import logging
import threading
import random

class TranslationClient:
    def __init__(self, base_url="http://localhost:5000"):
        """
        Initialize the client library with configurable polling and number of retries.

        The purpose of having these variables is for us to have control over how many times we
        would be calling the "/status" API as per the best appropriate, as opposed to the customer
        calling it directly and having to deal with the risks associated with it. We want to keep
        the polling logic abstracted from customer for ease of usage and eliminating the risks associated.

        This also gives us room to implement a backoff/jitter mechanism if required.

        :param base_url: Base URL of the translation server (e.g., "http://localhost:5000").
        :param initial_polling_interval: Initial interval (in seconds) between status polls.
        :param max_retries: Maximum number of retries for polling.
        :param backoff_factor: Multiplier for backoff strategy (increases interval between polls).
        """

        self.base_url = base_url
        self.initial_polling_interval = 1

        # For now, we have no limit (infinite retries), we can change it if we want a limit
        self.max_retries = float("inf")

        self.logger = logging.getLogger("Translation Client")

    def _poll_status(self):
        """
        Poll the server for the status of the translation job until it has finished running.
        Implement a backoff mechanism for intervals when we come across potentially (self resolvable or short-lived) errors in fetching the status.
        """
        retries = 0
        curr_interval = self.initial_polling_interval
        while retries < self.max_retries:
            try:
                response = requests.get(f"{self.base_url}/status")
                response.raise_for_status()  # Raise an HTTPError for bad responses

                result = response.json().get("result")

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


            except Exception as e:
                self.logger.error("An unexpected error occurred: %s", str(e))
                return { "error": True, "message": "An unexpected error occured. Please try again later" }

            # Wait before the next retry and apply the delay to prevent overly frequent polling
            time.sleep(curr_interval)
            curr_interval = self.initial_polling_interval + random.randint(1, 4)
            retries += 1

        self.logger.error("Max retries exceeded. Returning pending state.")
        return { "error": False, "task_completion_status": "pending" }

