# Akamai Edge Diagnostics MCP Server

A Model Context Protocol (MCP) server implementation for Akamai Edge Diagnostics API, providing comprehensive diagnostic tools for troubleshooting and analyzing edge server behavior.

## Features

This MCP server implements the full Akamai Edge Diagnostics API suite, providing access to:

### IP Operations

- **IP Verification**: Verify if an IP is an Akamai edge server
- **IP Location**: Get geographical and network information for IPs
- **Combined Verification & Location**: Single operation for both verification and location

### Network Diagnostics

- **Dig**: DNS query tool for domain information
- **MTR**: Network connectivity testing with traceroute
- **CURL**: Execute HTTP requests from edge servers
- **GREP**: Access and search edge server logs

### Edge Server Information

- **Edge Locations**: List all available edge server locations
- **GTM Properties**: List Global Traffic Management properties
- **GTM Property IPs**: Get test and target IPs for GTM hostnames
- **IPA Hostnames**: List IP Acceleration hostnames

### Advanced Diagnostics

- **Metadata Tracer**: Trace and analyze edge behavior for URLs
- **Error Statistics**: Get error statistics for specific URLs
- **Error Translator**: Decode and explain Akamai error codes
- **URL Health Check**: Comprehensive health check for URLs
- **ARL Translator**: Translate Akamaized URLs

### Diagnostic Scenarios

- **Connectivity Problems**: Diagnose connectivity issues
- **Content Problems**: Diagnose content delivery issues
- **User Diagnostic Data**: Generate diagnostic links and collect user data

## Installation

1. Install required dependencies:

```bash
pip install -r requirements.txt
```

2. Ensure your `~/.edgerc` file is configured with valid Akamai credentials:

```ini
[default]
client_secret = your_client_secret
host = your_host.akamaiapis.net
access_token = your_access_token
client_token = your_client_token
```

## Usage

### Running the Server

```bash
python edge_diagnostics_server.py
```

### Available Tools

#### IP Verification & Location

```python
# Verify if IP is an Akamai edge server
verify_edge_ip(ip="1.2.3.4")

# Get IP location information
locate_ip(ip="1.2.3.4")

# Both verification and location
verify_locate_ip(ip="1.2.3.4")
```

#### Network Diagnostics

```python
# DNS lookup
execute_dig(hostname="example.com", query_type="A", location="optional_location")

# Network connectivity test
execute_mtr(destination="example.com", source="optional_source")

# Execute cURL request
execute_curl(url="https://example.com", request_headers=[{"name": "User-Agent", "value": "Custom"}])

# Get edge logs
launch_grep(hostname="example.com", log_type="r")
get_grep_status(request_id="request_id_here")
```

#### Advanced Diagnostics

```python
# Trace metadata
launch_metadata_tracer(url="https://example.com", request_headers=[...])
get_metadata_tracer_status(request_id="request_id_here")

# Get error statistics
get_error_statistics(url="https://example.com", cp_code=12345)

# Translate error codes
translate_error(error_string="9.12a34bc.1234567890.123")

# Translate Akamaized URL
translate_url(url="https://example.akamaized.net/path")

# URL health check
launch_url_health_check(url="https://example.com", request_headers=[...])
get_url_health_check_status(request_id="request_id_here")
```

#### Diagnostic Scenarios

```python
# Diagnose connectivity problems
launch_connectivity_problems(url="https://example.com", client_location={...})
get_connectivity_problems_status(request_id="request_id_here")

# Diagnose content problems
launch_content_problems(url="https://example.com", request_headers=[...])
get_content_problems_status(request_id="request_id_here")
```

#### Information Retrieval

```python
# List edge server locations
list_edge_locations()

# List GTM properties
list_gtm_properties()

# Get GTM property IPs
get_gtm_property_ips(property="property_name", domain="akadns.net")

# List IPA hostnames
list_ipa_hostnames()
```

#### User Diagnostic Data

```python
# Generate diagnostic link
generate_diagnostic_link(url="https://example.com", note="Optional note")

# Get diagnostic data
get_diagnostic_data(group_id="group_id_here")
```

### Available Resources

Access resources directly via URI:

- `edge-diagnostics://locations` - Edge server locations
- `edge-diagnostics://gtm-properties` - GTM properties
- `edge-diagnostics://ipa-hostnames` - IPA hostnames
- `edge-diagnostics://user-diagnostic-groups` - User diagnostic groups

## Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "edge-diagnostics": {
      "command": "python",
      "args": ["/path/to/edge_diagnostics_server.py"],
      "env": {}
    }
  }
}
```

## API Reference

This server implements the Akamai Edge Diagnostics API v1. For detailed API documentation, see:
https://techdocs.akamai.com/edge-diagnostics/reference/api-summary

## Asynchronous Operations

Many diagnostic operations are asynchronous. The typical flow is:

1. Launch the operation (returns a `request_id`)
2. Poll for status using the `request_id`
3. Retrieve results when status shows completion

Operations with asynchronous support:

- Metadata Tracer
- GREP
- URL Health Check
- Connectivity Problems
- Content Problems

## Error Handling

All operations include comprehensive error handling with detailed error messages. Errors are logged and returned in a structured format.

## Security

- Credentials are read from `~/.edgerc` and never exposed
- EdgeGrid authentication is used for all API calls
- No credentials are stored in the codebase

## License

This is an unofficial MCP server implementation for Akamai Edge Diagnostics API.
