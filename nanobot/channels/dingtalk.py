"""DingTalk/DingDing channel implementation using Stream Mode."""

import asyncio
import json
import tempfile
import time
from pathlib import Path
from typing import Any

from loguru import logger
import httpx

from nanobot.bus.events import OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.channels.base import BaseChannel
from nanobot.config.schema import DingTalkConfig

try:
    from dingtalk_stream import (
        DingTalkStreamClient,
        Credential,
        CallbackHandler,
        CallbackMessage,
        AckMessage,
    )
    from dingtalk_stream.chatbot import ChatbotMessage

    DINGTALK_AVAILABLE = True
except ImportError:
    DINGTALK_AVAILABLE = False
    # Fallback so class definitions don't crash at module level
    CallbackHandler = object  # type: ignore[assignment,misc]
    CallbackMessage = None  # type: ignore[assignment,misc]
    AckMessage = None  # type: ignore[assignment,misc]
    ChatbotMessage = None  # type: ignore[assignment,misc]


class NanobotDingTalkHandler(CallbackHandler):
    """
    Standard DingTalk Stream SDK Callback Handler.
    Parses incoming messages and forwards them to the Nanobot channel.
    """

    def __init__(self, channel: "DingTalkChannel"):
        super().__init__()
        self.channel = channel

    async def process(self, message: CallbackMessage):
        """Process incoming stream message."""
        try:
            # Parse using SDK's ChatbotMessage for robust handling
            chatbot_msg = ChatbotMessage.from_dict(message.data)

            sender_id = chatbot_msg.sender_staff_id or chatbot_msg.sender_id
            sender_name = chatbot_msg.sender_nick or "Unknown"

            msg_type = message.data.get("msgtype", "text")

            # Handle audio messages
            if msg_type == "audio":
                download_code = message.data.get("audio", {}).get("downloadCode", "")
                if download_code:
                    logger.info(f"Received DingTalk audio message from {sender_name} ({sender_id})")
                    task = asyncio.create_task(
                        self.channel._on_audio_message(download_code, sender_id, sender_name)
                    )
                    self.channel._background_tasks.add(task)
                    task.add_done_callback(self.channel._background_tasks.discard)
                else:
                    logger.warning("Received audio message with no downloadCode")
                return AckMessage.STATUS_OK, "OK"

            # Extract text content; fall back to raw dict if SDK object is empty
            content = ""
            if chatbot_msg.text:
                content = chatbot_msg.text.content.strip()
            if not content:
                content = message.data.get("text", {}).get("content", "").strip()

            if not content:
                logger.warning(
                    f"Received empty or unsupported message type: {chatbot_msg.message_type}"
                )
                return AckMessage.STATUS_OK, "OK"

            logger.info(f"Received DingTalk message from {sender_name} ({sender_id}): {content}")

            # Forward to Nanobot via _on_message (non-blocking).
            # Store reference to prevent GC before task completes.
            task = asyncio.create_task(
                self.channel._on_message(content, sender_id, sender_name)
            )
            self.channel._background_tasks.add(task)
            task.add_done_callback(self.channel._background_tasks.discard)

            return AckMessage.STATUS_OK, "OK"

        except Exception as e:
            logger.error(f"Error processing DingTalk message: {e}")
            # Return OK to avoid retry loop from DingTalk server
            return AckMessage.STATUS_OK, "Error"


