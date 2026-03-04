# NetBox MCP Server

A full CRUD [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) server for [NetBox](https://netbox.dev/) built with [FastMCP](https://github.com/jlowin/fastmcp). Provides 8 tools covering **119 object types** across all 10 NetBox API apps.

## Tools

| Tool | Method | Description |
|---|---|---|
| `netbox_list_objects` | GET | List, filter, and paginate any object type |
| `netbox_get_object` | GET | Retrieve a single object by ID |
| `netbox_create_object` | POST | Create a new object |
| `netbox_update_object` | PATCH/PUT | Update an existing object |
| `netbox_delete_object` | DELETE | Delete an object |
| `netbox_list_object_types` | — | Discover all supported object types |
| `netbox_get_available` | GET | List available IPs, prefixes, VLANs, or ASNs |
| `netbox_create_available` | POST | Allocate next available from a pool |

## Supported Object Types

119 resources across 10 apps:

- **dcim** (44) — sites, devices, interfaces, racks, cables, manufacturers, platforms, and more
- **ipam** (18) — prefixes, ip-addresses, vlans, vrfs, asns, services, and more
- **circuits** (11) — providers, circuits, terminations, virtual circuits
- **vpn** (10) — tunnels, ike/ipsec policies, l2vpns
- **extras** (13) — tags, custom fields, webhooks, config contexts
- **tenancy** (6) — tenants, contacts
- **virtualization** (6) — clusters, virtual machines, VM interfaces
- **core** (4) — data sources, jobs, object changes
- **users** (4) — users, groups, tokens, permissions
- **wireless** (3) — wireless LANs, wireless links

## Prerequisites

- Python 3.11+
- A running NetBox instance
- A NetBox API token (with read/write permissions for full CRUD)

## Installation

```bash
# Clone the repo
git clone https://github.com/your-username/NetBox_MCP.git
cd NetBox_MCP

# Create a virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install the package
pip install -e .
```

## Configuration

Copy the example env file and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:

```
NETBOX_URL=https://your-netbox-instance.example.com
NETBOX_TOKEN=your-api-token-here
VERIFY_SSL=true
```

You can also pass these as CLI arguments:

```bash
netbox-mcp-server --netbox-url https://netbox.example.com --netbox-token your-token
```

## Running the Server

### stdio (default — for Claude Desktop, Claude Code, etc.)

```bash
source .venv/bin/activate
netbox-mcp-server
```

### SSE (HTTP transport)

```bash
netbox-mcp-server --transport sse --host 127.0.0.1 --port 8000
```

## Claude Desktop Integration

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "netbox": {
      "command": "/absolute/path/to/NetBox_MCP/.venv/bin/netbox-mcp-server",
      "env": {
        "NETBOX_URL": "https://your-netbox-instance.example.com",
        "NETBOX_TOKEN": "your-api-token-here"
      }
    }
  }
}
```

## Claude Code Integration

Add the MCP server to Claude Code:

```bash
claude mcp add netbox -- /absolute/path/to/NetBox_MCP/.venv/bin/netbox-mcp-server
```

Or with environment variables:

```bash
claude mcp add netbox -e NETBOX_URL=https://netbox.example.com -e NETBOX_TOKEN=your-token -- /absolute/path/to/NetBox_MCP/.venv/bin/netbox-mcp-server
```

## Usage Examples

Once connected, an LLM can use the tools like this:

**List all active devices:**
```
netbox_list_objects(object_type="dcim.devices", filters={"status": "active"})
```

**Get a specific site:**
```
netbox_get_object(object_type="dcim.sites", object_id=1)
```

**Create a new prefix:**
```
netbox_create_object(object_type="ipam.prefixes", data={"prefix": "10.0.0.0/24", "status": "active"})
```

**Update a device:**
```
netbox_update_object(object_type="dcim.devices", object_id=42, data={"status": "planned"})
```

**Delete a VLAN:**
```
netbox_delete_object(object_type="ipam.vlans", object_id=100)
```

**Allocate next available IP from a prefix:**
```
netbox_create_available(resource_type="ipam.prefixes", resource_id=5, available_type="ips", data={"description": "New host"})
```

**Discover object types:**
```
netbox_list_object_types(app="dcim")
```

## License

See [LICENSE](LICENSE) for details.
