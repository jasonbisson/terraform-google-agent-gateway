import google.auth
import google.auth.transport.requests
import urllib.request
import json
import os

def fetch_logs():
    project_id = os.environ.get("PROJECT_ID", "agent-gateway-4481")
    
    credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    credentials.refresh(google.auth.transport.requests.Request())
    
    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json"
    }
    
    url = "https://logging.googleapis.com/v2/entries:list"
    payload = {
        "resourceNames": [f"projects/{project_id}"],
        "filter": f'resource.type="aiplatform.googleapis.com/ReasoningEngine" OR logName:"cloudbuild"',
        "pageSize": 30,
        "orderBy": "timestamp desc"
    }
    
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            entries = data.get("entries", [])
            print(f"Found {len(entries)} log entries:")
            for e in entries:
                text = e.get("textPayload") or e.get("jsonPayload", {})
                print(f"[{e.get('timestamp')}] [{e.get('severity')}] {text}")
    except Exception as err:
        print("Error fetching logs:", err)

if __name__ == "__main__":
    fetch_logs()
