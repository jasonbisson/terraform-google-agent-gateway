#!/usr/bin/env python3
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Script to list and delete Vertex AI Reasoning Engine agents prior to running terraform destroy."""

import argparse
import json
import os
import sys
import urllib.request
import google.auth
import google.auth.transport.requests


def delete_agents(project: str, region: str, agent_name: str | None = None) -> None:
    """List and delete matching Reasoning Engine agents in the project."""
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
        print(f"Error listing Reasoning Engines in {project}/{region}: {e}")
        sys.exit(1)

    if not engines:
        print(f"No reasoning engines found in {project}/{region}.")
        return

    matching = []
    for engine in engines:
        name = engine.get("name", "")
        display_name = engine.get("displayName", "")
        if not agent_name or agent_name.lower() in display_name.lower() or agent_name.lower() in name.lower():
            matching.append((name, display_name))

    if not matching:
        print(f"No reasoning engines matching filter '{agent_name}' found.")
        return

    for engine_name, display_name in matching:
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


def main():
    parser = argparse.ArgumentParser(description="Delete Vertex AI Reasoning Engine agents.")
    parser.add_argument(
        "--project",
        default=os.environ.get("PROJECT_ID"),
        help="Google Cloud project ID (or set $PROJECT_ID)",
    )
    parser.add_argument(
        "--region",
        default=os.environ.get("REGION"),
        help="Google Cloud region (or set $REGION)",
    )
    parser.add_argument(
        "--agent-name",
        default=os.environ.get("AGENT_NAME"),
        help="Optional agent display name filter (or set $AGENT_NAME)",
    )
    args = parser.parse_args()

    if not args.project:
        parser.error("--project is required (or set $PROJECT_ID)")
    if not args.region:
        parser.error("--region is required (or set $REGION)")

    delete_agents(project=args.project, region=args.region, agent_name=args.agent_name)


if __name__ == "__main__":
    main()
