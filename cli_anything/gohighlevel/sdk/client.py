"""Importable public GoHighLevel SDK helpers.

This SDK intentionally wraps the official public API lane. Experimental
Firebase/internal workflow tooling stays in utils/ghl_internal_client.py.
"""
from __future__ import annotations

import os
from typing import Any

import requests

from cli_anything.gohighlevel.auth.pit import DEFAULT_VERSION

BASE_URL = "https://services.leadconnectorhq.com"


class GHLClient:
    """Small public API client with resource helpers matching ghlcli groups."""

    def __init__(
        self,
        api_key: str | None = None,
        location_id: str | None = None,
        version: str | None = None,
        base_url: str = BASE_URL,
        timeout: int = 30,
    ):
        self.api_key = (api_key or os.environ.get("GHL_API_KEY", "")).strip()
        self.location_id = (location_id or os.environ.get("GHL_LOCATION_ID", "")).strip()
        self.version = version or DEFAULT_VERSION
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        self.contacts = ContactsClient(self)
        self.conversations = ConversationsClient(self)
        self.workflows = WorkflowsClient(self)
        self.opportunities = OpportunitiesClient(self)
        self.calendars = CalendarsClient(self)
        self.locations = LocationsClient(self)
        self.payments = PaymentsClient(self)
        self.forms = FormsClient(self)
        self.social = SocialClient(self)
        self.documents = DocumentsClient(self)
        self.emails = EmailsClient(self)

    def request(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | list[Any] | None = None,
        params: dict[str, Any] | None = None,
        path_params: dict[str, Any] | None = None,
        version: str | None = None,
    ) -> Any:
        """Call any public HighLevel endpoint."""
        if not self.api_key:
            raise ValueError("GHL_API_KEY is not set")
        resolved_path = self.resolve_path(path, path_params)
        response = requests.request(
            method.upper(),
            f"{self.base_url}{resolved_path}",
            headers=self.headers(version),
            params=params or None,
            json=body,
            timeout=self.timeout,
        )
        response.raise_for_status()
        if not response.content:
            return {"statusCode": response.status_code}
        try:
            return response.json()
        except ValueError:
            return response.text

    def headers(self, version: str | None = None) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Version": version or self.version,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def require_location_id(self) -> str:
        if not self.location_id or self.location_id == "YOUR_LOCATION_ID":
            raise ValueError("GHL_LOCATION_ID is not set")
        return self.location_id

    def resolve_path(self, path: str, path_params: dict[str, Any] | None = None) -> str:
        resolved = path if path.startswith("/") else f"/{path}"
        params = {
            "locationId": self.location_id,
            "location_id": self.location_id,
            **(path_params or {}),
        }
        for key, value in params.items():
            if value is None:
                continue
            resolved = resolved.replace("{" + key + "}", str(value))
            resolved = resolved.replace(":" + key, str(value))
        return resolved

    def with_location(self, params: dict[str, Any] | None = None, key: str = "locationId") -> dict[str, Any]:
        payload = dict(params or {})
        payload.setdefault(key, self.require_location_id())
        return payload


class ResourceClient:
    def __init__(self, client: GHLClient):
        self.client = client

    def request(self, method: str, path: str, **kwargs) -> Any:
        return self.client.request(method, path, **kwargs)


class ContactsClient(ResourceClient):
    def list(self, *, limit: int = 20, skip: int = 0, **params) -> Any:
        return self.request("GET", "/contacts/", params=self.client.with_location({"limit": limit, "skip": skip, **params}))

    def get(self, contact_id: str) -> Any:
        return self.request("GET", f"/contacts/{contact_id}")

    def create(self, **body) -> Any:
        body.setdefault("locationId", self.client.require_location_id())
        return self.request("POST", "/contacts/", body=body)

    def update(self, contact_id: str, **body) -> Any:
        return self.request("PUT", f"/contacts/{contact_id}", body=body)

    def delete(self, contact_id: str) -> Any:
        return self.request("DELETE", f"/contacts/{contact_id}")

    def search(self, *, page: int = 1, page_limit: int = 20, query: str | None = None, filters: list[dict] | None = None) -> Any:
        body: dict[str, Any] = {
            "locationId": self.client.require_location_id(),
            "page": page,
            "pageLimit": page_limit,
        }
        if query:
            body["query"] = query
        if filters:
            body["filters"] = filters
        return self.request("POST", "/contacts/search", body=body)

    def add_tag(self, contact_id: str, *tags: str) -> Any:
        return self.request("POST", f"/contacts/{contact_id}/tags", body={"tags": list(tags)})

    def remove_tag(self, contact_id: str, *tags: str) -> Any:
        return self.request("DELETE", f"/contacts/{contact_id}/tags", body={"tags": list(tags)})


