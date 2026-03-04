#!/usr/bin/env python3
"""
Callback Server for Realm Integration

This server receives callbacks from Realm when tasks complete,
and forwards the results back to the user via the message bus.
"""

import asyncio
import json
from typing import Any
from aiohttp import web
from loguru import logger

from nanobot.bus.queue import MessageBus
from nanobot.bus.events import OutboundMessage


class CallbackServer:
    """HTTP server to receive callbacks from Realm."""

    def __init__(self, bus: MessageBus, host: str = "0.0.0.0", port: int = 18790):
        self.bus = bus
        self.host = host
        self.port = port
        self.app = web.Application()
        self.runner: web.AppRunner | None = None
        self._setup_routes()

        # Store task metadata (taskGroupId -> {channel, chat_id})
        self.task_metadata: dict[str, dict[str, str]] = {}

    def _setup_routes(self):
        """Setup HTTP routes."""
        self.app.router.add_post("/callback", self.handle_callback)
        self.app.router.add_get("/health", self.handle_health)

    async def handle_health(self, request: web.Request) -> web.Response:
        """Health check endpoint."""
        return web.json_response({"status": "ok"})

    async def handle_callback(self, request: web.Request) -> web.Response:
        """Handle callback from Realm."""
        try:
            data = await request.json()
            logger.info(f"[Callback] Received from Realm: {data.get('taskGroupId')}")

            task_group_id = data.get("taskGroupId")
            original_message = data.get("originalMessage", "")
            results = data.get("results", [])
            duration_ms = data.get("durationMs", 0)

            # Get task metadata
            metadata = self.task_metadata.get(task_group_id, {})
            channel = metadata.get("channel", "feishu")
            chat_id = metadata.get("chat_id", "")

            if not chat_id:
                logger.warning(f"[Callback] No chat_id found for task {task_group_id}")
                return web.json_response({"ok": False, "error": "No chat_id"}, status=400)

            # Format response
            response_content = self._format_response(original_message, results, duration_ms)

            # Send to user via message bus
            await self.bus.publish_outbound(OutboundMessage(
                channel=channel,
                chat_id=chat_id,
                content=response_content,
            ))

            # Clean up metadata
            self.task_metadata.pop(task_group_id, None)

            logger.info(f"[Callback] Forwarded result to {channel}:{chat_id}")
            return web.json_response({"ok": True})

        except Exception as e:
            logger.error(f"[Callback] Error handling callback: {e}")
            return web.json_response({"ok": False, "error": str(e)}, status=500)

    def _format_response(self, original_message: str, results: list[dict], duration_ms: int) -> str:
        """Format the callback response for display."""
        lines = [
            "✅ **Realm 任务完成**",
            "",
            f"📝 **原始请求**: {original_message}",
            f"⏱️ **耗时**: {duration_ms / 1000:.1f}s",
            "",
        ]

        for i, result in enumerate(results, 1):
            session_name = result.get("sessionName", "Unknown")
            response = result.get("response", "")
            status = result.get("status", "unknown")

            lines.append(f"### Session {i}: {session_name}")
            lines.append(f"**状态**: {status}")
            lines.append("")

            # Truncate long responses
            if len(response) > 1000:
                lines.append(f"```\n{response[:1000]}\n... (truncated)\n```")
            else:
                lines.append(f"```\n{response}\n```")
            lines.append("")

        return "\n".join(lines)

    def register_task(self, task_group_id: str, channel: str, chat_id: str):
        """Register a task with its metadata for callback routing."""
        self.task_metadata[task_group_id] = {
            "channel": channel,
            "chat_id": chat_id,
        }
        logger.info(f"[Callback] Registered task {task_group_id} for {channel}:{chat_id}")

    async def start(self):
        """Start the callback server."""
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, self.host, self.port)
        await site.start()
        logger.info(f"Callback server started on http://{self.host}:{self.port}")

    async def stop(self):
        """Stop the callback server."""
        if self.runner:
            await self.runner.cleanup()
            logger.info("Callback server stopped")
