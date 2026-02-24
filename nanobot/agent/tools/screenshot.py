"""Screenshot tool for capturing screen images."""

import asyncio
import platform
from pathlib import Path
from datetime import datetime
from typing import Any

from nanobot.agent.tools.base import Tool


class ScreenshotTool(Tool):
    """Tool to capture screenshots of the screen."""

    def __init__(self, workspace: Path):
        """Initialize the screenshot tool.

        Args:
            workspace: The workspace directory where screenshots will be saved
        """
        self.workspace = workspace
        self.screenshots_dir = workspace / "screenshots"
        self.screenshots_dir.mkdir(exist_ok=True, parents=True)

    @property
    def name(self) -> str:
        return "screenshot"

    @property
    def description(self) -> str:
        return "Take a screenshot of the screen and save it to a file. Returns the file path."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "output_path": {
                    "type": "string",
                    "description": "Optional output file path. If not specified, saves to workspace/screenshots/ with timestamp"
                },
                "mode": {
                    "type": "string",
                    "enum": ["fullscreen", "window", "selection"],
                    "description": "Screenshot mode: fullscreen (entire screen), window (click a window), or selection (select area). Default: fullscreen"
                }
            }
        }

    async def execute(
        self,
        output_path: str | None = None,
        mode: str = "fullscreen",
        **kwargs: Any
    ) -> str:
        """Execute the screenshot command.

        Args:
            output_path: Optional custom output path
            mode: Screenshot mode (fullscreen, window, selection)

        Returns:
            Success message with file path or error message
        """
        # 1. Check platform support
        if platform.system() != "Darwin":
            return "Error: Screenshot tool currently only supports macOS. For other platforms, use exec tool with platform-specific commands."

        # 2. Determine output path
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(self.screenshots_dir / f"screenshot_{timestamp}.png")
        else:
            # Expand user paths like ~/Desktop/screenshot.png
            output_path = str(Path(output_path).expanduser().resolve())

        # 3. Build command based on mode
        if mode == "fullscreen":
            # -x: disable sound, capture entire screen
            cmd = f"screencapture -x '{output_path}'"
        elif mode == "window":
            # -w: capture a window (user clicks on window)
            cmd = f"screencapture -w '{output_path}'"
        elif mode == "selection":
            # -i: interactive selection mode
            cmd = f"screencapture -i '{output_path}'"
        else:
            return f"Error: Unknown screenshot mode '{mode}'. Use 'fullscreen', 'window', or 'selection'."

        # 4. Execute command
        try:
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            # 5. Check if file was created
            if Path(output_path).exists():
                file_size = Path(output_path).stat().st_size
                return f"Screenshot saved to: {output_path} (size: {file_size:,} bytes)"
            else:
                # Command executed but file not created (e.g., user cancelled selection)
                error_msg = stderr.decode() if stderr else "Unknown error"
                return f"Screenshot not created. The command may have been cancelled or failed. Error: {error_msg}"

        except Exception as e:
            return f"Error taking screenshot: {str(e)}"
