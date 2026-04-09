#!/bin/bash
# =============================================================================
# nanobot.sh - Nanobot 服务管理脚本
#
# 用法:
#   ./nanobot.sh start    [-p PORT] [-v]   后台启动
#   ./nanobot.sh stop                      停止服务
#   ./nanobot.sh restart  [-p PORT] [-v]   重启服务
#   ./nanobot.sh status                    查看运行状态
#   ./nanobot.sh logs     [-f] [-n LINES]  查看日志
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
APP_NAME="nanobot"
PID_FILE="/tmp/nanobot.pid"
LOG_DIR="$HOME/.nanobot/logs"
LOG_FILE="$LOG_DIR/gateway.log"

# 自动加载 .env 文件（从脚本所在目录查找）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"
VENV_NANOBOT="$SCRIPT_DIR/.venv/bin/nanobot"

# 启动命令优先使用仓库本地虚拟环境
if [ -x "$VENV_NANOBOT" ]; then
    NANOBOT_CMD="$VENV_NANOBOT"
else
    NANOBOT_CMD="nanobot"
fi
if [ -f "$ENV_FILE" ]; then
    set -o allexport
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +o allexport
fi

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------
info()  { echo -e "${GREEN}[✓]${NC} $*"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
error() { echo -e "${RED}[✗]${NC} $*"; }
bold()  { echo -e "${BOLD}$*${NC}"; }

# 获取正在运行的 nanobot gateway 进程 PID（不依赖 pid 文件）
get_running_pid() {
    # 查找 nanobot gateway 进程，排除 grep 自身和本脚本
    local pid
    pid=$(ps ax -o pid,command | grep '[n]anobot gateway' | grep -v "$0" | awk '{print $1}' | head -1)
    echo "$pid"
}

# 判断进程是否存活
is_running() {
    local pid
    pid=$(get_running_pid)
    [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null
}

# ---------------------------------------------------------------------------
# start
# ---------------------------------------------------------------------------
do_start() {
    local port=18790
    local verbose=""

    # 解析参数
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -p|--port)  port="$2"; shift 2 ;;
            -v|--verbose) verbose="--verbose"; shift ;;
            *) error "未知参数: $1"; exit 1 ;;
        esac
    done

    if is_running; then
        local pid
        pid=$(get_running_pid)
        warn "Nanobot 已在运行 (PID: $pid)"
        echo "    如需重启请使用: $0 restart"
        return 1
    fi

    mkdir -p "$LOG_DIR"

    bold "🤖 Nanobot Gateway"
    echo ""
    info "端口: $port"
    info "日志: $LOG_FILE"
    echo ""

    # 后台启动，stdout/stderr 写入日志
    local cmd=("$NANOBOT_CMD" "gateway" "--port" "$port")
    if [ -n "$verbose" ]; then
        cmd+=("$verbose")
    fi
    nohup "${cmd[@]}" >> "$LOG_FILE" 2>&1 &
    local pid=$!
    echo "$pid" > "$PID_FILE"

    # 等待并检查是否成功启动
    sleep 2
    if kill -0 "$pid" 2>/dev/null; then
        info "启动成功 (PID: $pid)"
    else
        error "启动失败，请查看日志:"
        echo "    tail -50 $LOG_FILE"
        rm -f "$PID_FILE"
        return 1
    fi
}

# ---------------------------------------------------------------------------
# stop
# ---------------------------------------------------------------------------
do_stop() {
    local pid
    pid=$(get_running_pid)

    if [ -z "$pid" ]; then
        warn "Nanobot 未在运行"
        rm -f "$PID_FILE"
        return 0
    fi

    echo -n "正在停止 Nanobot (PID: $pid) ..."

    # 先发 SIGTERM，给进程优雅关闭的机会
    kill "$pid" 2>/dev/null || true

    # 等待进程退出，最多 10 秒
    local waited=0
    while kill -0 "$pid" 2>/dev/null && [ $waited -lt 10 ]; do
        sleep 1
        waited=$((waited + 1))
        echo -n "."
    done
    echo ""

    # 如果还没退出，强制终止
    if kill -0 "$pid" 2>/dev/null; then
        warn "进程未响应，强制终止"
        kill -9 "$pid" 2>/dev/null || true
        sleep 1
    fi

    rm -f "$PID_FILE"
    info "Nanobot 已停止"
}

