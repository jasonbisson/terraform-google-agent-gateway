import google.auth
import google.auth.transport.requests
import urllib.request
import json

def grant():
    project = "agent-gateway-4b08"
    region = "us-central1"
    agent_principal = "principal://agents.global.org-1076760281923.system.id.goog/resources/aiplatform/projects/4655064447/locations/us-central1/reasoningEngines/6593180244272742400"
    role = "roles/iap.egressor"

    credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    credentials.refresh(google.auth.transport.requests.Request())
    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json",
        "X-Goog-User-Project": project,
    }

    for resource_type in ["mcpServers", "endpoints"]:
        ar_url = f"https://agentregistry.googleapis.com/v1alpha/projects/{project}/locations/{region}/{resource_type}"
        try:
            list_req = urllib.request.Request(ar_url, headers=headers)
            with urllib.request.urlopen(list_req) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                items = data.get(resource_type, [])
        except Exception as e:
            print(f"Failed to list {resource_type}: {e}")
            continue

        for item in items:
            resource_name = item.get("name")
            if not resource_name:
                continue
            res_id = resource_name.split("/")[-1]
            display_name = item.get("displayName", res_id)
            iap_url = f"https://iap.googleapis.com/v1/projects/{project}/locations/{region}/iap_web/agentRegistry/{resource_type}/{res_id}"

            try:
                get_req = urllib.request.Request(
                    f"{iap_url}:getIamPolicy",
                    data=json.dumps({"options": {"requestedPolicyVersion": 3}}).encode("utf-8"),
                    headers=headers,
                    method="POST",
                )
                with urllib.request.urlopen(get_req) as get_resp:
                    policy = json.loads(get_resp.read().decode("utf-8"))

                bindings = policy.get("bindings", [])
                target_binding = None
                for b in bindings:
                    if b.get("role") == role and not b.get("condition"):
                        target_binding = b
                        break

                if target_binding:
                    if agent_principal not in target_binding.get("members", []):
                        target_binding.setdefault("members", []).append(agent_principal)
                else:
                    bindings.append({"role": role, "members": [agent_principal]})

                policy["bindings"] = bindings
                policy["version"] = 3

                set_req = urllib.request.Request(
                    f"{iap_url}:setIamPolicy",
                    data=json.dumps({"policy": policy}).encode("utf-8"),
                    headers=headers,
                    method="POST",
                )
                with urllib.request.urlopen(set_req) as set_resp:
                    set_resp.read()

                print(f"✓ Granted {role} to {agent_principal} on {resource_type}/{display_name}")
            except Exception as e:
                print(f"✕ Could not set IAM policy on {resource_type}/{display_name}: {e}")

if __name__ == "__main__":
    grant()
