from __future__ import annotations

import base64
import copy
import json
import unittest
from datetime import datetime
from unittest.mock import Mock, patch

from fis_demo import deploy, fabric


class FinanceDeploymentTests(unittest.TestCase):
    def setUp(self) -> None:
        with patch("fis_demo.fabric.az_token", return_value="fake-token"):
            self.client = fabric.Fabric("workspace")
        self.addCleanup(self.client.session.close)
        self.item = {"id": "notebook", "displayName": "FIS_01_Finance_Medallion", "type": "Notebook"}
        self.lakehouse = {"id": "gold", "displayName": "FIS_Finance_Gold"}

    def test_deployment_imports_its_own_fabric_helpers(self) -> None:
        self.assertIs(deploy.Fabric, fabric.Fabric)
        self.assertIs(deploy.az_token, fabric.az_token)
        self.assertIs(deploy.normalize_notebook, fabric.normalize_notebook)

    def test_notebook_normalization_preserves_code_and_binds_finance_gold(self) -> None:
        document = {"cells": [{"cell_type": "code", "source": "value = 1\nprint(value)\n"}]}
        normalized = fabric.normalize_notebook(document, self.lakehouse, "workspace")
        cell = normalized["cells"][0]
        self.assertEqual("".join(cell["source"]), "value = 1\nprint(value)")
        self.assertEqual(cell["outputs"], [])
        self.assertIsNone(cell["execution_count"])
        self.assertEqual(normalized["nbformat"], 4)
        self.assertEqual(normalized["metadata"]["dependencies"]["lakehouse"], {
            "default_lakehouse": "gold",
            "default_lakehouse_name": "FIS_Finance_Gold",
            "default_lakehouse_workspace_id": "workspace",
        })

    def test_existing_item_is_reused_without_writes(self) -> None:
        with patch.object(self.client, "items", return_value=[self.item]), patch.object(self.client, "request") as request:
            result = self.client.create_or_reuse(self.item["displayName"], "Notebook", "Synthetic finance")
        self.assertEqual(result, self.item)
        request.assert_not_called()

    def test_duplicate_item_names_are_rejected(self) -> None:
        with patch.object(self.client, "items", return_value=[self.item, self.item]):
            with self.assertRaisesRegex(RuntimeError, "refusing an ambiguous update"):
                self.client.create_or_reuse(self.item["displayName"], "Notebook", "Synthetic finance")

    def test_new_item_uses_the_dedicated_workspace(self) -> None:
        response = Mock(status_code=201, content=b"{}")
        response.json.return_value = {"id": "notebook"}
        with patch.object(self.client, "items", return_value=[]), patch.object(
            self.client, "request", return_value=response
        ) as request:
            result = self.client.create_or_reuse(self.item["displayName"], "Notebook", "Synthetic finance")
        self.assertEqual(result, self.item)
        self.assertEqual(request.call_args.args, ("POST", "/workspaces/workspace/items"))
        self.assertEqual(json.loads(request.call_args.kwargs["data"])["displayName"], self.item["displayName"])

    def test_failed_fabric_operation_is_surfaced(self) -> None:
        response = Mock(status_code=202, headers={"Location": "https://api.fabric.microsoft.com/v1/operations/test"})
        poll = Mock(content=b"{}")
        poll.json.return_value = {"status": "Failed", "error": {"message": "Test failure"}}
        with patch.object(self.client, "request", return_value=poll):
            with self.assertRaisesRegex(RuntimeError, "Fabric operation ended as Failed"):
                self.client.wait_lro(response)

    def test_recent_notebook_job_is_monitored_instead_of_resubmitted(self) -> None:
        started = "2026-10-28T17:00:00+00:00"
        now = datetime.fromisoformat(started).timestamp() + 30
        completed = {"id": "existing-job", "status": "Completed"}
        response = Mock()
        response.json.return_value = completed
        with patch("fis_demo.fabric.time.time", return_value=now), patch.object(
            self.client, "recent_jobs",
            return_value=[{"id": "existing-job", "startTimeUtc": started, "status": "InProgress"}],
        ), patch.object(self.client, "request", return_value=response) as request:
            result = self.client.run_notebook(self.item, self.lakehouse)
        self.assertEqual(result, completed)
        request.assert_called_once_with(
            "GET", "/workspaces/workspace/items/notebook/jobs/instances/existing-job"
        )

    def test_invalid_notebook_job_timestamp_does_not_trigger_a_new_run(self) -> None:
        for started in (None, "invalid-date"):
            with self.subTest(started=started), patch.object(
                self.client, "recent_jobs",
                return_value=[{"id": "existing-job", "startTimeUtc": started, "status": "InProgress"}],
            ), patch.object(self.client, "request") as request:
                with self.assertRaisesRegex(ValueError, "timestamp"):
                    self.client.run_notebook(self.item, self.lakehouse)
                request.assert_not_called()

    def test_completed_history_without_timestamp_does_not_block_a_new_run(self) -> None:
        submitted = Mock(
            headers={"Location": "https://api.fabric.microsoft.com/v1/workspaces/workspace/items/notebook/jobs/instances/new-job"},
            content=b"",
        )
        completed = {"id": "new-job", "status": "Completed"}
        response = Mock()
        response.json.return_value = completed
        with patch.object(
            self.client, "recent_jobs", return_value=[{"id": "finished-job", "status": "Completed"}]
        ), patch.object(self.client, "request", side_effect=[submitted, response]) as request:
            self.assertEqual(self.client.run_notebook(self.item, self.lakehouse), completed)
        self.assertEqual(request.call_args_list[0].args, (
            "POST", "/workspaces/workspace/items/notebook/jobs/instances?jobType=RunNotebook",
        ))
        configuration = json.loads(request.call_args_list[0].kwargs["data"])["executionData"]["configuration"]
        self.assertEqual(configuration["defaultLakehouse"], {"id": "gold", "name": "FIS_Finance_Gold"})
        self.assertEqual(request.call_args_list[1].args, (
            "GET", "/workspaces/workspace/items/notebook/jobs/instances/new-job",
        ))

    def test_privacy_receipt_keeps_marker_check_without_free_text_description(self) -> None:
        workspace = {
            "id": "workspace", "displayName": "FIS-Finance-IQ",
            "description": deploy.PRIVACY_MARKER + " Synthetic finance only.",
        }
        original_workspace = copy.deepcopy(workspace)
        assignment = {"principal": {"id": "caller", "type": "User"}, "role": "Admin"}
        payload = base64.urlsafe_b64encode(json.dumps({"oid": "caller", "tid": "tenant"}).encode()).decode().rstrip("=")
        token = f"header.{payload}.signature"
        workspace_response = Mock()
        workspace_response.json.return_value = workspace
        roles_response = Mock()
        roles_response.json.return_value = {"value": [assignment]}
        with patch("fis_demo.deploy.az_token", return_value=token), patch.object(
            self.client, "request", side_effect=[workspace_response, roles_response]
        ):
            result = deploy.verify_privacy(self.client, "FIS-Finance-IQ")
        self.assertTrue(result["descriptionMarkerVerified"])
        self.assertTrue(result["privacyVerified"])
        self.assertNotIn("description", result["workspace"])
        self.assertEqual(result["roleAssignments"], [assignment])
        self.assertEqual(workspace, original_workspace)

    def test_workspace_without_finance_marker_is_rejected(self) -> None:
        response = Mock()
        response.json.return_value = {"displayName": "FIS-Finance-IQ", "description": "Unrelated workspace"}
        with patch.object(self.client, "request", return_value=response):
            with self.assertRaisesRegex(ValueError, "dedicated FIS identity"):
                deploy.verify_privacy(self.client, "FIS-Finance-IQ")

    def test_multiple_workspace_role_assignments_are_rejected(self) -> None:
        workspace = Mock()
        workspace.json.return_value = {
            "displayName": "FIS-Finance-IQ", "description": deploy.PRIVACY_MARKER,
        }
        roles = Mock()
        roles.json.return_value = {"value": [{}, {}]}
        payload = base64.urlsafe_b64encode(b'{"oid":"caller","tid":"tenant"}').decode().rstrip("=")
        with patch("fis_demo.deploy.az_token", return_value=f"header.{payload}.signature"), patch.object(
            self.client, "request", side_effect=[workspace, roles]
        ):
            with self.assertRaisesRegex(ValueError, "exactly one workspace role assignment"):
                deploy.verify_privacy(self.client, "FIS-Finance-IQ")


if __name__ == "__main__":
    unittest.main()