class ConversationsClient(ResourceClient):
    TYPE_MAP = {
        "Email": "TYPE_EMAIL",
        "SMS": "TYPE_SMS",
        "WhatsApp": "TYPE_WHATSAPP",
        "GMB": "TYPE_GMB",
        "IG": "TYPE_INSTAGRAM",
        "FB": "TYPE_FACEBOOK",
        "Live_Chat": "TYPE_LIVE_CHAT",
        "Custom": "TYPE_CUSTOM",
    }

    def list(self, *, limit: int = 20, status: str | None = None, message_type: str | None = None) -> Any:
        params = self.client.with_location({"limit": limit})
        if status:
            params["status"] = status
        if message_type:
            params["lastMessageType"] = self.TYPE_MAP.get(message_type, message_type)
        return self.request("GET", "/conversations/search", params=params)

    def get(self, conversation_id: str) -> Any:
        return self.request("GET", f"/conversations/{conversation_id}")

    def messages(self, conversation_id: str, *, limit: int = 20, message_type: str | None = None) -> Any:
        params: dict[str, Any] = {"limit": limit}
        if message_type:
            params["type"] = message_type
        return self.request("GET", f"/conversations/{conversation_id}/messages", params=params)

    def get_email(self, email_message_id: str) -> Any:
        return self.request("GET", f"/conversations/messages/email/{email_message_id}")

    def send(self, conversation_id: str, message: str, *, message_type: str = "SMS") -> Any:
        return self.request(
            "POST",
            "/conversations/messages",
            body={"type": message_type, "message": message, "conversationId": conversation_id},
        )


class WorkflowsClient(ResourceClient):
    def list(self) -> Any:
        return self.request("GET", "/workflows/", params=self.client.with_location({}))

    def enroll(self, contact_id: str, workflow_id: str) -> Any:
        return self.request("POST", f"/contacts/{contact_id}/workflow/{workflow_id}")

    def remove(self, contact_id: str, workflow_id: str) -> Any:
        return self.request("DELETE", f"/contacts/{contact_id}/workflow/{workflow_id}")


class OpportunitiesClient(ResourceClient):
    def list(self, *, pipeline_id: str | None = None, limit: int = 20, **params) -> Any:
        query = self.client.with_location({"limit": limit, **params}, key="location_id")
        if pipeline_id:
            query["pipeline_id"] = pipeline_id
        return self.request("GET", "/opportunities/search", params=query)

    def get(self, opportunity_id: str) -> Any:
        return self.request("GET", f"/opportunities/{opportunity_id}")

    def create(self, **body) -> Any:
        body.setdefault("locationId", self.client.require_location_id())
        return self.request("POST", "/opportunities/", body=body)

    def update(self, opportunity_id: str, **body) -> Any:
        return self.request("PUT", f"/opportunities/{opportunity_id}", body=body)

    def delete(self, opportunity_id: str) -> Any:
        return self.request("DELETE", f"/opportunities/{opportunity_id}")

    def pipelines(self) -> Any:
        return self.request("GET", "/opportunities/pipelines", params=self.client.with_location({}))


class CalendarsClient(ResourceClient):
    def list(self) -> Any:
        return self.request("GET", "/calendars/", params=self.client.with_location({}))

    def get(self, calendar_id: str) -> Any:
        return self.request("GET", f"/calendars/{calendar_id}")

    def slots(self, calendar_id: str, *, start_date: str, end_date: str, timezone: str | None = None) -> Any:
        params = {"startDate": start_date, "endDate": end_date}
        if timezone:
            params["timezone"] = timezone
        return self.request("GET", f"/calendars/{calendar_id}/free-slots", params=params)

    def appointments(self, *, start_date: str | None = None, end_date: str | None = None, **params) -> Any:
        query = self.client.with_location(params)
        if start_date:
            query["startDate"] = start_date
        if end_date:
            query["endDate"] = end_date
        return self.request("GET", "/calendars/events/appointments", params=query)

    def book(self, **body) -> Any:
        body.setdefault("locationId", self.client.require_location_id())
        return self.request("POST", "/calendars/events/appointments", body=body)

    def groups(self) -> Any:
        return self.request("GET", "/calendars/groups", params=self.client.with_location({}))


