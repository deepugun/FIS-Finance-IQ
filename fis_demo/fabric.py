"""Fabric REST, Azure CLI authentication and notebook helpers for the FIS demo."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from datetime import datetime

import requests


FABRIC = "https://api.fabric.microsoft.com/v1"


def az_token(resource: str) -> str:
    executable = shutil.which("az.cmd" if os.name == "nt" else "az")
    if not executable:
        raise RuntimeError("Azure CLI was not found on PATH")
    command = [executable, "account", "get-access-token", "--resource", resource, "--query", "accessToken", "-o", "tsv"]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return result.stdout.strip()


class Fabric:
    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        self.session = requests.Session()
        self.session.headers.update(
            {"Authorization": f"Bearer {az_token('https://api.fabric.microsoft.com')}", "Content-Type": "application/json"}
        )

    def request(self, method: str, path_or_url: str, **kwargs) -> requests.Response:
        url = path_or_url if path_or_url.startswith("http") else f"{FABRIC}{path_or_url}"
        response = None
        for attempt in range(5):
            try:
                response = self.session.request(method, url, timeout=120, **kwargs)
                break
            except requests.RequestException:
                if attempt == 4:
                    raise
                time.sleep(2 ** attempt)
        assert response is not None
        if response.status_code >= 400:
            raise RuntimeError(f"{method} {url}: HTTP {response.status_code}: {response.text[:2000]}")
        return response

    def wait_lro(self, response: requests.Response, timeout: int = 900) -> dict:
        if response.status_code != 202:
            return response.json() if response.content else {}
        location = response.headers.get("Location")
        if not location:
            raise RuntimeError(f"202 response omitted Location header: {response.headers}")
        deadline = time.time() + timeout
        while time.time() < deadline:
            poll = self.request("GET", location)
            body = poll.json() if poll.content else {}
            status = body.get("status")
            if status in {"Succeeded", "Completed"}:
                return body
            if status in {"Failed", "Cancelled", "Deduped"}:
                raise RuntimeError(f"Fabric operation ended as {status}: {json.dumps(body)}")
            time.sleep(int(poll.headers.get("Retry-After", "5")))
        raise TimeoutError(f"Fabric operation did not complete within {timeout}s: {location}")

    def items(self) -> list[dict]:
        values: list[dict] = []
        url = f"/workspaces/{self.workspace_id}/items"
        while url:
            body = self.request("GET", url).json()
            values.extend(body.get("value", []))
            url = body.get("continuationUri")
        return values

    def create_or_reuse(self, display_name: str, item_type: str, description: str) -> dict:
        matches = [item for item in self.items() if item["displayName"] == display_name and item["type"] == item_type]
        if len(matches) > 1:
            raise RuntimeError(f"Multiple {item_type} items named {display_name}; refusing an ambiguous update")
        if matches:
            print(f"REUSE {item_type} {display_name} {matches[0]['id']}")
            return matches[0]
        response = self.request(
            "POST",
            f"/workspaces/{self.workspace_id}/items",
            data=json.dumps({"displayName": display_name, "type": item_type, "description": description}),
        )
        body = self.wait_lro(response)
        item_id = body.get("id") or body.get("itemId")
        if not item_id:
            matches = [
                item for item in self.items()
                if item["displayName"] == display_name and item["type"] == item_type
            ]
            if len(matches) != 1:
                raise RuntimeError(f"Could not discover newly created {item_type} {display_name}: {body}")
            return matches[0]
        item = {"id": item_id, "displayName": display_name, "type": item_type}
        print(f"CREATE {item_type} {display_name} {item_id}")
        return item

    def recent_jobs(self, item_id: str) -> list[dict]:
        response = self.request("GET", f"/workspaces/{self.workspace_id}/items/{item_id}/jobs/instances")
        return response.json().get("value", [])

    def run_notebook(self, item: dict, lakehouse: dict, timeout: int = 2400) -> dict:
        # Monitor recent active runs instead of submitting a duplicate job.
        now = time.time()
        recent = []
        for job in self.recent_jobs(item["id"]):
            if job.get("status") in {"Completed", "Failed", "Cancelled", "Deduped"}:
                continue
            started = job.get("startTimeUtc") or job.get("startTime")
            if not isinstance(started, str):
                raise ValueError(f"Notebook job {job['id']} omitted its start timestamp")
            try:
                epoch = datetime.fromisoformat(started.replace("Z", "+00:00")).timestamp()
            except ValueError as error:
                raise ValueError(f"Invalid notebook job start timestamp: {started}") from error
            if now - epoch <= 300:
                recent.append(job)
        if recent:
            job_id = recent[0]["id"]
            print(f"MONITOR existing Notebook job {item['displayName']} {job_id}")
        else:
            body = {
                "executionData": {
                    "configuration": {
                        "defaultLakehouse": {"id": lakehouse["id"], "name": lakehouse["displayName"]}
                    }
                }
            }
            response = self.request(
                "POST",
                f"/workspaces/{self.workspace_id}/items/{item['id']}/jobs/instances?jobType=RunNotebook",
                data=json.dumps(body),
            )
            job_id = response.headers.get("Location", "").rstrip("/").split("/")[-1]
            if not job_id and response.content:
                job_id = response.json().get("id")
            if not job_id:
                jobs = self.recent_jobs(item["id"])
                if not jobs:
                    raise RuntimeError(f"No job ID returned for {item['displayName']}")
                job_id = jobs[0]["id"]
            print(f"SUBMITTED Notebook {item['displayName']} job={job_id}")

        deadline = time.time() + timeout
        while time.time() < deadline:
            job = self.request(
                "GET", f"/workspaces/{self.workspace_id}/items/{item['id']}/jobs/instances/{job_id}"
            ).json()
            status = job.get("status")
            print(f"JOB {item['displayName']} {job_id} {status}")
            if status == "Completed":
                return job
            if status in {"Failed", "Cancelled", "Deduped"}:
                raise RuntimeError(f"Notebook {item['displayName']} ended as {status}: {json.dumps(job)}")
            time.sleep(20)
        raise TimeoutError(f"Notebook {item['displayName']} timed out: {job_id}")


def normalize_notebook(notebook: dict, lakehouse: dict, workspace_id: str) -> dict:
    for cell in notebook.get("cells", []):
        cell.setdefault("metadata", {})
        if cell.get("cell_type") == "code":
            cell.setdefault("outputs", [])
            cell.setdefault("execution_count", None)
        source = cell.get("source", [])
        text = "".join(source) if isinstance(source, list) else str(source)
        lines = text.splitlines(keepends=True)
        if lines and lines[-1].endswith(("\n", "\r")):
            lines[-1] = lines[-1].rstrip("\r\n")
        cell["source"] = lines
    metadata = notebook.setdefault("metadata", {})
    metadata.setdefault("kernelspec", {"display_name": "Synapse PySpark", "language": "Python", "name": "synapse_pyspark"})
    metadata.setdefault("language_info", {"name": "python"})
    metadata.setdefault("dependencies", {})["lakehouse"] = {
        "default_lakehouse": lakehouse["id"],
        "default_lakehouse_name": lakehouse["displayName"],
        "default_lakehouse_workspace_id": workspace_id,
    }
    notebook["nbformat"] = 4
    notebook.setdefault("nbformat_minor", 5)
    return notebook
