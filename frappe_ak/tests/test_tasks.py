"""Tests for tasks.py — scheduled background jobs."""

from unittest.mock import patch, MagicMock, call

import frappe
from frappe.tests import UnitTestCase
from frappe.utils import now_datetime, add_days

from frappe_ak.tasks import expire_shares, send_reminders


class TestExpireShares(UnitTestCase):
	"""Tests for the expire_shares scheduled task."""

	@patch("frappe_ak.tasks.frappe.db.commit")
	@patch("frappe_ak.tasks.frappe.db.set_value")
	@patch("frappe_ak.tasks.frappe.get_all")
	def test_expires_active_shares_past_deadline(self, mock_get_all, mock_set_value, mock_commit):
		mock_get_all.return_value = ["SHARE-001", "SHARE-002"]

		expire_shares()

		self.assertEqual(mock_set_value.call_count, 2)
		mock_set_value.assert_any_call(
			"AK Document Share", "SHARE-001",
			{"is_active": 0, "status": "Expired"},
			update_modified=False,
		)
		mock_set_value.assert_any_call(
			"AK Document Share", "SHARE-002",
			{"is_active": 0, "status": "Expired"},
			update_modified=False,
		)
		mock_commit.assert_called_once()

	@patch("frappe_ak.tasks.frappe.db.commit")
	@patch("frappe_ak.tasks.frappe.db.set_value")
	@patch("frappe_ak.tasks.frappe.get_all")
	def test_no_expired_shares_does_nothing(self, mock_get_all, mock_set_value, mock_commit):
		mock_get_all.return_value = []

		expire_shares()

		mock_set_value.assert_not_called()
		mock_commit.assert_not_called()

	@patch("frappe_ak.tasks.frappe.get_all")
	def test_queries_correct_filters(self, mock_get_all):
		mock_get_all.return_value = []

		expire_shares()

		call_kwargs = mock_get_all.call_args
		filters = call_kwargs.kwargs.get("filters") or call_kwargs[1].get("filters")
		self.assertEqual(filters["is_active"], 1)
		self.assertIn("not in", filters["status"][0] if isinstance(filters["status"], list) else "")


class TestSendReminders(UnitTestCase):
	"""Tests for the send_reminders scheduled task."""

	@patch("frappe_ak.tasks.frappe.get_all")
	def test_no_templates_with_reminders_returns_early(self, mock_get_all):
		mock_get_all.return_value = []

		send_reminders()

		# Only called once for templates, never for shares
		mock_get_all.assert_called_once()

	@patch("frappe_ak.tasks.frappe.db.commit")
	@patch("frappe_ak.tasks.frappe.db.set_value")
	@patch("frappe_ak.email_utils.send_document_email")
	@patch("frappe_ak.tasks.frappe.get_all")
	def test_sends_reminder_for_eligible_shares(self, mock_get_all, mock_send_email, mock_set_value, mock_commit):
		# First call returns templates, second returns shares
		mock_get_all.side_effect = [
			[frappe._dict({"name": "TMPL-001", "reminder_days": 3})],
			[frappe._dict({"name": "SHARE-001", "recipient_email": "test@example.com"})],
		]

		send_reminders()

		mock_send_email.assert_called_once_with("SHARE-001")
		mock_set_value.assert_called_once()
		call_args = mock_set_value.call_args
		self.assertEqual(call_args[0][1], "SHARE-001")
		self.assertEqual(call_args[0][2]["reminder_sent"], 1)
		mock_commit.assert_called_once()

	@patch("frappe_ak.tasks.frappe.db.commit")
	@patch("frappe_ak.tasks.frappe.db.set_value")
	@patch("frappe_ak.tasks.send_document_email", side_effect=Exception("SMTP error"))
	@patch("frappe_ak.tasks.frappe.log_error")
	@patch("frappe_ak.tasks.frappe.get_all")
	def test_handles_send_failure_gracefully(self, mock_get_all, mock_log_error, mock_send_email, mock_set_value, mock_commit):
		mock_get_all.side_effect = [
			[frappe._dict({"name": "TMPL-001", "reminder_days": 3})],
			[frappe._dict({"name": "SHARE-001", "recipient_email": "test@example.com"})],
		]

		# Should not raise
		send_reminders()

		mock_log_error.assert_called_once()
		# reminder_sent should NOT be set since it failed
		mock_set_value.assert_not_called()
		# No successful sends, so no commit
		mock_commit.assert_not_called()

	@patch("frappe_ak.tasks.frappe.db.commit")
	@patch("frappe_ak.tasks.frappe.db.set_value")
	@patch("frappe_ak.email_utils.send_document_email")
	@patch("frappe_ak.tasks.frappe.get_all")
	def test_multiple_templates_multiple_shares(self, mock_get_all, mock_send_email, mock_set_value, mock_commit):
		mock_get_all.side_effect = [
			# Two templates
			[
				frappe._dict({"name": "TMPL-001", "reminder_days": 3}),
				frappe._dict({"name": "TMPL-002", "reminder_days": 7}),
			],
			# Shares for TMPL-001
			[frappe._dict({"name": "SHARE-001", "recipient_email": "a@example.com"})],
			# Shares for TMPL-002
			[
				frappe._dict({"name": "SHARE-002", "recipient_email": "b@example.com"}),
				frappe._dict({"name": "SHARE-003", "recipient_email": "c@example.com"}),
			],
		]

		send_reminders()

		self.assertEqual(mock_send_email.call_count, 3)
		self.assertEqual(mock_set_value.call_count, 3)
		mock_commit.assert_called_once()

	@patch("frappe_ak.tasks.frappe.get_all")
	def test_queries_shares_with_correct_filters(self, mock_get_all):
		mock_get_all.side_effect = [
			[frappe._dict({"name": "TMPL-001", "reminder_days": 5})],
			[],  # No shares found
		]

		send_reminders()

		# Second call is the shares query
		shares_call = mock_get_all.call_args_list[1]
		filters = shares_call.kwargs.get("filters") or shares_call[1].get("filters")
		self.assertEqual(filters["template"], "TMPL-001")
		self.assertEqual(filters["is_active"], 1)
		self.assertEqual(filters["email_sent"], 1)
		self.assertEqual(filters["reminder_sent"], 0)
		self.assertEqual(filters["status"], ["in", ["Active", "Viewed"]])
