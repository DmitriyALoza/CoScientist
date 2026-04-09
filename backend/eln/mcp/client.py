"""
MCP (Model Context Protocol) client stub.

Connects to MCP tool servers, enforces an allowlist, and logs all tool calls.
Full implementation in Phase 6 — this provides the interface contract.
"""


from eln.audit.logger import AuditLogger


class MCPClient:
    """
    Client for connecting to MCP servers and calling tools.

    Tools are allowlisted per workspace policy. All calls are logged.
    """

    def __init__(
        self,
        allowlist: list[str] | None = None,
        audit_logger: AuditLogger | None = None,
    ):
        self.allowlist = set(allowlist) if allowlist else set()
        self.audit = audit_logger
        self._connected = False

    async def connect(self, server_url: str) -> None:
        """Connect to an MCP server."""
        # TODO: implement actual MCP connection using the `mcp` package
        self._connected = True

    async def call_tool(self, tool_name: str, args: dict) -> dict:
        """
        Call a tool on the connected MCP server.

        Raises ValueError if tool is not in the allowlist.
        """
        if self.allowlist and tool_name not in self.allowlist:
            raise ValueError(
                f"Tool '{tool_name}' not in allowlist. "
                f"Allowed: {sorted(self.allowlist)}"
            )

        if not self._connected:
            raise RuntimeError("Not connected to an MCP server. Call connect() first.")

        # TODO: actual MCP tool call
        result = {"status": "stub", "message": f"MCP tool '{tool_name}' not yet implemented."}

        if self.audit:
            self.audit.log_tool_call(
                tool_name=tool_name,
                args=args,
                result_summary=str(result),
            )

        return result

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected
