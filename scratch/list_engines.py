import google.auth
import google.auth.transport.requests
import urllib.request
import json
import sys

def main():
    project = "agent-gateway-4481"
    region = "us-central1"
    
    credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    credentials.refresh(google.auth.transport.requests.Request())
    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json",
        "X-Goog-User-Project": project,
    }

    print("--- Listing Vertex AI Operations ---")
    ops_url = f"https://{region}-aiplatform.googleapis.com/v1beta1/projects/{project}/locations/{region}/operations?filter=metadata.operationType%3D%22CREATE_REASONING_ENGINE%22"
    try:
        req = urllib.request.Request(ops_url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            operations = data.get("operations", [])
            for op in operations[:10]:
                print(f"Name: {op.get('name')}")
                print(f"Done: {op.get('done')}")
                if "error" in op:
                    print(f"Error: {op.get('error')}")
                if "metadata" in op:
                    meta = op.get("metadata", {})
                    print(f"Metadata: {json.dumps(meta, indent=2)}")
                print("-" * 40)
    except Exception as e:
        print(f"Failed to list operations: {e}")

    print("\n--- Listing Reasoning Engines ---")
    engines_url = f"https://{region}-aiplatform.googleapis.com/v1beta1/projects/{project}/locations/{region}/reasoningEngines"
    try:
        req = urllib.request.Request(engines_url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            engines = data.get("reasoningEngines", [])
            for engine in engines:
                print(f"Name: {engine.get('name')}")
                print(f"Display Name: {engine.get('displayName')}")
                print(f"Create Time: {engine.get('createTime')}")
                print("-" * 40)
    except Exception as e:
        print(f"Failed to list reasoning engines: {e}")

if __name__ == "__main__":
    main()
