"""Additional command groups for the ghlcli foundation."""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import click
import requests

from cli_anything.gohighlevel import coverage, endpoints, mcp_inventory, qa_stress, registry
from cli_anything.gohighlevel.adapters import public_api
from cli_anything.gohighlevel.auth import firebase, pit
from cli_anything.gohighlevel.auth.oauth import (
    OAuthClient,
    load_profile,
    redact_token_response,
    save_profile,
)


def _emit(ctx: click.Context, data: Any, title: str | None = None) -> None:
    if ctx.obj and ctx.obj.get("json"):
        click.echo(json.dumps(data, indent=2, default=str))
        return
    if title:
        click.echo(title)
        click.echo("-" * len(title))
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                click.echo("  ".join(f"{k}={v}" for k, v in item.items()))
            else:
                click.echo(str(item))
    elif isinstance(data, dict):
        for key, value in data.items():
            click.echo(f"{key}: {value}")
    else:
        click.echo(str(data))


def _set_local_json(ctx: click.Context, local_json: bool) -> None:
    if local_json:
        ctx.ensure_object(dict)
        ctx.obj["json"] = True


def _handle_api_error(exc: Exception) -> None:
    if isinstance(exc, requests.exceptions.HTTPError):
        response = exc.response
        try:
            message = response.json()
        except Exception:
            message = response.text
        click.echo(f"API Error ({response.status_code}): {message}", err=True)
    else:
        click.echo(f"Error: {exc}", err=True)
    sys.exit(1)


def _parse_params(values: tuple[str, ...]) -> dict[str, str]:
    params: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise click.ClickException(f"Expected --param key=value, got: {value}")
        key, item = value.split("=", 1)
        params[key] = item
    return params


def _resolve_path(path: str, values: tuple[str, ...], location_id: str | None = None) -> str:
    path_params = _parse_params(values)
    if location_id:
        path_params.setdefault("locationId", location_id)
        path_params.setdefault("location_id", location_id)
        path_params.setdefault("location", location_id)

    resolved = path
    for key, value in path_params.items():
        resolved = resolved.replace("{" + key + "}", value)

    unresolved = sorted(set(re.findall(r"\{([^{}]+)\}", resolved)))
    if unresolved:
        missing = ", ".join(unresolved)
        raise click.ClickException(f"Missing --path-param for: {missing}")
    return resolved


def _read_body(path: str | None) -> Any:
    if not path:
        return None
    with open(path) as f:
        return json.load(f)


def _require_experimental(ctx: click.Context) -> None:
    if not (ctx.obj and ctx.obj.get("experimental")):
        raise click.ClickException(
            "This command uses HighLevel internal backend endpoints. "
            "Re-run with --experimental after reviewing the request."
        )


