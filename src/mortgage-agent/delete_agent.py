import google.auth
import google.auth.transport.requests
import urllib.request
import json
import os

def delete_agent():
    project = os.environ.get("PROJECT_ID", "agent-gateway-4b08")
    region = os.environ.get("REGION", "us-central1")

    credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    credentials.refresh(google.auth.transport.requests.Request())
    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json",
    }

    url = f"https://{region}-aiplatform.googleapis.com/v1beta1/projects/{project}/locations/{region}/reasoningEngines"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            engines = data.get("reasoningEngines", [])
    except Exception as e:
        print(f"Error listing Reasoning Engines: {e}")
        return

    if not engines:
        print("No reasoning engines found in project.")
        return

    for engine in engines:
        engine_name = engine.get("name")
        display_name = engine.get("displayName", "")
        print(f"Deleting Reasoning Engine: {engine_name} ({display_name})...")

        del_req = urllib.request.Request(
            f"https://{region}-aiplatform.googleapis.com/v1beta1/{engine_name}",
            headers=headers,
            method="DELETE",
        )
        try:
            with urllib.request.urlopen(del_req) as del_resp:
                del_resp.read()
            print(f"  ✓ Delete operation started for {engine_name}")
        except Exception as e:
            print(f"  ✕ Failed to delete {engine_name}: {e}")

if __name__ == "__main__":
    delete_agent()
