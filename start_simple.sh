#!/bin/bash
# Nanobot简化启动脚本 - 最简单的版本

# 捕获Ctrl+C，优雅关闭
trap 'echo -e "\n🛑 正在关闭nanobot..."; pkill -f "nanobot gateway"; exit 0' SIGINT SIGTERM

echo "🚀 启动nanobot..."
echo "⚠️  按 Ctrl+C 退出"
echo ""

# 直接启动nanobot，实时显示所有输出
nanobot gateway
