import subprocess
import time
import httpx

app_process = subprocess.Popen(["python", "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"])

time.sleep(2)

try:
    response = httpx.get("http://127.0.0.1:8000/dashboard")
    print(response.status_code)
except Exception as e:
    print(e)
finally:
    app_process.terminate()
