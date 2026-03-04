"""
Realm Skill Integration Module

This module integrates the Realm skill into NanoBot's agent loop.
It provides a hook that detects Realm-related requests and routes them appropriately.
"""

import json
from typing import Optional, Dict, Any, TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from nanobot.callback_server import CallbackServer

# Import the realm skill
from nanobot.skills.Realm.realm_skill import RealmSkill, should_use_skill


class RealmSkillIntegration:
    """Integration layer for Realm skill in NanoBot."""

    def __init__(self):
        self.skill = RealmSkill()
        self.callback_server: Optional["CallbackServer"] = None
        self.current_channel: Optional[str] = None
        self.current_chat_id: Optional[str] = None

    def set_callback_server(self, server: "CallbackServer"):
        """Set the callback server instance."""
        self.callback_server = server

    def set_context(self, channel: str, chat_id: str):
        """Set the current context for routing callbacks."""
        self.current_channel = channel
        self.current_chat_id = chat_id

    def should_handle(self, message: str) -> bool:
        """Check if this message should be handled by Realm skill."""
        return should_use_skill(message)

    def handle(self, message: str) -> Optional[str]:
        """Handle a message with Realm skill."""
        try:
            # Execute the skill
            result = self.skill.execute(message)

            # If this was a dispatch request, extract task_group_id and register it
            if "Task Group ID:" in result and self.callback_server:
                # Extract task_group_id from response
                import re
                match = re.search(r"Task Group ID: ([a-f0-9-]+)", result)
                if match and self.current_channel and self.current_chat_id:
                    task_group_id = match.group(1)
                    self.callback_server.register_task(
                        task_group_id,
                        self.current_channel,
                        self.current_chat_id
                    )

            return result
        except Exception as e:
            return f"❌ Realm skill error: {str(e)}"


# Global instance
_realm_integration = RealmSkillIntegration()


def set_callback_server(server: "CallbackServer"):
    """Set the callback server for the integration."""
    _realm_integration.set_callback_server(server)


def set_context(channel: str, chat_id: str):
    """Set the current context for routing callbacks."""
    _realm_integration.set_context(channel, chat_id)


def is_realm_request(message: str) -> bool:
    """Check if a message is a Realm development request."""
    return _realm_integration.should_handle(message)


def handle_realm_request(message: str) -> str:
    """Handle a Realm development request."""
    result = _realm_integration.handle(message)
    return result or "Unable to process Realm request"
