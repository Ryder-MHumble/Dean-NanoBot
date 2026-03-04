"""
Realm 项目开发 Skill

这个 Skill 用于与 Realm 任务编排系统交互，处理开发类需求。
支持：
- 项目分析
- 代码优化
- 文档生成
- 接口调用
- 新项目创建
"""

import httpx
import json
from typing import Optional, Dict, Any
import re

REALM_API = "http://localhost:4003"
REALM_DISPATCH_URL = f"{REALM_API}/dispatch"
REALM_SESSIONS_URL = f"{REALM_API}/sessions"

class RealmSkill:
    """Realm 项目开发技能"""

    def __init__(self):
        self.client = httpx.Client(timeout=30.0)
        self.available_projects = self._load_projects()

    def _load_projects(self) -> Dict[str, str]:
        """加载可用的项目列表"""
        try:
            response = self.client.get(REALM_SESSIONS_URL)
            if response.status_code == 200:
                data = response.json()
                projects = {}
                for session in data.get("sessions", []):
                    projects[session["name"].lower()] = session["id"]
                return projects
        except Exception as e:
            print(f"加载项目列表失败: {e}")
        return {}

    def parse_request(self, message: str) -> Dict[str, Any]:
        """解析用户请求，提取项目名称和任务类型"""

        # 项目名称映射
        project_aliases = {
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

        # 任务类型识别
        task_types = {
            "分析": "analyze",
            "优化": "optimize",
            "生成": "generate",
            "调用": "invoke",
            "创建": "create",
            "修复": "fix",
            "改进": "improve",
        }

        result = {
            "project": None,
            "project_id": None,
            "task_type": "analyze",  # 默认
            "description": message,
            "raw_message": message,
        }

        # 识别项目
        message_lower = message.lower()
        for alias, project_name in project_aliases.items():
            if alias in message_lower:
                result["project"] = project_name
                # 查找项目 ID
                for proj_name, proj_id in self.available_projects.items():
                    if project_name.lower() in proj_name.lower():
                        result["project_id"] = proj_id
                break

        # 识别任务类型
        for keyword, task_type in task_types.items():
            if keyword in message:
                result["task_type"] = task_type
                break

        return result

    def dispatch_task(self, project_id: Optional[str], message: str) -> Dict[str, Any]:
        """向 Realm 分发任务"""
        try:
            payload = {
                "message": message,
                "callbackUrl": "http://localhost:18790/callback",
            }

            if project_id:
                payload["sessionId"] = project_id

            response = self.client.post(REALM_DISPATCH_URL, json=payload)

            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    return {
                        "success": True,
                        "task_group_id": data.get("taskGroupId"),
                        "dispatched": data.get("dispatched", []),
                        "message": f"✅ 任务已分发 (Task Group ID: {data.get('taskGroupId')})",
                    }

            return {
                "success": False,
                "message": f"❌ 任务分发失败: HTTP {response.status_code}",
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"❌ 任务分发异常: {str(e)}",
            }

    def list_projects(self) -> str:
        """列出所有可用项目"""
        if not self.available_projects:
            return "❌ 无法获取项目列表"

        projects_info = []
        for project_name, project_id in self.available_projects.items():
            projects_info.append(f"• {project_name} ({project_id[:8]}...)")

        return f"""✅ 可用项目列表：

{chr(10).join(projects_info)}

💡 你可以发送以下指令：
- 分析 [项目名] 的 [功能/结构]
- 优化 [项目名] 的 [模块/功能]
- 为 [项目名] 生成 [文档类型]
- 调用 [项目名] 的接口
- 创建 [项目名] session"""

    def execute(self, message: str) -> str:
        """执行 Skill 的主逻辑"""

        # 特殊指令：列出项目
        if "列出" in message and "项目" in message:
            return self.list_projects()

        # 解析请求
        parsed = self.parse_request(message)

        # 如果没有识别到项目，提示用户
        if not parsed["project"]:
            return f"""❓ 我没有识别到具体的项目。

📋 可用项目：
{self.list_projects()}

💡 请明确指定项目名称，例如：
- "分析 Athena 项目的结构"
- "优化 Personal_Resume-main 的 UI"
- "为 guameow_flutter 生成文档"
"""

        # 构建任务描述
        task_description = f"{parsed['description']}"

        # 分发任务
        result = self.dispatch_task(parsed["project_id"], task_description)

        if result["success"]:
            return f"""✅ 任务已成功分发！

📋 项目: {parsed['project']}
🎯 任务类型: {parsed['task_type']}
📝 描述: {parsed['description']}
🔗 Task Group ID: {result['task_group_id']}

⏳ 正在处理中...
💬 结果将通过飞书回复给你"""
        else:
            return result["message"]


# 导出 Skill 实例
realm_skill = RealmSkill()


def handle_development_request(message: str) -> str:
    """处理开发类请求的主入口"""
    return realm_skill.execute(message)


# 关键词识别
DEVELOPMENT_KEYWORDS = [
    "分析", "优化", "生成", "调用", "创建", "修复", "改进",
    "项目", "代码", "功能", "模块", "文档", "接口", "session",
    "athena", "简历", "resume", "guameow", "flutter", "prism", "pdf", "realm", "爬虫", "crawler",
]


def should_use_skill(message: str) -> bool:
    """判断是否应该使用这个 Skill"""
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in DEVELOPMENT_KEYWORDS)
