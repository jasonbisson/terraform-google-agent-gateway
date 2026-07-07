import google.auth
import google.auth.transport.requests
import urllib.request
import json
import sys

def main():
    project = "agent-gateway-4481"
    
    credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    credentials.refresh(google.auth.transport.requests.Request())
    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json",
        "X-Goog-User-Project": project,
    }

    print("--- Listing Cloud Builds ---")
    builds_url = f"https://cloudbuild.googleapis.com/v1/projects/{project}/builds?pageSize=10"
    try:
        req = urllib.request.Request(builds_url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            builds = data.get("builds", [])
            for b in builds:
                print(f"ID: {b.get('id')}")
                print(f"Status: {b.get('status')}")
                print(f"Create Time: {b.get('createTime')}")
                print(f"Source: {json.dumps(b.get('source', {}))}")
                print(f"Log URL: {b.get('logUrl')}")
                # Print failure info if exists
                if "failureInfo" in b:
                    print(f"Failure Info: {b.get('failureInfo')}")
                print("-" * 40)
    except Exception as e:
        print(f"Failed to list builds: {sys.exc_info()}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
