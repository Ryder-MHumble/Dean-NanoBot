"""Realm tool for dispatching tasks to Realm project sessions."""

import httpx
from typing import Any
from loguru import logger

from nanobot.agent.tools.base import Tool


class RealmTool(Tool):
    """
    Tool for dispatching development tasks to Realm project sessions.

    Realm manages multiple Claude Code sessions for different projects.
    This tool allows the agent to dispatch tasks to specific projects.
    """
    
    name = "realm"
    description = """**PRIMARY TOOL for Realm project management - ALWAYS use this instead of curl/exec.**

This tool manages development tasks across multiple Claude Code sessions.

CRITICAL: You MUST use this tool (NOT curl/exec) when:
- User mentions "Realm" keyword
- User mentions project names: Athena, Personal_Resume-main, guameow_flutter, prism-resume-forge, information_crawler, 简历, 爬虫
- User asks to: analyze, optimize, generate docs, improve UI/UX, list projects, CREATE NEW PROJECT
- Chinese: 分析, 优化, 生成文档, 列出项目, 帮我执行, 创建项目

Why use this tool instead of curl:
- Automatic callback routing (results sent back to user)
- Proper error handling
- Task tracking and status updates

Examples that REQUIRE this tool:
✓ "用Realm帮我执行..." → realm(action="dispatch", message="...")
✓ "分析 Athena 项目" → realm(action="dispatch", message="分析 Athena 项目")
✓ "优化 guameow_flutter 的 UI" → realm(action="dispatch", message="优化 guameow_flutter 的 UI")
✓ "列出所有项目" → realm(action="list")
✓ "在Realm中创建一个新项目 MyApp" → realm(action="create", project_name="MyApp", project_path="/path/to/MyApp")
✓ "把本地的 xxx 项目添加到 Realm" → realm(action="create", project_name="xxx", project_path="/path/to/xxx")
✗ DO NOT use exec/curl for http://localhost:4003 - use this tool instead!
"""
    
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["dispatch", "list", "create"],
                "description": "Action to perform: 'dispatch' to send a task, 'list' to show available projects, 'create' to create a new project session"
            },
            "message": {
                "type": "string",
                "description": "The task message to dispatch (required for 'dispatch' action)"
            },
            "project_id": {
                "type": "string",
                "description": "Optional project/session ID to target a specific project"
            },
            "project_name": {
                "type": "string",
                "description": "Name for the new project (required for 'create' action)"
            },
            "project_path": {
                "type": "string",
                "description": "Absolute path to the project directory (required for 'create' action)"
            },
            "description": {
                "type": "string",
                "description": "Optional description for the new project (for 'create' action)"
            }
        },
        "required": ["action"]
    }
    
    def __init__(self, callback_server: Any = None):
        self.realm_api = "http://localhost:4003"
        self.callback_url = "http://localhost:18790/callback"
        self.callback_server = callback_server
        self.current_channel: str | None = None
        self.current_chat_id: str | None = None
        
        # Project name mapping for user-friendly names
        self.project_aliases = {
            "athena": "Athena",
            "简历": "Personal_Resume-main",
            "resume": "Personal_Resume-main",
            "personal": "Personal_Resume-main",
            "guameow": "guameow_flutter",
            "flutter": "guameow_flutter",
            "prism": "prism-resume-forge",
            "pdf": "prism-resume-forge",
            "realm": "Realm",
            "爬虫": "information_crawler",
            "crawler": "information_crawler",
        }
    
    def set_context(self, channel: str, chat_id: str):
        """Set the current context for callback routing."""
        self.current_channel = channel
        self.current_chat_id = chat_id
    
    async def execute(self, action: str, message: str = "", project_id: str = "",
                     project_name: str = "", project_path: str = "", description: str = "") -> str:
        """Execute the Realm tool."""
        try:
            if action == "list":
                return await self._list_projects()
            elif action == "dispatch":
                if not message:
                    return "❌ Error: 'message' parameter is required for dispatch action"
                return await self._dispatch_task(message, project_id)
            elif action == "create":
                if not project_name or not project_path:
                    return "❌ Error: 'project_name' and 'project_path' are required for create action"
                return await self._create_session(project_name, project_path, description)
            else:
                return f"❌ Unknown action: {action}"
        except Exception as e:
            logger.error(f"Realm tool error: {e}")
            return f"❌ Realm tool error: {str(e)}"
    
    async def _list_projects(self) -> str:
        """List all available Realm projects."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.realm_api}/sessions")
                
                if response.status_code != 200:
                    return f"❌ Failed to fetch projects: HTTP {response.status_code}"
                
                data = response.json()
                sessions = data.get("sessions", [])
                
                if not sessions:
                    return "❌ No projects found in Realm"
                
                lines = ["✅ 可用项目列表：\n"]
                for session in sessions:
                    name = session.get("name", "Unknown")
                    session_id = session.get("id", "")
                    lines.append(f"• {name} ({session_id[:8]}...)")
                
                lines.append("\n💡 你可以发送以下指令：")
                lines.append("- 分析 [项目名] 的 [功能/结构]")
                lines.append("- 优化 [项目名] 的 [模块/功能]")
                lines.append("- 为 [项目名] 生成 [文档类型]")
                
                return "\n".join(lines)
                
        except httpx.ConnectError:
            return f"❌ 无法连接到 Realm 服务器 ({self.realm_api})\n请确保 Realm 服务器正在运行：cd ~/Desktop/My\\ Projects/Realm && npm run server"
        except Exception as e:
            return f"❌ 获取项目列表失败: {str(e)}"
    
    async def _dispatch_task(self, message: str, project_id: str = "") -> str:
        """Dispatch a task to Realm."""
        try:
            # If no project_id provided, try to extract from message and find matching session
            if not project_id:
                project_id = await self._find_session_id(message)

            # Build request payload
            payload = {
                "message": message,
                "callbackUrl": self.callback_url,
            }

            if project_id:
                payload["sessionId"] = project_id
                logger.info(f"Dispatching to specific session: {project_id}")
            else:
                logger.info("Dispatching without sessionId, Realm will use LLM routing")

            # Send dispatch request
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.realm_api}/dispatch",
                    json=payload
                )

                if response.status_code != 200:
                    return f"❌ 任务分发失败: HTTP {response.status_code}"

                data = response.json()

                if not data.get("ok"):
                    error = data.get("error", "Unknown error")
                    return f"❌ 任务分发失败: {error}"

                task_group_id = data.get("taskGroupId", "")
                dispatched = data.get("dispatched", [])

                # Register task for callback routing
                if self.callback_server and task_group_id and self.current_channel and self.current_chat_id:
                    self.callback_server.register_task(
                        task_group_id,
                        self.current_channel,
                        self.current_chat_id
                    )

                # Build response
                lines = ["✅ 任务已成功分发！\n"]
                lines.append(f"🔗 Task Group ID: {task_group_id}")
                lines.append(f"📝 描述: {message}")

                if dispatched:
                    lines.append(f"\n📊 已分发到 {len(dispatched)} 个 session:")
                    for d in dispatched[:3]:  # Show first 3
                        session_name = d.get("sessionName", "Unknown")
                        lines.append(f"  • {session_name}")

                lines.append("\n⏳ 正在处理中...")
                lines.append("💬 结果将在任务完成后自动发送给你")

                return "\n".join(lines)

        except httpx.ConnectError:
            return f"❌ 无法连接到 Realm 服务器 ({self.realm_api})\n请确保 Realm 服务器正在运行"
        except Exception as e:
            logger.error(f"Dispatch task error: {e}")
            return f"❌ 任务分发异常: {str(e)}"

    async def _find_session_id(self, message: str) -> str:
        """Try to find a matching session ID from the message."""
        try:
            # Get all sessions
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.realm_api}/sessions")
                if response.status_code != 200:
                    return ""

                data = response.json()
                sessions = data.get("sessions", [])

                # Try to match project name in message
                message_lower = message.lower()

                # Check project aliases
                for alias, project_name in self.project_aliases.items():
                    if alias in message_lower:
                        # Find session with this project name
                        for session in sessions:
                            if project_name.lower() in session.get("name", "").lower():
                                logger.info(f"Matched '{alias}' to session: {session.get('name')}")
                                return session.get("id", "")

                # Try direct name matching
                for session in sessions:
                    session_name = session.get("name", "").lower()
                    if session_name and session_name in message_lower:
                        logger.info(f"Direct match found: {session.get('name')}")
                        return session.get("id", "")

                return ""
        except Exception as e:
            logger.warning(f"Failed to find session ID: {e}")
            return ""

    async def _create_session(self, project_name: str, project_path: str, description: str = "") -> str:
        """Create a new Realm session for a project."""
        try:
            # Build request payload
            payload = {
                "name": project_name,
                "cwd": project_path,
                "agentType": "claude_code",
                "mode": "auto-edit",
            }
            
            if description:
                payload["description"] = description
            
            # Send create session request
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.realm_api}/sessions",
                    json=payload
                )
                
                if response.status_code != 201:
                    return f"❌ 创建 session 失败: HTTP {response.status_code}"
                
                data = response.json()
                
                if not data.get("ok"):
                    error = data.get("error", "Unknown error")
                    return f"❌ 创建 session 失败: {error}"
                
                session = data.get("session", {})
                session_id = session.get("id", "")
                session_name = session.get("name", project_name)
                tmux_session = session.get("tmuxSession", "")
                
                # Build response
                lines = ["✅ 新项目 session 创建成功！\n"]
                lines.append(f"📋 项目名称: {session_name}")
                lines.append(f"🔗 Session ID: {session_id}")
                lines.append(f"📁 项目路径: {project_path}")
                lines.append(f"🖥️  Tmux Session: {tmux_session}")
                
                if description:
                    lines.append(f"📝 描述: {description}")
                
                lines.append("\n💡 现在你可以向这个项目分发任务了！")
                lines.append(f"例如：分析 {session_name} 项目的架构")
                
                return "\n".join(lines)
                
        except httpx.ConnectError:
            return f"❌ 无法连接到 Realm 服务器 ({self.realm_api})\n请确保 Realm 服务器正在运行"
        except Exception as e:
            logger.error(f"Create session error: {e}")
            return f"❌ 创建 session 异常: {str(e)}"
