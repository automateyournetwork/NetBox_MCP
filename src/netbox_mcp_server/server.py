"""NetBox MCP Server - Full CRUD operations for all NetBox API endpoints."""

from __future__ import annotations

import argparse
import logging
from typing import Any

import httpx
from fastmcp import FastMCP
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    netbox_url: str = "http://localhost:8000"
    netbox_token: SecretStr = SecretStr("")
    verify_ssl: bool = True


# ---------------------------------------------------------------------------
# All supported NetBox object types  (app.resource -> API path segment)
# ---------------------------------------------------------------------------

OBJECT_TYPES: dict[str, str] = {
    # ── DCIM ──────────────────────────────────────────────────────────────
    "dcim.regions": "dcim/regions",
    "dcim.site-groups": "dcim/site-groups",
    "dcim.sites": "dcim/sites",
    "dcim.locations": "dcim/locations",
    "dcim.rack-types": "dcim/rack-types",
    "dcim.rack-roles": "dcim/rack-roles",
    "dcim.racks": "dcim/racks",
    "dcim.rack-reservations": "dcim/rack-reservations",
    "dcim.manufacturers": "dcim/manufacturers",
    "dcim.device-types": "dcim/device-types",
    "dcim.device-type-profiles": "dcim/device-type-profiles",
    "dcim.module-types": "dcim/module-types",
    "dcim.device-roles": "dcim/device-roles",
    "dcim.platforms": "dcim/platforms",
    "dcim.devices": "dcim/devices",
    "dcim.modules": "dcim/modules",
    "dcim.console-ports": "dcim/console-ports",
    "dcim.console-port-templates": "dcim/console-port-templates",
    "dcim.console-server-ports": "dcim/console-server-ports",
    "dcim.console-server-port-templates": "dcim/console-server-port-templates",
    "dcim.power-ports": "dcim/power-ports",
    "dcim.power-port-templates": "dcim/power-port-templates",
    "dcim.power-outlets": "dcim/power-outlets",
    "dcim.power-outlet-templates": "dcim/power-outlet-templates",
    "dcim.interfaces": "dcim/interfaces",
    "dcim.interface-templates": "dcim/interface-templates",
    "dcim.front-ports": "dcim/front-ports",
    "dcim.front-port-templates": "dcim/front-port-templates",
    "dcim.rear-ports": "dcim/rear-ports",
    "dcim.rear-port-templates": "dcim/rear-port-templates",
    "dcim.device-bays": "dcim/device-bays",
    "dcim.device-bay-templates": "dcim/device-bay-templates",
    "dcim.module-bays": "dcim/module-bays",
    "dcim.module-bay-templates": "dcim/module-bay-templates",
    "dcim.inventory-items": "dcim/inventory-items",
    "dcim.inventory-item-templates": "dcim/inventory-item-templates",
    "dcim.inventory-item-roles": "dcim/inventory-item-roles",
    "dcim.cables": "dcim/cables",
    "dcim.cable-terminations": "dcim/cable-terminations",
    "dcim.power-panels": "dcim/power-panels",
    "dcim.power-feeds": "dcim/power-feeds",
    "dcim.virtual-chassis": "dcim/virtual-chassis",
    "dcim.virtual-device-contexts": "dcim/virtual-device-contexts",
    "dcim.mac-addresses": "dcim/mac-addresses",
    # ── IPAM ──────────────────────────────────────────────────────────────
    "ipam.vrfs": "ipam/vrfs",
    "ipam.route-targets": "ipam/route-targets",
    "ipam.rirs": "ipam/rirs",
    "ipam.aggregates": "ipam/aggregates",
    "ipam.roles": "ipam/roles",
    "ipam.prefixes": "ipam/prefixes",
    "ipam.ip-ranges": "ipam/ip-ranges",
    "ipam.ip-addresses": "ipam/ip-addresses",
    "ipam.asns": "ipam/asns",
    "ipam.asn-ranges": "ipam/asn-ranges",
    "ipam.fhrp-groups": "ipam/fhrp-groups",
    "ipam.fhrp-group-assignments": "ipam/fhrp-group-assignments",
    "ipam.vlan-groups": "ipam/vlan-groups",
    "ipam.vlans": "ipam/vlans",
    "ipam.vlan-translation-policies": "ipam/vlan-translation-policies",
    "ipam.vlan-translation-rules": "ipam/vlan-translation-rules",
    "ipam.service-templates": "ipam/service-templates",
    "ipam.services": "ipam/services",
    # ── Circuits ──────────────────────────────────────────────────────────
    "circuits.providers": "circuits/providers",
    "circuits.provider-accounts": "circuits/provider-accounts",
    "circuits.provider-networks": "circuits/provider-networks",
    "circuits.circuit-types": "circuits/circuit-types",
    "circuits.circuits": "circuits/circuits",
    "circuits.circuit-terminations": "circuits/circuit-terminations",
    "circuits.circuit-groups": "circuits/circuit-groups",
    "circuits.circuit-group-assignments": "circuits/circuit-group-assignments",
    "circuits.virtual-circuits": "circuits/virtual-circuits",
    "circuits.virtual-circuit-types": "circuits/virtual-circuit-types",
    "circuits.virtual-circuit-terminations": "circuits/virtual-circuit-terminations",
    # ── Tenancy ───────────────────────────────────────────────────────────
    "tenancy.tenant-groups": "tenancy/tenant-groups",
    "tenancy.tenants": "tenancy/tenants",
    "tenancy.contact-groups": "tenancy/contact-groups",
    "tenancy.contact-roles": "tenancy/contact-roles",
    "tenancy.contacts": "tenancy/contacts",
    "tenancy.contact-assignments": "tenancy/contact-assignments",
    # ── Virtualization ────────────────────────────────────────────────────
    "virtualization.cluster-types": "virtualization/cluster-types",
    "virtualization.cluster-groups": "virtualization/cluster-groups",
    "virtualization.clusters": "virtualization/clusters",
    "virtualization.virtual-machines": "virtualization/virtual-machines",
    "virtualization.interfaces": "virtualization/interfaces",
    "virtualization.virtual-disks": "virtualization/virtual-disks",
    # ── Wireless ──────────────────────────────────────────────────────────
    "wireless.wireless-lan-groups": "wireless/wireless-lan-groups",
    "wireless.wireless-lans": "wireless/wireless-lans",
    "wireless.wireless-links": "wireless/wireless-links",
    # ── VPN ────────────────────────────────────────────────────────────────
    "vpn.ike-policies": "vpn/ike-policies",
    "vpn.ike-proposals": "vpn/ike-proposals",
    "vpn.ipsec-policies": "vpn/ipsec-policies",
    "vpn.ipsec-proposals": "vpn/ipsec-proposals",
    "vpn.ipsec-profiles": "vpn/ipsec-profiles",
    "vpn.tunnel-groups": "vpn/tunnel-groups",
    "vpn.tunnels": "vpn/tunnels",
    "vpn.tunnel-terminations": "vpn/tunnel-terminations",
    "vpn.l2vpns": "vpn/l2vpns",
    "vpn.l2vpn-terminations": "vpn/l2vpn-terminations",
    # ── Extras ────────────────────────────────────────────────────────────
    "extras.webhooks": "extras/webhooks",
    "extras.event-rules": "extras/event-rules",
    "extras.custom-fields": "extras/custom-fields",
    "extras.custom-field-choice-sets": "extras/custom-field-choice-sets",
    "extras.custom-links": "extras/custom-links",
    "extras.export-templates": "extras/export-templates",
    "extras.saved-filters": "extras/saved-filters",
    "extras.tags": "extras/tags",
    "extras.image-attachments": "extras/image-attachments",
    "extras.journal-entries": "extras/journal-entries",
    "extras.config-contexts": "extras/config-contexts",
    "extras.config-templates": "extras/config-templates",
    "extras.bookmarks": "extras/bookmarks",
    # ── Core ──────────────────────────────────────────────────────────────
    "core.data-sources": "core/data-sources",
    "core.data-files": "core/data-files",
    "core.jobs": "core/jobs",
    "core.object-changes": "core/object-changes",
    # ── Users ─────────────────────────────────────────────────────────────
    "users.users": "users/users",
    "users.groups": "users/groups",
    "users.tokens": "users/tokens",
    "users.permissions": "users/permissions",
}


# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------

class NetBoxClient:
    """Thin wrapper around httpx for NetBox REST API calls."""

    def __init__(self, url: str, token: str, verify_ssl: bool = True) -> None:
        self.base_url = url.rstrip("/")
        self.client = httpx.Client(
            base_url=f"{self.base_url}/api/",
            headers={
                "Authorization": f"Token {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            verify=verify_ssl,
            timeout=30.0,
        )

    # -- helpers -----------------------------------------------------------

    def _resolve_path(self, object_type: str) -> str:
        """Convert 'dcim.devices' -> 'dcim/devices'."""
        path = OBJECT_TYPES.get(object_type)
        if path is None:
            raise ValueError(
                f"Unknown object_type '{object_type}'. "
                f"Valid types: {', '.join(sorted(OBJECT_TYPES))}"
            )
        return path

    # -- CRUD --------------------------------------------------------------

    def list_objects(
        self,
        object_type: str,
        filters: dict[str, Any] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        path = self._resolve_path(object_type)
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if filters:
            params.update(filters)
        resp = self.client.get(f"{path}/", params=params)
        resp.raise_for_status()
        return resp.json()

    def get_object(self, object_type: str, object_id: int) -> dict[str, Any]:
        path = self._resolve_path(object_type)
        resp = self.client.get(f"{path}/{object_id}/")
        resp.raise_for_status()
        return resp.json()

    def create_object(self, object_type: str, data: dict[str, Any]) -> dict[str, Any]:
        path = self._resolve_path(object_type)
        resp = self.client.post(f"{path}/", json=data)
        resp.raise_for_status()
        return resp.json()

    def update_object(
        self,
        object_type: str,
        object_id: int,
        data: dict[str, Any],
        partial: bool = True,
    ) -> dict[str, Any]:
        path = self._resolve_path(object_type)
        if partial:
            resp = self.client.patch(f"{path}/{object_id}/", json=data)
        else:
            resp = self.client.put(f"{path}/{object_id}/", json=data)
        resp.raise_for_status()
        return resp.json()

    def delete_object(self, object_type: str, object_id: int) -> dict[str, str]:
        path = self._resolve_path(object_type)
        resp = self.client.delete(f"{path}/{object_id}/")
        resp.raise_for_status()
        return {"status": "deleted", "object_type": object_type, "id": object_id}


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "NetBox MCP Server",
    instructions="Full CRUD MCP server for NetBox infrastructure management. "
    "Use netbox_list_object_types to discover available object types, then use "
    "the CRUD tools (list, get, create, update, delete) with the object_type parameter.",
)

settings = Settings()
netbox: NetBoxClient | None = None


def get_client() -> NetBoxClient:
    global netbox
    if netbox is None:
        netbox = NetBoxClient(
            url=settings.netbox_url,
            token=settings.netbox_token.get_secret_value(),
            verify_ssl=settings.verify_ssl,
        )
    return netbox


# ---------------------------------------------------------------------------
# Tool: List / search objects
# ---------------------------------------------------------------------------

@mcp.tool()
def netbox_list_objects(
    object_type: str,
    filters: dict[str, Any] | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    """List NetBox objects of a given type with optional filtering and pagination.

    Args:
        object_type: The NetBox object type in 'app.resource' format.
            Examples: 'dcim.devices', 'ipam.ip-addresses', 'circuits.circuits',
            'tenancy.tenants', 'virtualization.virtual-machines', 'dcim.sites',
            'ipam.prefixes', 'ipam.vlans', 'dcim.interfaces', 'dcim.cables'.
        filters: Optional dict of filter parameters.
            Examples: {"site": "nyc"}, {"status": "active", "role": "router"},
            {"tenant__n": "null"}, {"tag": "production"}, {"q": "search term"}.
        limit: Maximum number of results to return (1-1000, default 50).
        offset: Number of results to skip for pagination (default 0).

    Returns:
        A dict with 'count' (total matching), 'next', 'previous', and 'results'.
    """
    client = get_client()
    return client.list_objects(object_type, filters=filters, limit=limit, offset=offset)


# ---------------------------------------------------------------------------
# Tool: Get single object
# ---------------------------------------------------------------------------

@mcp.tool()
def netbox_get_object(object_type: str, object_id: int) -> dict[str, Any]:
    """Retrieve a single NetBox object by its ID.

    Args:
        object_type: The NetBox object type in 'app.resource' format.
            Examples: 'dcim.devices', 'ipam.ip-addresses', 'dcim.sites'.
        object_id: The numeric ID of the object.

    Returns:
        The full object representation as a dict.
    """
    client = get_client()
    return client.get_object(object_type, object_id)


# ---------------------------------------------------------------------------
# Tool: Create object
# ---------------------------------------------------------------------------

@mcp.tool()
def netbox_create_object(
    object_type: str,
    data: dict[str, Any],
) -> dict[str, Any]:
    """Create a new NetBox object.

    Args:
        object_type: The NetBox object type in 'app.resource' format.
            Examples: 'dcim.devices', 'ipam.ip-addresses', 'dcim.sites'.
        data: A dict of fields for the new object. Required fields vary by type.
            Examples:
            - Site: {"name": "NYC-DC1", "slug": "nyc-dc1", "status": "active"}
            - Device: {"name": "router01", "role": 1, "device_type": 1, "site": 1}
            - IP: {"address": "10.0.0.1/24", "status": "active"}
            - Prefix: {"prefix": "10.0.0.0/24", "status": "active"}
            - VLAN: {"vid": 100, "name": "Management", "status": "active"}
            - Interface: {"device": 1, "name": "eth0", "type": "1000base-t"}
            - Cable: {"a_terminations": [{"object_type": "dcim.interface", "object_id": 1}],
                      "b_terminations": [{"object_type": "dcim.interface", "object_id": 2}]}
            - Tenant: {"name": "Acme Corp", "slug": "acme-corp"}
            - Circuit: {"cid": "CIR-001", "provider": 1, "type": 1}
            - VM: {"name": "vm01", "cluster": 1, "status": "active"}

    Returns:
        The created object as a dict (including its new ID).
    """
    client = get_client()
    return client.create_object(object_type, data)


# ---------------------------------------------------------------------------
# Tool: Update object
# ---------------------------------------------------------------------------

@mcp.tool()
def netbox_update_object(
    object_type: str,
    object_id: int,
    data: dict[str, Any],
    partial: bool = True,
) -> dict[str, Any]:
    """Update an existing NetBox object.

    Args:
        object_type: The NetBox object type in 'app.resource' format.
            Examples: 'dcim.devices', 'ipam.ip-addresses', 'dcim.sites'.
        object_id: The numeric ID of the object to update.
        data: A dict of fields to update.
            Examples: {"status": "planned"}, {"name": "new-name"},
            {"description": "Updated description", "tags": [{"name": "prod"}]}.
        partial: If True (default), use PATCH (only send changed fields).
            If False, use PUT (must send ALL required fields).

    Returns:
        The updated object as a dict.
    """
    client = get_client()
    return client.update_object(object_type, object_id, data, partial=partial)


# ---------------------------------------------------------------------------
# Tool: Delete object
# ---------------------------------------------------------------------------

@mcp.tool()
def netbox_delete_object(object_type: str, object_id: int) -> dict[str, str]:
    """Delete a NetBox object.

    Args:
        object_type: The NetBox object type in 'app.resource' format.
            Examples: 'dcim.devices', 'ipam.ip-addresses', 'dcim.sites'.
        object_id: The numeric ID of the object to delete.

    Returns:
        A confirmation dict with status, object_type, and id.
    """
    client = get_client()
    return client.delete_object(object_type, object_id)


# ---------------------------------------------------------------------------
# Tool: List available object types
# ---------------------------------------------------------------------------

@mcp.tool()
def netbox_list_object_types(app: str | None = None) -> dict[str, list[str]]:
    """List all supported NetBox object types, optionally filtered by app.

    Args:
        app: Optional app name to filter by.
            Valid apps: 'dcim', 'ipam', 'circuits', 'tenancy',
            'virtualization', 'wireless', 'vpn', 'extras', 'core', 'users'.

    Returns:
        A dict mapping app names to lists of object type strings.
    """
    result: dict[str, list[str]] = {}
    for obj_type in sorted(OBJECT_TYPES):
        obj_app, _ = obj_type.split(".", 1)
        if app and obj_app != app:
            continue
        result.setdefault(obj_app, []).append(obj_type)
    return result


# ---------------------------------------------------------------------------
# Tool: Get available prefixes/IPs (IPAM special endpoints)
# ---------------------------------------------------------------------------

@mcp.tool()
def netbox_get_available(
    resource_type: str,
    resource_id: int,
    available_type: str,
    limit: int = 50,
) -> list[dict[str, Any]] | dict[str, Any]:
    """Get available (unallocated) child resources from IPAM.

    Args:
        resource_type: The parent resource type. One of:
            'ipam.prefixes', 'ipam.ip-ranges', 'ipam.vlan-groups', 'ipam.asn-ranges'.
        resource_id: The numeric ID of the parent resource.
        available_type: What to list as available. One of:
            'prefixes' (for ipam.prefixes parents),
            'ips' (for ipam.prefixes or ipam.ip-ranges parents),
            'vlans' (for ipam.vlan-groups parents),
            'asns' (for ipam.asn-ranges parents).
        limit: Maximum number of results (default 50).

    Returns:
        A list of available resources or a paginated response dict.
    """
    client = get_client()
    path_map = {
        "ipam.prefixes": "ipam/prefixes",
        "ipam.ip-ranges": "ipam/ip-ranges",
        "ipam.vlan-groups": "ipam/vlan-groups",
        "ipam.asn-ranges": "ipam/asn-ranges",
    }
    base = path_map.get(resource_type)
    if base is None:
        raise ValueError(
            f"resource_type must be one of: {', '.join(sorted(path_map))}"
        )
    valid_available = {
        "ipam.prefixes": ("prefixes", "ips"),
        "ipam.ip-ranges": ("ips",),
        "ipam.vlan-groups": ("vlans",),
        "ipam.asn-ranges": ("asns",),
    }
    if available_type not in valid_available[resource_type]:
        raise ValueError(
            f"For {resource_type}, available_type must be one of: "
            f"{', '.join(valid_available[resource_type])}"
        )
    url = f"{base}/{resource_id}/available-{available_type}/"
    resp = client.client.get(url, params={"limit": limit})
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Tool: Create available (allocate from pool)
# ---------------------------------------------------------------------------

@mcp.tool()
def netbox_create_available(
    resource_type: str,
    resource_id: int,
    available_type: str,
    data: dict[str, Any],
) -> dict[str, Any] | list[dict[str, Any]]:
    """Allocate the next available resource from a pool (prefix, IP, VLAN, ASN).

    Args:
        resource_type: The parent resource type. One of:
            'ipam.prefixes', 'ipam.ip-ranges', 'ipam.vlan-groups', 'ipam.asn-ranges'.
        resource_id: The numeric ID of the parent resource.
        available_type: What to allocate. One of:
            'prefixes' (allocate a child prefix),
            'ips' (allocate an IP address),
            'vlans' (allocate a VLAN),
            'asns' (allocate an ASN).
        data: Parameters for allocation.
            For prefixes: {"prefix_length": 28} or {"prefix_length": 28, "description": "New subnet"}
            For ips: {"description": "New host"} or {"status": "active"}
            For vlans: {"name": "NewVLAN", "status": "active"}
            For asns: {"description": "New ASN"}

    Returns:
        The newly created/allocated object(s).
    """
    client = get_client()
    path_map = {
        "ipam.prefixes": "ipam/prefixes",
        "ipam.ip-ranges": "ipam/ip-ranges",
        "ipam.vlan-groups": "ipam/vlan-groups",
        "ipam.asn-ranges": "ipam/asn-ranges",
    }
    base = path_map.get(resource_type)
    if base is None:
        raise ValueError(
            f"resource_type must be one of: {', '.join(sorted(path_map))}"
        )
    url = f"{base}/{resource_id}/available-{available_type}/"
    resp = client.client.post(url, json=data)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="NetBox MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="MCP transport type (default: stdio)",
    )
    parser.add_argument("--host", default="127.0.0.1", help="HTTP host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="HTTP port (default: 8000)")
    parser.add_argument("--netbox-url", help="NetBox URL (overrides env)")
    parser.add_argument("--netbox-token", help="NetBox API token (overrides env)")
    parser.add_argument("--no-verify-ssl", action="store_true", help="Disable SSL verification")
    args = parser.parse_args()

    global settings
    if args.netbox_url:
        settings.netbox_url = args.netbox_url
    if args.netbox_token:
        settings.netbox_token = SecretStr(args.netbox_token)
    if args.no_verify_ssl:
        settings.verify_ssl = False

    if args.transport == "sse":
        mcp.run(transport="sse", host=args.host, port=args.port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