class DingTalkChannel(BaseChannel):
    """
    DingTalk channel using Stream Mode.

    Uses WebSocket to receive events via `dingtalk-stream` SDK.
    Uses direct HTTP API to send messages (SDK is mainly for receiving).

    Note: Currently only supports private (1:1) chat. Group messages are
    received but replies are sent back as private messages to the sender.
    """

    name = "dingtalk"

    def __init__(self, config: DingTalkConfig, bus: MessageBus, groq_api_key: str = ""):
        super().__init__(config, bus, groq_api_key=groq_api_key)
        self.config: DingTalkConfig = config
        self._client: Any = None
        self._http: httpx.AsyncClient | None = None

        # Access Token management for sending messages
        self._access_token: str | None = None
        self._token_expiry: float = 0

        # Hold references to background tasks to prevent GC
        self._background_tasks: set[asyncio.Task] = set()

    async def start(self) -> None:
        """Start the DingTalk bot with Stream Mode."""
        try:
            if not DINGTALK_AVAILABLE:
                logger.error(
                    "DingTalk Stream SDK not installed. Run: pip install dingtalk-stream"
                )
                return

            if not self.config.client_id or not self.config.client_secret:
                logger.error("DingTalk client_id and client_secret not configured")
                return

            self._running = True
            self._http = httpx.AsyncClient()

            logger.info(
                f"Initializing DingTalk Stream Client with Client ID: {self.config.client_id}..."
            )
            credential = Credential(self.config.client_id, self.config.client_secret)
            self._client = DingTalkStreamClient(credential)

            # Register standard handler
            handler = NanobotDingTalkHandler(self)
            self._client.register_callback_handler(ChatbotMessage.TOPIC, handler)

            logger.info("DingTalk bot started with Stream Mode")

            # Reconnect loop: restart stream if SDK exits or crashes
            while self._running:
                try:
                    await self._client.start()
                except Exception as e:
                    logger.warning(f"DingTalk stream error: {e}")
                if self._running:
                    logger.info("Reconnecting DingTalk stream in 5 seconds...")
                    await asyncio.sleep(5)

        except Exception as e:
            logger.exception(f"Failed to start DingTalk channel: {e}")

    async def stop(self) -> None:
        """Stop the DingTalk bot."""
        self._running = False
        # Close the shared HTTP client
        if self._http:
            await self._http.aclose()
            self._http = None
        # Cancel outstanding background tasks
        for task in self._background_tasks:
            task.cancel()
        self._background_tasks.clear()

    async def _get_access_token(self) -> str | None:
        """Get or refresh Access Token."""
        if self._access_token and time.time() < self._token_expiry:
            return self._access_token

        url = "https://api.dingtalk.com/v1.0/oauth2/accessToken"
        data = {
            "appKey": self.config.client_id,
            "appSecret": self.config.client_secret,
        }

        if not self._http:
            logger.warning("DingTalk HTTP client not initialized, cannot refresh token")
            return None

        try:
            resp = await self._http.post(url, json=data)
            resp.raise_for_status()
            res_data = resp.json()
            self._access_token = res_data.get("accessToken")
            # Expire 60s early to be safe
            self._token_expiry = time.time() + int(res_data.get("expireIn", 7200)) - 60
            return self._access_token
        except Exception as e:
            logger.error(f"Failed to get DingTalk access token: {e}")
            return None

    async def send(self, msg: OutboundMessage) -> None:
        """Send a message through DingTalk."""
        token = await self._get_access_token()
        if not token:
            return

        # oToMessages/batchSend: sends to individual users (private chat)
        # https://open.dingtalk.com/document/orgapp/robot-batch-send-messages
        url = "https://api.dingtalk.com/v1.0/robot/oToMessages/batchSend"

        headers = {"x-acs-dingtalk-access-token": token}

        # Handle message content
        content = msg.content

        # If there are media files, append file path information to the message
        if msg.media and len(msg.media) > 0:
            content += "\n\n📎 **附件**:\n"
            for media_path in msg.media:
                # Display friendly filename
                from pathlib import Path
                filename = Path(media_path).name
                content += f"- {filename} (路径: {media_path})\n"

            content += "\n💡 图片已保存到本地，可以在上述路径查看。"

        data = {
            "robotCode": self.config.client_id,
            "userIds": [msg.chat_id],  # chat_id is the user's staffId
            "msgKey": "sampleMarkdown",
            "msgParam": json.dumps({
                "text": content,
                "title": "Nanobot Reply",
            }),
        }

        if not self._http:
            logger.warning("DingTalk HTTP client not initialized, cannot send")
            return

        try:
            resp = await self._http.post(url, json=data, headers=headers)
            if resp.status_code != 200:
                logger.error(f"DingTalk send failed: {resp.text}")
            else:
                logger.debug(f"DingTalk message sent to {msg.chat_id}")
        except Exception as e:
            logger.error(f"Error sending DingTalk message: {e}")

    async def _on_message(self, content: str, sender_id: str, sender_name: str) -> None:
        """Handle incoming message (called by NanobotDingTalkHandler).

        Delegates to BaseChannel._handle_message() which enforces allow_from
        permission checks before publishing to the bus.
        """
        try:
            logger.info(f"DingTalk inbound: {content} from {sender_name}")
            await self._handle_message(
                sender_id=sender_id,
                chat_id=sender_id,  # For private chat, chat_id == sender_id
                content=str(content),
                metadata={
                    "sender_name": sender_name,
                    "platform": "dingtalk",
                },
            )
        except Exception as e:
            logger.error(f"Error publishing DingTalk message: {e}")

    async def _on_audio_message(self, download_code: str, sender_id: str, sender_name: str) -> None:
        """Handle incoming audio message: download, transcribe, then forward as text."""
        try:
            # Step 1: Get download URL from DingTalk API
            token = await self._get_access_token()
            if not token:
                logger.error("Cannot process audio: failed to get access token")
                return

            download_url = await self._get_audio_download_url(token, download_code)
            if not download_url:
                logger.error("Cannot process audio: failed to get download URL")
                await self._on_message("[语音消息：无法下载]", sender_id, sender_name)
                return

            # Step 2: Download audio file to temp dir
            audio_path = await self._download_audio_file(download_url)
            if not audio_path:
                logger.error("Cannot process audio: download failed")
                await self._on_message("[语音消息：下载失败]", sender_id, sender_name)
                return

            # Step 3: Transcribe with Groq (shared base method handles format conversion)
            try:
                transcription = await self._transcribe_audio(audio_path)
            finally:
                # Clean up temp file
                try:
                    Path(audio_path).unlink(missing_ok=True)
                except Exception:
                    pass

            if transcription:
                logger.info(f"DingTalk audio transcribed from {sender_name}: {transcription[:80]}...")
                await self._on_message(transcription, sender_id, sender_name)
            else:
                logger.warning("Audio transcription returned empty result")
                await self._on_message("[语音消息：转录失败，请发送文字]", sender_id, sender_name)

        except Exception as e:
            logger.error(f"Error processing DingTalk audio message: {e}")

    async def _get_audio_download_url(self, token: str, download_code: str) -> str | None:
        """Call DingTalk API to get a temporary download URL for an audio file."""
        if not self._http:
            return None
        url = "https://api.dingtalk.com/v1.0/robot/messageFiles/download"
        headers = {"x-acs-dingtalk-access-token": token}
        body = {"downloadCode": download_code, "robotCode": self.config.client_id}
        try:
            resp = await self._http.post(url, json=body, headers=headers, timeout=15.0)
            resp.raise_for_status()
            return resp.json().get("downloadUrl")
        except Exception as e:
            logger.error(f"Failed to get DingTalk audio download URL: {e}")
            return None

    async def _download_audio_file(self, url: str) -> str | None:
        """Download audio from URL to a temporary file. Returns local path or None."""
        if not self._http:
            return None
        try:
            resp = await self._http.get(url, timeout=30.0, follow_redirects=True)
            resp.raise_for_status()
            # DingTalk voice messages are typically AMR; use .amr extension
            suffix = ".amr"
            content_type = resp.headers.get("content-type", "")
            if "mp4" in content_type or "m4a" in content_type:
                suffix = ".m4a"
            elif "ogg" in content_type:
                suffix = ".ogg"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
                f.write(resp.content)
                return f.name
        except Exception as e:
            logger.error(f"Failed to download DingTalk audio file: {e}")
            return None