def register_foundation_commands(cli: click.Group) -> None:
    """Attach the new foundation command groups to the existing Click app."""

    @cli.command("doctor")
    @click.option("--json", "local_json", is_flag=True, help="Output JSON")
    @click.pass_context
    def doctor(ctx: click.Context, local_json):
        """Check local ghlcli configuration without calling HighLevel."""
        _set_local_json(ctx, local_json)
        token_profile = load_profile(os.environ.get("GHLCLI_PROFILE", "default"))
        data = {
            "project": "ghlcli",
            "public_api": pit.status(),
            "firebase": firebase.status(),
            "oauth": {
                "client_id": bool(os.environ.get("GHL_CLIENT_ID", "").strip()),
                "client_secret": bool(os.environ.get("GHL_CLIENT_SECRET", "").strip()),
                "stored_default_profile": bool(token_profile),
            },
            "endpoint_catalog": endpoints.catalog_status(),
        }
        _emit(ctx, data, "ghlcli doctor")

    @cli.group("capabilities")
    def capabilities_group():
        """Inspect the merged ghlcli capability registry."""

    @capabilities_group.command("list")
    @click.option("--provider", default=None, help="Filter by provider")
    @click.option("--stability", default=None, help="Filter by stability")
    @click.option("--auth", default=None, help="Filter by auth lane")
    @click.option("--merged", is_flag=True, help="Merge duplicate endpoint-backed capabilities")
    @click.option("--json", "local_json", is_flag=True, help="Output JSON")
    @click.pass_context
    def capabilities_list(ctx: click.Context, provider, stability, auth, merged, local_json):
        """List known and planned capabilities."""
        _set_local_json(ctx, local_json)
        items = list(registry.iter_commands(provider=provider, stability=stability, auth=auth))
        if merged:
            items = registry.merge_duplicate_capabilities(items)
        _emit(ctx, items, "Capabilities")

    @cli.group("endpoints")
    def endpoints_group():
        """Inspect the open-ghl-mcp endpoint catalog."""

    @endpoints_group.command("list")
    @click.option("--category", default=None, help="Only list one category")
    @click.option("--json", "local_json", is_flag=True, help="Output JSON")
    @click.pass_context
    def endpoints_list(ctx: click.Context, category, local_json):
        """List endpoint categories or endpoints for a category."""
        _set_local_json(ctx, local_json)
        try:
            if category:
                data = [endpoint.__dict__ for endpoint in endpoints.iter_endpoints(category)]
            else:
                data = [{"category": name} for name in endpoints.list_categories()]
            _emit(ctx, data, "Endpoints")
        except Exception as exc:
            raise click.ClickException(str(exc)) from exc

    @endpoints_group.command("show")
    @click.argument("category")
    @click.option("--json", "local_json", is_flag=True, help="Output JSON")
    @click.pass_context
    def endpoints_show(ctx: click.Context, category, local_json):
        """Show all endpoints in a category."""
        _set_local_json(ctx, local_json)
        try:
            data = [endpoint.__dict__ for endpoint in endpoints.iter_endpoints(category)]
            _emit(ctx, data, f"Endpoints: {category}")
        except Exception as exc:
            raise click.ClickException(str(exc)) from exc

    @endpoints_group.command("search")
    @click.argument("query")
    @click.option("--category", default=None, help="Only search one category")
    @click.option("--json", "local_json", is_flag=True, help="Output JSON")
    @click.pass_context
    def endpoints_search(ctx: click.Context, query, category, local_json):
        """Search endpoint catalog."""
        _set_local_json(ctx, local_json)
        try:
            data = [endpoint.__dict__ for endpoint in endpoints.search_endpoints(query, category)]
            _emit(ctx, data, f"Endpoint search: {query}")
        except Exception as exc:
            raise click.ClickException(str(exc)) from exc

    @endpoints_group.command("coverage")
    @click.option("--json", "local_json", is_flag=True, help="Output JSON")
    @click.pass_context
    def endpoints_coverage(ctx: click.Context, local_json):
        """Compare native commands with endpoint catalog coverage."""
        _set_local_json(ctx, local_json)
        try:
            data = coverage.build_endpoint_coverage(cli)
            _emit(ctx, data, "Endpoint coverage")
        except Exception as exc:
            raise click.ClickException(str(exc)) from exc


    @cli.command("request")
    @click.argument("method")
    @click.argument("path")
    @click.option("--body", "body_path", default=None, type=click.Path(exists=True), help="JSON request body file")
    @click.option("--param", "params", multiple=True, help="Query param key=value")
    @click.option("--path-param", "path_params", multiple=True, help="Path placeholder key=value")
    @click.option("--version", default="2021-07-28", help="HighLevel Version header")
    @click.option("--dry-run", is_flag=True, help="Print the request instead of sending it")
    @click.option("--json", "local_json", is_flag=True, help="Output JSON")
    @click.pass_context
    def generic_request(ctx: click.Context, method, path, body_path, params, path_params, version, dry_run, local_json):
        """Call any public HighLevel endpoint configured with PIT/OAuth token."""
        _set_local_json(ctx, local_json)
        try:
            body = _read_body(body_path)
            query = _parse_params(params)
            location_id = ctx.obj.get("location_id") if ctx.obj else None
            resolved_path = _resolve_path(path, path_params, location_id)
            request_preview = {
                "method": method.upper(),
                "path": resolved_path,
                "params": query,
                "body": body,
                "version": version,
            }
            if dry_run:
                _emit(ctx, request_preview, "Request dry run")
                return
            result = public_api.request(method, resolved_path, body=body, params=query, version=version)
            _emit(ctx, result, "Response")
        except Exception as exc:
            _handle_api_error(exc)

    @cli.group("internal")
    def internal_group():
        """Experimental internal HighLevel backend gateway."""

    @internal_group.command("request")
    @click.argument("method")
    @click.argument("path")
    @click.option("--body", "body_path", default=None, type=click.Path(exists=True), help="JSON request body file")
    @click.option("--path-param", "path_params", multiple=True, help="Path placeholder key=value")
    @click.option("--dry-run", is_flag=True, help="Print request without sending it")
    @click.option("--confirm", is_flag=True, help="Required for mutating internal requests")
    @click.option("--json", "local_json", is_flag=True, help="Output JSON")
    @click.pass_context
    def internal_request(ctx: click.Context, method, path, body_path, path_params, dry_run, confirm, local_json):
        """Call backend.leadconnectorhq.com with Firebase session auth."""
        _set_local_json(ctx, local_json)
        _require_experimental(ctx)
        try:
            body = _read_body(body_path)
            location_id = ctx.obj.get("location_id") if ctx.obj else None
            resolved_path = _resolve_path(path, path_params, location_id)
            method_upper = method.upper()
            mutates = method_upper not in {"GET", "HEAD", "OPTIONS"}
            preview = {
                "method": method_upper,
                "base_url": "https://backend.leadconnectorhq.com",
                "path": resolved_path,
                "body": body,
                "auth": "firebase-session",
                "mutates": mutates,
                "confirmed": bool(confirm),
            }
            if dry_run:
                _emit(ctx, preview, "Internal request dry run")
                return
            if mutates and not confirm:
                raise click.ClickException(
                    "Mutating internal requests require --confirm. "
                    "Run once with --dry-run first and verify the path/body."
                )

            from cli_anything.gohighlevel.utils.ghl_internal_client import (
                InternalGHLClient,
                TokenManager,
            )

            client = InternalGHLClient(TokenManager(), location_id or "")
            result = client.request(method_upper, resolved_path, body)
            if result is None:
                raise click.ClickException("Internal API request failed after Firebase token refresh.")
            _emit(ctx, result, "Internal response")
        except click.ClickException:
            raise
        except Exception as exc:
            click.echo(f"Error: {exc}", err=True)
            sys.exit(1)

    @cli.group("qa")
    def qa_group():
        """Run repeatable ghlcli QA and stress checks."""

    @qa_group.command("stress")
    @click.option("--mode", type=click.Choice(["mock", "dry-run", "live-read", "live-write"]), default="dry-run")
    @click.option("--report-dir", default=".gstack/qa-reports", help="Directory for markdown QA reports")
    @click.option("--timeout", default=30, type=int, help="Per-command timeout in seconds")
    @click.option("--include-agency", is_flag=True, help="Run agency PIT checks when agency env vars exist")
    @click.option("--json", "local_json", is_flag=True, help="Output JSON")
    @click.pass_context
    def qa_stress_command(ctx: click.Context, mode, report_dir, timeout, include_agency, local_json):
        """Stress-test CLI command wiring, dry-runs, and optional live API reads/writes."""
        _set_local_json(ctx, local_json)
        try:
            data = qa_stress.run_stress(
                mode=mode,
                report_dir=report_dir,
                timeout=timeout,
                include_agency=include_agency,
                cli=cli,
            )
            _emit(ctx, data, "QA stress")
        except ValueError as exc:
            raise click.ClickException(str(exc)) from exc

    @cli.group("oauth")
    def oauth_group():
        """OAuth token helpers."""

    @oauth_group.command("exchange-code")
    @click.option("--code", required=True, help="Authorization code from HighLevel")
    @click.option("--redirect-uri", required=True, help="OAuth redirect URI")
    @click.option("--user-type", default=None, help="Optional user_type, e.g. Company or Location")
    @click.option("--profile", default=None, help="Save token response under profile name")
    @click.option("--show-secrets", is_flag=True, help="Print full tokens instead of redacted metadata")
    @click.option("--json", "local_json", is_flag=True, help="Output JSON")
    @click.pass_context
    def oauth_exchange_code(ctx: click.Context, code, redirect_uri, user_type, profile, show_secrets, local_json):
        """Exchange an OAuth authorization code for access/refresh tokens."""
        _set_local_json(ctx, local_json)
        try:
            result = OAuthClient.from_env().exchange_code(code, redirect_uri, user_type)
            if profile:
                save_profile(profile, result)
            _emit(ctx, result if show_secrets else redact_token_response(result), "OAuth token")
        except Exception as exc:
            _handle_api_error(exc)

    @oauth_group.command("refresh")
    @click.option("--refresh-token", default=None, help="Refresh token; defaults to saved profile")
    @click.option("--profile", default="default", help="Profile to load/save")
    @click.option("--show-secrets", is_flag=True, help="Print full tokens instead of redacted metadata")
    @click.option("--json", "local_json", is_flag=True, help="Output JSON")
    @click.pass_context
    def oauth_refresh(ctx: click.Context, refresh_token, profile, show_secrets, local_json):
        """Refresh an OAuth access token."""
        _set_local_json(ctx, local_json)
        try:
            token = refresh_token
            if not token:
                stored = load_profile(profile) or {}
                token = stored.get("refresh_token")
            if not token:
                raise click.ClickException("Refresh token missing. Pass --refresh-token or save a profile first.")
            result = OAuthClient.from_env().refresh(token)
            save_profile(profile, result)
            _emit(ctx, result if show_secrets else redact_token_response(result), "OAuth refresh")
        except Exception as exc:
            _handle_api_error(exc)

    @oauth_group.command("location-token")
    @click.option("--company-token", default=None, help="Company access token; defaults to saved profile access_token")
    @click.option("--company-id", required=True, help="HighLevel company ID")
    @click.option("--location-id", required=True, help="HighLevel location ID")
    @click.option("--profile", default=None, help="Profile to load/save")
    @click.option("--show-secrets", is_flag=True, help="Print full tokens instead of redacted metadata")
    @click.option("--json", "local_json", is_flag=True, help="Output JSON")
    @click.pass_context
    def oauth_location_token(ctx: click.Context, company_token, company_id, location_id, profile, show_secrets, local_json):
        """Exchange a company token for a location token."""
        _set_local_json(ctx, local_json)
        try:
            token = company_token
            if not token and profile:
                stored = load_profile(profile) or {}
                token = stored.get("access_token")
            if not token:
                raise click.ClickException("Company token missing. Pass --company-token or --profile.")
            result = OAuthClient.from_env().location_token(token, company_id, location_id)
            if profile:
                save_profile(profile, result)
            _emit(ctx, result if show_secrets else redact_token_response(result), "Location token")
        except Exception as exc:
            _handle_api_error(exc)

    @cli.group("mcp")
    def mcp_group():
        """Inspect locally cloned GHL MCP projects."""

    @mcp_group.group("servers")
    def mcp_servers_group():
        """Inspect known local MCP servers."""

    @mcp_servers_group.command("list")
    @click.option("--json", "local_json", is_flag=True, help="Output JSON")
    @click.pass_context
    def mcp_servers_list(ctx: click.Context, local_json):
        """List known MCP servers and startup commands."""
        _set_local_json(ctx, local_json)
        _emit(ctx, [server.__dict__ for server in mcp_inventory.list_servers()], "MCP servers")

    @mcp_group.group("tools")
    def mcp_tools_group():
        """Inspect MCP tools without launching the server."""

    @mcp_tools_group.command("list")
    @click.argument("server", default="open-ghl-mcp", required=False)
    @click.option("--json", "local_json", is_flag=True, help="Output JSON")
    @click.pass_context
    def mcp_tools_list(ctx: click.Context, server, local_json):
        """List tools exposed by a locally cloned MCP server."""
        _set_local_json(ctx, local_json)
        try:
            _emit(ctx, [tool.__dict__ for tool in mcp_inventory.list_tools(server)], "MCP tools")
        except Exception as exc:
            raise click.ClickException(str(exc)) from exc
