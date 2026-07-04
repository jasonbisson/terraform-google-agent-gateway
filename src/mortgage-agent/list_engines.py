import google.auth
import google.auth.transport.requests
import urllib.request
import json

def list_engines():
    project = "agent-gateway-4b08"
    region = "us-central1"
    
    credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    credentials.refresh(google.auth.transport.requests.Request())
    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json"
    }
    
    url = f"https://{region}-aiplatform.googleapis.com/v1beta1/projects/{project}/locations/{region}/reasoningEngines"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            engines = data.get("reasoningEngines", [])
            print(f"Found {len(engines)} Reasoning Engines:")
            for e in engines:
                print(f"  Name: {e.get('name')}")
                print(f"  Display Name: {e.get('displayName')}")
    except Exception as err:
        print("Error listing engines:", err)

if __name__ == "__main__":
    list_engines()
