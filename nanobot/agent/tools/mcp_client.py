"""MCP (Model Context Protocol) client integration for nanobot."""

import os
from contextlib import AsyncExitStack
from typing import Any

from loguru import logger

from nanobot.agent.tools.base import Tool


class MCPToolWrapper(Tool):
    """Wraps an MCP tool as a nanobot Tool."""

    def __init__(self, tool_def: Any, client: "MCPClient") -> None:
        self._tool_name = tool_def.name
        self._tool_description = tool_def.description or ""
        # inputSchema is already a JSON Schema dict
        schema = tool_def.inputSchema
        if isinstance(schema, dict):
            self._tool_parameters = schema
        else:
            self._tool_parameters = {"type": "object", "properties": {}}
        self._client = client

    @property
    def name(self) -> str:
        return self._tool_name

    @property
    def description(self) -> str:
        return self._tool_description

    @property
    def parameters(self) -> dict[str, Any]:
        return self._tool_parameters

    async def execute(self, **kwargs: Any) -> str:
        return await self._client.call_tool(self._tool_name, kwargs)


class MCPClient:
    """Manages a connection to a single MCP server via stdio transport."""

    def __init__(self, config: Any) -> None:
        """
        Args:
            config: MCPServerConfig with command, args, env fields.
        """
        self._config = config
        self._session: Any = None
        self._exit_stack: AsyncExitStack | None = None

    async def start(self) -> None:
        """Start the MCP server subprocess and establish a session."""
        from mcp import ClientSession
        from mcp.client.stdio import StdioServerParameters, stdio_client
        import asyncio

        env = {**os.environ, **self._config.env} if self._config.env else None

        params = StdioServerParameters(
            command=self._config.command,
            args=self._config.args,
            env=env,
        )

        logger.debug(f"MCP: starting '{self._config.command} {' '.join(self._config.args)}'")
        
        try:
            self._exit_stack = AsyncExitStack()
            logger.debug(f"MCP: opening stdio_client...")
            read, write = await asyncio.wait_for(
                self._exit_stack.enter_async_context(stdio_client(params)),
                timeout=10.0
            )
            logger.debug(f"MCP: stdio_client opened, creating session...")
            session = await self._exit_stack.enter_async_context(ClientSession(read, write))
            logger.debug(f"MCP: initializing session...")
            await session.initialize()
            self._session = session
            logger.debug(f"MCP client connected: {self._config.command} {' '.join(self._config.args)}")
        except asyncio.TimeoutError:
            logger.error(f"MCP: timeout connecting to '{self._config.command}'")
            raise
        except Exception as e:
            logger.error(f"MCP: error starting '{self._config.command}': {type(e).__name__}: {e}")
            if self._exit_stack:
                try:
                    await self._exit_stack.aclose()
                except Exception as cleanup_err:
                    logger.debug(f"MCP: cleanup error: {cleanup_err}")
                self._exit_stack = None
            raise

    async def list_tools(self) -> list[Any]:
        """Return the list of tools exposed by this MCP server."""
        result = await self._session.list_tools()
        return result.tools

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        """Call a tool on the MCP server and return the result as a string."""
        result = await self._session.call_tool(name, arguments)

        if result.isError:
            # Collect error text from content blocks
            error_parts = [c.text for c in result.content if hasattr(c, "text")]
            return "Error: " + (" ".join(error_parts) if error_parts else "unknown error")

        parts = [c.text for c in result.content if hasattr(c, "text")]
        return "\n".join(parts) if parts else "(no output)"

    async def stop(self) -> None:
        """Shut down the MCP session and subprocess."""
        if self._exit_stack:
            await self._exit_stack.aclose()
            self._exit_stack = None
            self._session = None
            logger.debug(f"MCP client stopped: {self._config.command}")
