import subprocess
import time
import httpx
import os

env = os.environ.copy()
env["DASHBOARD_USERNAME"] = "admin"
env["DASHBOARD_PASSWORD"] = "admin"

app_process = subprocess.Popen(["python", "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"], env=env)

time.sleep(2)

try:
    response = httpx.get("http://127.0.0.1:8000/dashboard", auth=("admin", "admin"))
    print(response.status_code)
except Exception as e:
    print(e)
finally:
    app_process.terminate()
