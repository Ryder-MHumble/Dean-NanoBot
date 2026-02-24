#!/bin/bash
# Nanobot快速启动脚本
# 功能：启动nanobot并实时显示日志，Ctrl+C时优雅关闭

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 日志文件
LOG_FILE="/tmp/nanobot_$(date +%Y%m%d_%H%M%S).log"
NANOBOT_PID=""

# 清理函数
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 收到终止信号，正在关闭nanobot...${NC}"

    if [ ! -z "$NANOBOT_PID" ] && kill -0 $NANOBOT_PID 2>/dev/null; then
        echo -e "${CYAN}   终止进程 $NANOBOT_PID${NC}"
        kill $NANOBOT_PID 2>/dev/null || true

        # 等待进程结束，最多等待5秒
        for i in {1..5}; do
            if ! kill -0 $NANOBOT_PID 2>/dev/null; then
                break
            fi
            sleep 1
            echo -e "${CYAN}   等待进程结束... ($i/5)${NC}"
        done

        # 如果还没结束，强制终止
        if kill -0 $NANOBOT_PID 2>/dev/null; then
            echo -e "${RED}   强制终止进程${NC}"
            kill -9 $NANOBOT_PID 2>/dev/null || true
        fi
    fi

    # 检查是否还有残留进程
    REMAINING=$(ps aux | grep nanobot | grep -v grep | grep -v $$ || true)
    if [ ! -z "$REMAINING" ]; then
        echo -e "${YELLOW}   清理残留进程...${NC}"
        pkill -f nanobot || true
    fi

    echo -e "${GREEN}✅ Nanobot已安全关闭${NC}"
    echo -e "${BLUE}📋 日志已保存到: $LOG_FILE${NC}"
    exit 0
}

# 捕获终止信号
trap cleanup SIGINT SIGTERM

# 打印启动信息
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🤖 Nanobot 快速启动脚本${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${CYAN}📝 日志文件: $LOG_FILE${NC}"
echo -e "${YELLOW}⚠️  按 Ctrl+C 可安全退出${NC}"
echo ""

# 检查nanobot是否已经在运行
EXISTING=$(ps aux | grep nanobot | grep gateway | grep -v grep || true)
if [ ! -z "$EXISTING" ]; then
    echo -e "${RED}❌ 错误: nanobot已经在运行${NC}"
    echo ""
    echo "$EXISTING"
    echo ""
    echo -e "${YELLOW}请先终止现有进程：${NC}"
    echo "  pkill -f nanobot"
    exit 1
fi

# 启动nanobot
echo -e "${GREEN}🚀 正在启动nanobot gateway...${NC}"
echo ""

# 启动nanobot并实时显示日志
nanobot gateway 2>&1 | tee "$LOG_FILE" &
NANOBOT_PID=$!

# 等待一下确保进程启动
sleep 2

# 检查进程是否成功启动
if ! kill -0 $NANOBOT_PID 2>/dev/null; then
    echo -e "${RED}❌ Nanobot启动失败${NC}"
    echo -e "${BLUE}请查看日志: $LOG_FILE${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Nanobot已启动 (PID: $NANOBOT_PID)${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 等待进程结束
wait $NANOBOT_PID
