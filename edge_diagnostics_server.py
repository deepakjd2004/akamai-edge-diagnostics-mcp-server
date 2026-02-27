#!/usr/bin/env python3
"""
Akamai Edge Diagnostics MCP Server
Implements Edge Diagnostics API capabilities from https://techdocs.akamai.com/edge-diagnostics/reference/api-summary
Reads credentials from ~/.edgerc file 
"""

import asyncio
import json
import logging
from os.path import expanduser
from urllib.parse import urljoin
from typing import Any, Dict, List, Optional

import requests
from akamai.edgegrid import EdgeGridAuth, EdgeRc
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)

# Edge Diagnostics API endpoints
EDGE_LOCATIONS_ENDPOINT = "/edge-diagnostics/v1/edge-locations"
VERIFY_IP_ENDPOINT = "/edge-diagnostics/v1/verify-edge-ip"
LOCATE_IP_ENDPOINT = "/edge-diagnostics/v1/locate-ip"
VERIFY_LOCATE_IP_ENDPOINT = "/edge-diagnostics/v1/verify-locate-ip"
GTM_PROPERTIES_ENDPOINT = "/edge-diagnostics/v1/gtm/gtm-properties"
IPA_HOSTNAMES_ENDPOINT = "/edge-diagnostics/v1/ipa/hostnames"
ERROR_TRANSLATOR_ENDPOINT = "/edge-diagnostics/v1/error-translator"
TRANSLATED_URL_ENDPOINT = "/edge-diagnostics/v1/translated-url"
METADATA_TRACER_ENDPOINT = "/edge-diagnostics/v1/metadata-tracer"
ESTATS_ENDPOINT = "/edge-diagnostics/v1/estats"
CURL_ENDPOINT = "/edge-diagnostics/v1/curl"
DIG_ENDPOINT = "/edge-diagnostics/v1/dig"
MTR_ENDPOINT = "/edge-diagnostics/v1/mtr"
GREP_ENDPOINT = "/edge-diagnostics/v1/grep"
URL_HEALTH_CHECK_ENDPOINT = "/edge-diagnostics/v1/url-health-check"
CONNECTIVITY_PROBLEMS_ENDPOINT = "/edge-diagnostics/v1/connectivity-problems"
CONTENT_PROBLEMS_ENDPOINT = "/edge-diagnostics/v1/content-problems"
USER_DIAGNOSTIC_DATA_ENDPOINT = "/edge-diagnostics/v1/user-diagnostic-data/groups"
ESI_DEBUGGER_ENDPOINT = "/edge-diagnostics/v1/esi-debugger-api/v1/debug"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("edge-diagnostics-mcp")