# ---------------------------------------------------------------------------
# restart
# ---------------------------------------------------------------------------
do_restart() {
    do_stop
    echo ""
    do_start "$@"
}

# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------
do_status() {
    local pid
    pid=$(get_running_pid)

    bold "🤖 Nanobot 状态"
    echo ""

    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        info "运行中 (PID: $pid)"
        echo ""

        # 显示进程详情
        echo -e "${CYAN}进程信息:${NC}"
        ps -p "$pid" -o pid,user,%cpu,%mem,etime,command | head -2
        echo ""

        # 显示最近日志
        if [ -f "$LOG_FILE" ]; then
            echo -e "${CYAN}最近日志 (最后 5 行):${NC}"
            tail -5 "$LOG_FILE" 2>/dev/null || true
        fi
    else
        error "未运行"
        rm -f "$PID_FILE"

        # 检查是否有残留进程
        local orphan
        orphan=$(ps ax -o pid,command | grep '[n]anobot' | grep -v "$0" | grep -v grep || true)
        if [ -n "$orphan" ]; then
            echo ""
            warn "发现残留进程:"
            echo "$orphan"
            echo ""
            echo "    可使用 $0 stop 清理"
        fi
    fi
}

# ---------------------------------------------------------------------------
# logs
# ---------------------------------------------------------------------------
do_logs() {
    local follow=false
    local lines=50

    while [[ $# -gt 0 ]]; do
        case "$1" in
            -f|--follow) follow=true; shift ;;
            -n|--lines)  lines="$2"; shift 2 ;;
            *) error "未知参数: $1"; exit 1 ;;
        esac
    done

    if [ ! -f "$LOG_FILE" ]; then
        warn "日志文件不存在: $LOG_FILE"
        return 1
    fi

    if $follow; then
        info "实时日志 (Ctrl+C 退出)"
        echo ""
        tail -f -n "$lines" "$LOG_FILE"
    else
        tail -n "$lines" "$LOG_FILE"
    fi
}

# ---------------------------------------------------------------------------
# 帮助
# ---------------------------------------------------------------------------
do_help() {
    bold "🤖 Nanobot 服务管理脚本"
    echo ""
    echo "用法: $0 <命令> [选项]"
    echo ""
    bold "命令:"
    echo "  start    [-p PORT] [-v]     后台启动 gateway (默认端口 18790)"
    echo "  stop                        停止服务"
    echo "  restart  [-p PORT] [-v]     重启服务"
    echo "  status                      查看运行状态"
    echo "  logs     [-f] [-n LINES]    查看日志 (-f 实时跟踪)"
    echo ""
    bold "示例:"
    echo "  $0 start                    使用默认端口启动"
    echo "  $0 start -p 8080            指定端口启动"
    echo "  $0 stop                     停止服务"
    echo "  $0 restart                  重启服务"
    echo "  $0 status                   查看状态"
    echo "  $0 logs -f                  实时查看日志"
    echo "  $0 logs -n 100              查看最近 100 行日志"
}

# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------
COMMAND="${1:-}"
shift || true

case "$COMMAND" in
    start)   do_start "$@" ;;
    stop)    do_stop ;;
    restart) do_restart "$@" ;;
    status)  do_status ;;
    logs)    do_logs "$@" ;;
    help|-h|--help) do_help ;;
    "")
        do_help
        exit 1
        ;;
    *)
        error "未知命令: $COMMAND"
        echo ""
        do_help
        exit 1
        ;;
esac