class LocationsClient(ResourceClient):
    def get(self, location_id: str | None = None) -> Any:
        return self.request("GET", f"/locations/{location_id or self.client.require_location_id()}")

    def search(self, *, company_id: str, limit: int = 20, skip: int = 0, query: str | None = None) -> Any:
        params: dict[str, Any] = {"companyId": company_id, "limit": limit, "skip": skip}
        if query:
            params["query"] = query
        return self.request("GET", "/locations/search", params=params)

    def tags(self) -> Any:
        return self.request("GET", "/locations/{locationId}/tags")

    def custom_fields(self) -> Any:
        return self.request("GET", "/locations/{locationId}/customFields")

    def custom_values(self) -> Any:
        return self.request("GET", "/locations/{locationId}/customValues")


class PaymentsClient(ResourceClient):
    def transactions(self, *, limit: int = 20, offset: int = 0, contact_id: str | None = None) -> Any:
        params = self.client.with_location({"limit": limit, "offset": offset})
        if contact_id:
            params["contactId"] = contact_id
        return self.request("GET", "/payments/transactions", params=params)

    def orders(self, *, limit: int = 20, offset: int = 0) -> Any:
        return self.request("GET", "/payments/orders", params=self.client.with_location({"limit": limit, "offset": offset}))

    def invoices(self, *, limit: int = 20, offset: int = 0, status: str | None = None, contact_id: str | None = None) -> Any:
        params = self.client.with_location({"limit": limit, "offset": offset})
        if status:
            params["status"] = status
        if contact_id:
            params["contactId"] = contact_id
        return self.request("GET", "/invoices/", params=params)

    def create_invoice(self, **body) -> Any:
        body.setdefault("locationId", self.client.require_location_id())
        return self.request("POST", "/invoices/", body=body)


class FormsClient(ResourceClient):
    def list(self, *, limit: int = 20, skip: int = 0, form_type: str | None = None) -> Any:
        params = self.client.with_location({"limit": limit, "skip": skip})
        if form_type:
            params["type"] = form_type
        return self.request("GET", "/forms/", params=params)

    def submissions(self, form_id: str, *, limit: int = 20, page: int = 1) -> Any:
        return self.request("GET", "/forms/submissions", params=self.client.with_location({"formId": form_id, "limit": limit, "page": page}))


class SocialClient(ResourceClient):
    def accounts(self) -> Any:
        return self.request("GET", "/social-media-posting/{locationId}/accounts")

    def posts(self, *, limit: int = 20, skip: int = 0, post_type: str | None = None) -> Any:
        body: dict[str, Any] = {"limit": str(limit), "skip": str(skip)}
        if post_type:
            body["type"] = post_type
        return self.request("POST", "/social-media-posting/{locationId}/posts/list", body=body)

    def create_post(self, *, account_ids: list[str], text: str, media_urls: list[str] | None = None, scheduled_at: str | None = None) -> Any:
        body: dict[str, Any] = {
            "locationId": self.client.require_location_id(),
            "accountIds": account_ids,
            "summary": text,
        }
        if media_urls:
            body["media"] = [{"url": url, "type": "image"} for url in media_urls]
        if scheduled_at:
            body["scheduledAt"] = scheduled_at
        return self.request("POST", "/social-media-posting/{locationId}/posts", body=body)


class DocumentsClient(ResourceClient):
    def list(self, *, limit: int = 20, skip: int = 0, **params) -> Any:
        return self.request("GET", "/proposals/document", params=self.client.with_location({"limit": limit, "skip": skip, **params}))

    def templates(self, *, limit: int = 20, **params) -> Any:
        return self.request("GET", "/proposals/templates", params=self.client.with_location({"limit": limit, **params}))

    def send(self, document_id: str, **body) -> Any:
        body.setdefault("documentId", document_id)
        body.setdefault("locationId", self.client.require_location_id())
        return self.request("POST", "/proposals/document/send", body=body)

    def send_template(self, template_id: str, contact_id: str, user_id: str, **body) -> Any:
        body.update({"templateId": template_id, "contactId": contact_id, "userId": user_id})
        body.setdefault("locationId", self.client.require_location_id())
        return self.request("POST", "/proposals/templates/send", body=body)


class EmailsClient(ResourceClient):
    def list_campaigns(self, *, status: str | None = None) -> Any:
        params = self.client.with_location({})
        if status:
            params["status"] = status
        return self.request("GET", "/campaigns/", params=params)