class EdgeDiagnosticsClient:
    """Edge Diagnostics API client using EdgeGrid authentication from ~/.edgerc"""
    
    def __init__(self, section: str = 'default'):
        """
        Initialize Edge Diagnostics client with credentials from ~/.edgerc
        
        Args:
            section: Section name in .edgerc file (default: 'default')
        """
        self.section = section
        self.session = None
        self.base_url = None
        self._initialize_session()
    
    def _initialize_session(self):
        """Initialize requests session with EdgeGrid authentication"""
        try:
            # Read credentials from ~/.edgerc
            edgerc_path = expanduser("~/.edgerc")
            edgerc = EdgeRc(edgerc_path)
            
            # Get credentials for the specified section
            client_token = edgerc.get(self.section, 'client_token')
            client_secret = edgerc.get(self.section, 'client_secret')
            access_token = edgerc.get(self.section, 'access_token')
            host = edgerc.get(self.section, 'host')
            
            # Create authenticated session
            self.session = requests.Session()
            self.session.auth = EdgeGridAuth(
                client_token=client_token,
                client_secret=client_secret,
                access_token=access_token
            )
            
            # Set base URL
            self.base_url = f"https://{host}"
            
            logger.info(f"Initialized Edge Diagnostics client for section '{self.section}'")
            
        except Exception as e:
            logger.error(f"Failed to initialize Edge Diagnostics client: {e}")
            raise
    
    def _build_params(self, account_switch_key: Optional[str] = None) -> Dict[str, str]:
        """Build query parameters with optional accountSwitchKey"""
        params = {}
        if account_switch_key:
            params['accountSwitchKey'] = account_switch_key
        return params
    
    def get_edge_locations(self, account_switch_key: Optional[str] = None) -> Dict[str, Any]:
        """List available edge server locations"""
        try:
            url = urljoin(self.base_url, EDGE_LOCATIONS_ENDPOINT)
            params = self._build_params(account_switch_key)
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting edge locations: {e}")
            raise
    
    def verify_edge_ip(self, ip: str, account_switch_key: Optional[str] = None) -> Dict[str, Any]:
        """Verify if an IP is an Akamai edge server IP"""
        try:
            url = urljoin(self.base_url, VERIFY_IP_ENDPOINT)
            params = self._build_params(account_switch_key)
            payload = {"ipAddresses": [ip]}
            logger.info(f"Making request to: {url} with params: {params}")
            response = self.session.post(url, params=params, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error verifying IP: {e}")
            raise
    
    def locate_ip(self, ip: str, account_switch_key: Optional[str] = None) -> Dict[str, Any]:
        """Locate an IP network"""
        try:
            url = urljoin(self.base_url, LOCATE_IP_ENDPOINT)
            params = self._build_params(account_switch_key)
            payload = {"ipAddresses": [ip]}
            response = self.session.post(url, params=params, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error locating IP: {e}")
            raise
    
    def verify_locate_ip(self, ip: str, account_switch_key: Optional[str] = None) -> Dict[str, Any]:
        """Verify and locate an IP"""
        try:
            url = urljoin(self.base_url, VERIFY_LOCATE_IP_ENDPOINT)
            params = self._build_params(account_switch_key)
            payload = {"ipAddress": ip}
            response = self.session.post(url, params=params, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error verifying and locating IP: {e}")
            raise
    
    def get_gtm_properties(self) -> Dict[str, Any]:
        """List GTM properties"""
        try:
            url = urljoin(self.base_url, GTM_PROPERTIES_ENDPOINT)
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting GTM properties: {e}")
            raise
    
    def get_gtm_property_ips(self, property_name: str, domain: str) -> Dict[str, Any]:
        """List test and target IPs for a GTM hostname"""
        try:
            url = urljoin(self.base_url, f"/edge-diagnostics/v1/gtm/{property_name}/{domain}/gtm-property-ips")
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting GTM property IPs: {e}")
            raise
    
    def get_ipa_hostnames(self) -> Dict[str, Any]:
        """List IP acceleration hostnames"""
        try:
            url = urljoin(self.base_url, IPA_HOSTNAMES_ENDPOINT)
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting IPA hostnames: {e}")
            raise
    
    def translate_error(self, error_string: str, account_switch_key: Optional[str] = None) -> Dict[str, Any]:
        """Translate error string"""
        try:
            url = urljoin(self.base_url, ERROR_TRANSLATOR_ENDPOINT)
            params = self._build_params(account_switch_key)
            payload = {"errorCode": error_string}
            response = self.session.post(url, params=params, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error translating error: {e}")
            raise
    
    def get_error_translator_status(self, request_id: str) -> Dict[str, Any]:
        """Get a translate error string response"""
        try:
            url = urljoin(self.base_url, f"{ERROR_TRANSLATOR_ENDPOINT}/requests/{request_id}")
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting error translator status: {e}")
            raise
    
    def translate_url(self, url_to_translate: str) -> Dict[str, Any]:
        """Translate an Akamaized URL (ARL translator)"""
        try:
            url = urljoin(self.base_url, TRANSLATED_URL_ENDPOINT)
            payload = {"url": url_to_translate}
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error translating URL: {e}")
            raise
    
    def launch_metadata_tracer(self, url: str, request_headers: Optional[List[Dict]] = None, account_switch_key: Optional[str] = None) -> Dict[str, Any]:
        """Launch a metadata tracing request"""
        try:
            endpoint = urljoin(self.base_url, METADATA_TRACER_ENDPOINT)
            params = self._build_params(account_switch_key)
            payload = {"url": url}
            if request_headers:
                payload["requestHeaders"] = request_headers
            response = self.session.post(endpoint, params=params, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                raise Exception(f"403 Forbidden - Your API credentials don't have access to Metadata Tracer. This API requires specific entitlements. Contact your Akamai account team to request access.")
            logger.error(f"Error launching metadata tracer: {e}")
            raise
        except Exception as e:
            logger.error(f"Error launching metadata tracer: {e}")
            raise
    
    def get_metadata_tracer_status(self, request_id: str, account_switch_key: Optional[str] = None) -> Dict[str, Any]:
        """Check a metadata tracing request status"""
        try:
            url = urljoin(self.base_url, f"{METADATA_TRACER_ENDPOINT}/requests/{request_id}")
            params = self._build_params(account_switch_key)
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting metadata tracer status: {e}")
            raise
    
    def get_error_statistics(self, url: str, cp_code: Optional[int] = None) -> Dict[str, Any]:
        """Get error statistics"""
        try:
            endpoint = urljoin(self.base_url, ESTATS_ENDPOINT)
            payload = {"url": url}
            if cp_code:
                payload["cpCode"] = cp_code
            response = self.session.post(endpoint, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting error statistics: {e}")
            raise
    
    def execute_curl(self, url: str, request_headers: Optional[List[Dict]] = None, account_switch_key: Optional[str] = None) -> Dict[str, Any]:
        """Request content with cURL"""
        try:
            endpoint = urljoin(self.base_url, CURL_ENDPOINT)
            params = self._build_params(account_switch_key)
            payload = {"url": url}
            if request_headers:
                payload["requestHeaders"] = request_headers
            response = self.session.post(endpoint, params=params, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error executing cURL: {e}")
            raise
    
    def execute_dig(self, hostname: str, query_type: str = "A", is_gtm_hostname: bool = False, edge_location_id: Optional[str] = None, edge_ip: Optional[str] = None, account_switch_key: Optional[str] = None) -> Dict[str, Any]:
        """Get domain details with dig"""
        try:
            endpoint = urljoin(self.base_url, DIG_ENDPOINT)
            params = self._build_params(account_switch_key)
            payload = {
                "hostname": hostname,
                "queryType": query_type,
                "isGtmHostname": is_gtm_hostname
            }
            if edge_location_id:
                payload["edgeLocationId"] = edge_location_id
            if edge_ip:
                payload["edgeIp"] = edge_ip
            response = self.session.post(endpoint, params=params, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error executing dig: {e}")
            raise
    
    def execute_mtr(self, destination: str, source: Optional[str] = None) -> Dict[str, Any]:
        """Test network connectivity with MTR"""
        try:
            endpoint = urljoin(self.base_url, MTR_ENDPOINT)
            payload = {"destination": destination}
            if source:
                payload["source"] = source
            response = self.session.post(endpoint, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error executing MTR: {e}")
            raise
    
    def launch_grep(self, hostname: str, log_type: str = "r") -> Dict[str, Any]:
        """Launch a GREP request to get specific logs"""
        try:
            endpoint = urljoin(self.base_url, GREP_ENDPOINT)
            payload = {
                "hostname": hostname,
                "logType": log_type
            }
            response = self.session.post(endpoint, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error launching GREP: {e}")
            raise
    
    def get_grep_status(self, request_id: str) -> Dict[str, Any]:
        """Check a GREP request status"""
        try:
            url = urljoin(self.base_url, f"{GREP_ENDPOINT}/requests/{request_id}")
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting GREP status: {e}")
            raise
    
    def launch_url_health_check(self, url: str, request_headers: Optional[List[Dict]] = None, edge_location_id: Optional[str] = None, ip_version: Optional[str] = None, packet_type: Optional[str] = None, port: Optional[int] = None, query_type: Optional[str] = None, run_from_site_shield: Optional[bool] = None, sensitive_request_header_keys: Optional[List[str]] = None, spoof_edge_ip: Optional[str] = None, views_allowed: Optional[List[str]] = None, account_switch_key: Optional[str] = None) -> Dict[str, Any]:
        """Run the URL health check"""
        try:
            endpoint = urljoin(self.base_url, URL_HEALTH_CHECK_ENDPOINT)
            params = self._build_params(account_switch_key)
            payload = {"url": url}
            if request_headers:
                payload["requestHeaders"] = request_headers
            if edge_location_id:
                payload["edgeLocationId"] = edge_location_id
            if ip_version:
                payload["ipVersion"] = ip_version
            if packet_type:
                payload["packetType"] = packet_type
            if port is not None:
                payload["port"] = port
            if query_type:
                payload["queryType"] = query_type
            if run_from_site_shield is not None:
                payload["runFromSiteShield"] = run_from_site_shield
            if sensitive_request_header_keys:
                payload["sensitiveRequestHeaderKeys"] = sensitive_request_header_keys
            if spoof_edge_ip:
                payload["spoofEdgeIp"] = spoof_edge_ip
            if views_allowed:
                payload["viewsAllowed"] = views_allowed
            response = self.session.post(endpoint, params=params, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                raise Exception(f"403 Forbidden - Your API credentials may not have access to URL Health Check. Check your entitlements.")
            logger.error(f"Error launching URL health check: {e}")
            raise
        except Exception as e:
            logger.error(f"Error launching URL health check: {e}")
            raise
    
    def get_url_health_check_status(self, request_id: str, account_switch_key: Optional[str] = None) -> Dict[str, Any]:
        """Get a URL health check response"""
        try:
            url = urljoin(self.base_url, f"{URL_HEALTH_CHECK_ENDPOINT}/requests/{request_id}")
            params = self._build_params(account_switch_key)
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting URL health check status: {e}")
            raise
    
    def launch_connectivity_problems(self, url: str, client_location: Optional[Dict] = None) -> Dict[str, Any]:
        """Run the Connectivity problems scenario"""
        try:
            endpoint = urljoin(self.base_url, CONNECTIVITY_PROBLEMS_ENDPOINT)
            payload = {"url": url}
            if client_location:
                payload["clientLocation"] = client_location
            response = self.session.post(endpoint, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error launching connectivity problems check: {e}")
            raise
    
    def get_connectivity_problems_status(self, request_id: str) -> Dict[str, Any]:
        """Get the Connectivity problems scenario response"""
        try:
            url = urljoin(self.base_url, f"{CONNECTIVITY_PROBLEMS_ENDPOINT}/{request_id}")
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting connectivity problems status: {e}")
            raise
    
    def launch_content_problems(self, url: str, request_headers: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Run the Content problems scenario"""
        try:
            endpoint = urljoin(self.base_url, CONTENT_PROBLEMS_ENDPOINT)
            payload = {"url": url}
            if request_headers:
                payload["requestHeaders"] = request_headers
            response = self.session.post(endpoint, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error launching content problems check: {e}")
            raise
    
    def get_content_problems_status(self, request_id: str) -> Dict[str, Any]:
        """Get the Content problems scenario response"""
        try:
            url = urljoin(self.base_url, f"{CONTENT_PROBLEMS_ENDPOINT}/{request_id}")
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting content problems status: {e}")
            raise
    
    def get_user_diagnostic_groups(self, account_switch_key: Optional[str] = None) -> Dict[str, Any]:
        """List user diagnostic data groups"""
        try:
            url = urljoin(self.base_url, USER_DIAGNOSTIC_DATA_ENDPOINT)
            params = self._build_params(account_switch_key)
            logger.info(f"Making request to: {url} with params: {params}")
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting user diagnostic groups: {e}")
            raise
    
    def generate_diagnostic_link(self, url: str, note: Optional[str] = None, account_switch_key: Optional[str] = None) -> Dict[str, Any]:
        """Generate a diagnostic link"""
        try:
            endpoint = urljoin(self.base_url, USER_DIAGNOSTIC_DATA_ENDPOINT)
            params = self._build_params(account_switch_key)
            payload = {"url": url}
            if note:
                payload["note"] = note
            logger.info(f"Making request to: {endpoint} with params: {params}")
            response = self.session.post(endpoint, params=params, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error generating diagnostic link: {e}")
            raise
    
    def get_diagnostic_data(self, group_id: str, account_switch_key: Optional[str] = None) -> Dict[str, Any]:
        """Get diagnostic data of a group"""
        try:
            url = urljoin(self.base_url, f"{USER_DIAGNOSTIC_DATA_ENDPOINT}/{group_id}/records")
            params = self._build_params(account_switch_key)
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting diagnostic data: {e}")
            raise

# Initialize Edge Diagnostics client
edge_client = EdgeDiagnosticsClient()

# Create the server instance
server = Server("edge-diagnostics-mcp")

@server.list_resources()
async def handle_list_resources() -> List[Resource]:
    """List available Edge Diagnostics resources"""
    return [
        Resource(
            uri="edge-diagnostics://locations",
            name="Edge Server Locations",
            description="List all available edge server locations",
            mimeType="application/json",
        ),
        Resource(
            uri="edge-diagnostics://gtm-properties",
            name="GTM Properties",
            description="List all GTM properties",
            mimeType="application/json",
        ),
        Resource(
            uri="edge-diagnostics://ipa-hostnames",
            name="IPA Hostnames",
            description="List all IP acceleration hostnames",
            mimeType="application/json",
        ),
        Resource(
            uri="edge-diagnostics://user-diagnostic-groups",
            name="User Diagnostic Groups",
            description="List all user diagnostic data groups",
            mimeType="application/json",
        ),
    ]

@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read a specific Edge Diagnostics resource"""
    try:
        if uri == "edge-diagnostics://locations":
            data = edge_client.get_edge_locations()
            return json.dumps(data, indent=2)
        elif uri == "edge-diagnostics://gtm-properties":
            data = edge_client.get_gtm_properties()
            return json.dumps(data, indent=2)
        elif uri == "edge-diagnostics://ipa-hostnames":
            data = edge_client.get_ipa_hostnames()
            return json.dumps(data, indent=2)
        elif uri == "edge-diagnostics://user-diagnostic-groups":
            data = edge_client.get_user_diagnostic_groups()
            return json.dumps(data, indent=2)
        else:
            raise ValueError(f"Unknown resource: {uri}")
    except Exception as e:
        logger.error(f"Error reading resource {uri}: {e}")
        return json.dumps({"error": str(e)})

# List available tools - Capabilities of MCP Server. AI client read this to know what tools are available
@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools"""
    return [
        Tool(
            name="verify_edge_ip",
            description="Verify if an IP address is an Akamai edge server IP",
            inputSchema={
                "type": "object",
                "properties": {
                    "ip": {
                        "type": "string",
                        "description": "IP address to verify",
                    },
                    "account_switch_key": {
                        "type": "string",
                        "description": "Optional account switch key for multi-account access",
                    },
                },
                "required": ["ip"],
            },
        ),
        Tool(
            name="locate_ip",
            description="Locate an IP network and get geographical information",
            inputSchema={
                "type": "object",
                "properties": {
                    "ip": {
                        "type": "string",
                        "description": "IP address to locate",
                    },
                    "account_switch_key": {
                        "type": "string",
                        "description": "Optional account switch key for multi-account access",
                    },
                },
                "required": ["ip"],
            },
        ),
        Tool(
            name="verify_locate_ip",
            description="Verify if an IP is an Akamai edge server and get its location",
            inputSchema={
                "type": "object",
                "properties": {
                    "ip": {
                        "type": "string",
                        "description": "IP address to verify and locate",
                    },
                    "account_switch_key": {
                        "type": "string",
                        "description": "Optional account switch key for multi-account access",
                    },
                },
                "required": ["ip"],
            },
        ),
        Tool(
            name="list_edge_locations",
            description="List all available edge server locations",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="list_gtm_properties",
            description="List all GTM (Global Traffic Management) properties",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_gtm_property_ips",
            description="Get test and target IPs for a specific GTM hostname",
            inputSchema={
                "type": "object",
                "properties": {
                    "property": {
                        "type": "string",
                        "description": "GTM property name",
                    },
                    "domain": {
                        "type": "string",
                        "description": "GTM domain",
                    },
                },
                "required": ["property", "domain"],
            },
        ),
        Tool(
            name="list_ipa_hostnames",
            description="List all IP acceleration hostnames",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="translate_error",
            description="Translate an Akamai error string to get detailed information (async - returns request_id)",
            inputSchema={
                "type": "object",
                "properties": {
                    "error_string": {
                        "type": "string",
                        "description": "Error string to translate",
                    },
                    "account_switch_key": {
                        "type": "string",
                        "description": "Optional account switch key for multi-account access",
                    },
                },
                "required": ["error_string"],
            },
        ),
        Tool(
            name="get_error_translator_status",
            description="Get the status and result of an error translation request",
            inputSchema={
                "type": "object",
                "properties": {
                    "request_id": {
                        "type": "string",
                        "description": "Request ID from translate_error",
                    },
                },
                "required": ["request_id"],
            },
        ),
        Tool(
            name="translate_url",
            description="Translate an Akamaized URL using ARL translator",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to translate",
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="launch_metadata_tracer",
            description="Launch a metadata tracing request to analyze edge behavior",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to trace",
                    },
                    "request_headers": {
                        "type": "array",
                        "description": "Optional request headers as array of {name, value} objects",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "value": {"type": "string"}
                            }
                        }
                    },
                    "account_switch_key": {
                        "type": "string",
                        "description": "Optional account switch key for multi-account access",
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="get_metadata_tracer_status",
            description="Check the status of a metadata tracing request",
            inputSchema={
                "type": "object",
                "properties": {
                    "request_id": {
                        "type": "string",
                        "description": "Request ID from launch_metadata_tracer",
                    },
                    "account_switch_key": {
                        "type": "string",
                        "description": "Optional account switch key for multi-account access",
                    },
                },
                "required": ["request_id"],
            },
        ),
        Tool(
            name="get_error_statistics",
            description="Get error statistics for a URL",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to get error statistics for",
                    },
                    "cp_code": {
                        "type": "integer",
                        "description": "Optional CP code",
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="execute_curl",
            description="Request content using cURL from Akamai edge servers",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to fetch",
                    },
                    "request_headers": {
                        "type": "array",
                        "description": "Optional request headers as array of {name, value} objects",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "value": {"type": "string"}
                            }
                        }
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="execute_dig",
            description="Get domain details using dig command from Akamai edge servers",
            inputSchema={
                "type": "object",
                "properties": {
                    "hostname": {
                        "type": "string",
                        "description": "Hostname or domain name to query",
                    },
                    "query_type": {
                        "type": "string",
                        "description": "DNS query type: A, AAAA, SOA, CNAME, PTR, MX, NS, TXT, SRV, CAA, or ANY (default: A)",
                        "default": "A",
                    },
                    "is_gtm_hostname": {
                        "type": "boolean",
                        "description": "Set to true if hostname is a GTM hostname (default: false)",
                        "default": False,
                    },
                    "edge_location_id": {
                        "type": "string",
                        "description": "Optional edge server location ID. Use list_edge_locations to get valid IDs",
                    },
                    "edge_ip": {
                        "type": "string",
                        "description": "Optional edge server IP to run dig from. Use verify_edge_ip to verify it's an edge IP",
                    },
                    "account_switch_key": {
                        "type": "string",
                        "description": "Optional account switch key for multi-account access",
                    },
                },
                "required": ["hostname"],
            },
        ),
        Tool(
            name="execute_mtr",
            description="Test network connectivity using MTR (My Traceroute)",
            inputSchema={
                "type": "object",
                "properties": {
                    "destination": {
                        "type": "string",
                        "description": "Destination IP or hostname",
                    },
                    "source": {
                        "type": "string",
                        "description": "Optional source location",
                    },
                },
                "required": ["destination"],
            },
        ),
        Tool(
            name="launch_grep",
            description="Launch a GREP request to get specific edge server logs",
            inputSchema={
                "type": "object",
                "properties": {
                    "hostname": {
                        "type": "string",
                        "description": "Hostname to get logs for",
                    },
                    "log_type": {
                        "type": "string",
                        "description": "Log type (r for request logs)",
                        "default": "r",
                    },
                },
                "required": ["hostname"],
            },
        ),
        Tool(
            name="get_grep_status",
            description="Check the status of a GREP request",
            inputSchema={
                "type": "object",
                "properties": {
                    "request_id": {
                        "type": "string",
                        "description": "Request ID from launch_grep",
                    },
                },
                "required": ["request_id"],
            },
        ),
        Tool(
            name="launch_url_health_check",
            description="Run a comprehensive URL health check",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to check",
                    },
                    "request_headers": {
                        "type": "array",
                        "description": "Optional request headers as array of {name, value} objects",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "value": {"type": "string"}
                            }
                        }
                    },
                    "edge_location_id": {
                        "type": "string",
                        "description": "Optional edge server location ID. Use list_edge_locations to get valid IDs",
                    },
                    "ip_version": {
                        "type": "string",
                        "description": "IP version for cURL and MTR: IPV4 or IPV6",
                        "enum": ["IPV4", "IPV6"],
                    },
                    "packet_type": {
                        "type": "string",
                        "description": "Packet type for MTR: ICMP or TCP (only with CONNECTIVITY in views_allowed)",
                        "enum": ["ICMP", "TCP"],
                    },
                    "port": {
                        "type": "integer",
                        "description": "Port number for MTR: 80 or 443 (only with CONNECTIVITY in views_allowed)",
                        "enum": [80, 443],
                    },
                    "query_type": {
                        "type": "string",
                        "description": "DNS query type for dig: A, AAAA, SOA, CNAME, PTR, MX, NS, TXT, SRV, CAA, or ANY",
                    },
                    "run_from_site_shield": {
                        "type": "boolean",
                        "description": "Run health check from a Site Shield map",
                    },
                    "sensitive_request_header_keys": {
                        "type": "array",
                        "description": "Sensitive request headers to not store in database",
                        "items": {"type": "string"},
                    },
                    "spoof_edge_ip": {
                        "type": "string",
                        "description": "IP of edge server to serve traffic from (from dig answerSection)",
                    },
                    "views_allowed": {
                        "type": "array",
                        "description": "Additional operations: CONNECTIVITY (MTR) and/or LOGS (GREP)",
                        "items": {"type": "string"},
                    },
                    "account_switch_key": {
                        "type": "string",
                        "description": "Optional account switch key for multi-account access",
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="get_url_health_check_status",
            description="Get the status of a URL health check",
            inputSchema={
                "type": "object",
                "properties": {
                    "request_id": {
                        "type": "string",
                        "description": "Request ID from launch_url_health_check",
                    },
                    "account_switch_key": {
                        "type": "string",
                        "description": "Optional account switch key for multi-account access",
                    },
                },
                "required": ["request_id"],
            },
        ),
        Tool(
            name="launch_connectivity_problems",
            description="Run the connectivity problems diagnostic scenario",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to diagnose",
                    },
                    "client_location": {
                        "type": "object",
                        "description": "Optional client location information",
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="get_connectivity_problems_status",
            description="Get the status of a connectivity problems diagnostic",
            inputSchema={
                "type": "object",
                "properties": {
                    "request_id": {
                        "type": "string",
                        "description": "Request ID from launch_connectivity_problems",
                    },
                },
                "required": ["request_id"],
            },
        ),
        Tool(
            name="launch_content_problems",
            description="Run the content problems diagnostic scenario",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to diagnose",
                    },
                    "request_headers": {
                        "type": "array",
                        "description": "Optional request headers as array of {name, value} objects",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "value": {"type": "string"}
                            }
                        }
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="get_content_problems_status",
            description="Get the status of a content problems diagnostic",
            inputSchema={
                "type": "object",
                "properties": {
                    "request_id": {
                        "type": "string",
                        "description": "Request ID from launch_content_problems",
                    },
                },
                "required": ["request_id"],
            },
        ),
        Tool(
            name="generate_diagnostic_link",
            description="Generate a diagnostic link for user data collection",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL for diagnostic link",
                    },
                    "note": {
                        "type": "string",
                        "description": "Optional note for the diagnostic link",
                    },
                    "account_switch_key": {
                        "type": "string",
                        "description": "Optional account switch key for multi-account access",
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="get_diagnostic_data",
            description="Get diagnostic data for a specific group",
            inputSchema={
                "type": "object",
                "properties": {
                    "group_id": {
                        "type": "string",
                        "description": "Group ID to get diagnostic data for",
                    },
                    "account_switch_key": {
                        "type": "string",
                        "description": "Optional account switch key for multi-account access",
                    },
                },
                "required": ["group_id"],
            },
        ),
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List[TextContent]:
    """Handle tool execution"""
    try:
        if name == "verify_edge_ip":
            ip = arguments.get('ip')
            account_switch_key = arguments.get('account_switch_key')
            data = edge_client.verify_edge_ip(ip, account_switch_key)
            return [TextContent(
                type="text",
                text=f"IP Verification Result:\n\n{json.dumps(data, indent=2)}"
            )]
        
        elif name == "locate_ip":
            ip = arguments.get('ip')
            account_switch_key = arguments.get('account_switch_key')
            data = edge_client.locate_ip(ip, account_switch_key)
            return [TextContent(
                type="text",
                text=f"IP Location:\n\n{json.dumps(data, indent=2)}"
            )]
        
        elif name == "verify_locate_ip":
            ip = arguments.get('ip')
            account_switch_key = arguments.get('account_switch_key')
            data = edge_client.verify_locate_ip(ip, account_switch_key)
            return [TextContent(
                type="text",
                text=f"IP Verification and Location:\n\n{json.dumps(data, indent=2)}"
            )]
        
        elif name == "list_edge_locations":
            data = edge_client.get_edge_locations()
            return [TextContent(
                type="text",
                text=f"Edge Server Locations:\n\n{json.dumps(data, indent=2)}"
            )]
        
        elif name == "list_gtm_properties":
            data = edge_client.get_gtm_properties()
            return [TextContent(
                type="text",
                text=f"GTM Properties:\n\n{json.dumps(data, indent=2)}"
            )]
        
        elif name == "get_gtm_property_ips":
            property_name = arguments.get('property')
            domain = arguments.get('domain')
            data = edge_client.get_gtm_property_ips(property_name, domain)
            return [TextContent(
                type="text",
                text=f"GTM Property IPs for {property_name}.{domain}:\n\n{json.dumps(data, indent=2)}"
            )]
        
        elif name == "list_ipa_hostnames":
            data = edge_client.get_ipa_hostnames()
            return [TextContent(
                type="text",
                text=f"IPA Hostnames:\n\n{json.dumps(data, indent=2)}"
            )]
        
        elif name == "translate_error":
            error_string = arguments.get('error_string')
            account_switch_key = arguments.get('account_switch_key')
            data = edge_client.translate_error(error_string, account_switch_key)
            return [TextContent(
                type="text",
                text=f"Error Translation:\n\n{json.dumps(data, indent=2)}"
            )]
        
        elif name == "get_error_translator_status":
            request_id = arguments.get('request_id')
            data = edge_client.get_error_translator_status(request_id)
            return [TextContent(
                type="text",
                text=f"Error Translation Status:\n\n{json.dumps(data, indent=2)}"
            )]
        
        elif name == "translate_url":
            url = arguments.get('url')
            data = edge_client.translate_url(url)
            return [TextContent(
                type="text",
                text=f"URL Translation:\n\n{json.dumps(data, indent=2)}"
            )]
        
        elif name == "launch_metadata_tracer":
            url = arguments.get('url')
            request_headers = arguments.get('request_headers')
            account_switch_key = arguments.get('account_switch_key')
            data = edge_client.launch_metadata_tracer(url, request_headers, account_switch_key)
            return [TextContent(
                type="text",
                text=f"Metadata Tracer Launched:\n\n{json.dumps(data, indent=2)}"
            )]
        
        elif name == "get_metadata_tracer_status":
            request_id = arguments.get('request_id')
            account_switch_key = arguments.get('account_switch_key')
            data = edge_client.get_metadata_tracer_status(request_id, account_switch_key)
            return [TextContent(
                type="text",
                text=f"Metadata Tracer Status:\n\n{json.dumps(data, indent=2)}"
            )]
        
        elif name == "get_error_statistics":
            url = arguments.get('url')
            cp_code = arguments.get('cp_code')
            data = edge_client.get_error_statistics(url, cp_code)
            return [TextContent(
                type="text",
                text=f"Error Statistics:\n\n{json.dumps(data, indent=2)}"
            )]
        
        elif name == "execute_curl":
            url = arguments.get('url')
            request_headers = arguments.get('request_headers')
            data = edge_client.execute_curl(url, request_headers)
            return [TextContent(
                type="text",
                text=f"cURL Result:\n\n{json.dumps(data, indent=2)}"
            )]
        
        elif name == "execute_dig":
            hostname = arguments.get('hostname')
            query_type = arguments.get('query_type', 'A')
            is_gtm_hostname = arguments.get('is_gtm_hostname', False)
            edge_location_id = arguments.get('edge_location_id')
            edge_ip = arguments.get('edge_ip')
            account_switch_key = arguments.get('account_switch_key')
            data = edge_client.execute_dig(hostname, query_type, is_gtm_hostname, edge_location_id, edge_ip, account_switch_key)
            return [TextContent(
                type="text",
                text=f"Dig Result:\n\n{json.dumps(data, indent=2)}"
            )]
        
        elif name == "execute_mtr":
            destination = arguments.get('destination')
            source = arguments.get('source')
            data = edge_client.execute_mtr(destination, source)
            return [TextContent(
                type="text",
                text=f"MTR Result:\n\n{json.dumps(data, indent=2)}"
            )]
        
        elif name == "launch_grep":
            hostname = arguments.get('hostname')
            log_type = arguments.get('log_type', 'r')
            data = edge_client.launch_grep(hostname, log_type)
            return [TextContent(
                type="text",
                text=f"GREP Request Launched:\n\n{json.dumps(data, indent=2)}"
            )]
        
        elif name == "get_grep_status":
            request_id = arguments.get('request_id')
            data = edge_client.get_grep_status(request_id)
            return [TextContent(
                type="text",
                text=f"GREP Status:\n\n{json.dumps(data, indent=2)}"
            )]
        
        elif name == "launch_url_health_check":
            url = arguments.get('url')
            request_headers = arguments.get('request_headers')
            edge_location_id = arguments.get('edge_location_id')
            ip_version = arguments.get('ip_version')
            packet_type = arguments.get('packet_type')
            port = arguments.get('port')
            query_type = arguments.get('query_type')
            run_from_site_shield = arguments.get('run_from_site_shield')
            sensitive_request_header_keys = arguments.get('sensitive_request_header_keys')
            spoof_edge_ip = arguments.get('spoof_edge_ip')
            views_allowed = arguments.get('views_allowed')
            account_switch_key = arguments.get('account_switch_key')
            data = edge_client.launch_url_health_check(url, request_headers, edge_location_id, ip_version, packet_type, port, query_type, run_from_site_shield, sensitive_request_header_keys, spoof_edge_ip, views_allowed, account_switch_key)
            return [TextContent(
                type="text",
                text=f"URL Health Check Launched:\n\n{json.dumps(data, indent=2)}"
            )]
        
        elif name == "get_url_health_check_status":
            request_id = arguments.get('request_id')
            account_switch_key = arguments.get('account_switch_key')
            data = edge_client.get_url_health_check_status(request_id, account_switch_key)
            return [TextContent(
                type="text",
                text=f"URL Health Check Status:\n\n{json.dumps(data, indent=2)}"
            )]
        
        elif name == "launch_connectivity_problems":
            url = arguments.get('url')
            client_location = arguments.get('client_location')
            data = edge_client.launch_connectivity_problems(url, client_location)
            return [TextContent(
                type="text",
                text=f"Connectivity Problems Check Launched:\n\n{json.dumps(data, indent=2)}"
            )]
        
        elif name == "get_connectivity_problems_status":
            request_id = arguments.get('request_id')
            data = edge_client.get_connectivity_problems_status(request_id)
            return [TextContent(
                type="text",
                text=f"Connectivity Problems Status:\n\n{json.dumps(data, indent=2)}"
            )]
        
        elif name == "launch_content_problems":
            url = arguments.get('url')
            request_headers = arguments.get('request_headers')
            data = edge_client.launch_content_problems(url, request_headers)
            return [TextContent(
                type="text",
                text=f"Content Problems Check Launched:\n\n{json.dumps(data, indent=2)}"
            )]
        
        elif name == "get_content_problems_status":
            request_id = arguments.get('request_id')
            data = edge_client.get_content_problems_status(request_id)
            return [TextContent(
                type="text",
                text=f"Content Problems Status:\n\n{json.dumps(data, indent=2)}"
            )]
        
        elif name == "generate_diagnostic_link":
            url = arguments.get('url')
            note = arguments.get('note')
            account_switch_key = arguments.get('account_switch_key')
            data = edge_client.generate_diagnostic_link(url, note, account_switch_key)
            return [TextContent(
                type="text",
                text=f"Diagnostic Link Generated:\n\n{json.dumps(data, indent=2)}"
            )]
        
        elif name == "get_diagnostic_data":
            group_id = arguments.get('group_id')
            account_switch_key = arguments.get('account_switch_key')
            data = edge_client.get_diagnostic_data(group_id, account_switch_key)
            return [TextContent(
                type="text",
                text=f"Diagnostic Data:\n\n{json.dumps(data, indent=2)}"
            )]
        
        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
    
    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}")
        return [TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]

async def main():
    """Main entry point for the server"""
    # Run the server using stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="edge-diagnostics-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
