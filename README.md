## Getting Started

### Setup

1. Create and activate a virtual environment:

   **Windows:**
   ```
   python -m venv venv
   venv\Scripts\activate
   ```

   **macOS/Linux:**
   ```
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

### Run

- Run the integration test (the server will be initialized by the test):
    ```
    pytest -s integration_test.py
    ```


