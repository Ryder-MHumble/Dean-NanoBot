#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
#  Nanobot — Deploy & Manage
#  Usage:  ./deploy.sh [command] [options]
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"
PID_FILE="/tmp/nanobot.pid"
NANOBOT_DIR="$HOME/.nanobot"
LOG_DIR="$NANOBOT_DIR/logs"
LOG_FILE="$LOG_DIR/gateway.log"
CONFIG_FILE="$NANOBOT_DIR/config.json"
ENV_FILE="$PROJECT_DIR/.env"
VERSION=$(grep '^version' "$PROJECT_DIR/pyproject.toml" 2>/dev/null \
    | head -1 | sed 's/version = "\(.*\)"/\1/' || echo "0.0.0")

PORT=18790
TAIL_LINES=50
FOLLOW=false

# Load .env early so all NANOBOT_* vars are available
if [[ -f "$ENV_FILE" ]]; then
    set -o allexport
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +o allexport
fi

# ── ANSI ──────────────────────────────────────────────────────
R='\033[0;31m';   G='\033[0;32m';  Y='\033[0;33m'
B='\033[0;34m';   M='\033[0;35m';  C='\033[0;36m'
W='\033[0;37m';   D='\033[0;90m';  BOLD='\033[1m'
BW='\033[1;97m';  BC='\033[1;36m'
NC='\033[0m'
P1='\033[38;5;57m'; P2='\033[38;5;63m'; P3='\033[38;5;69m'
P4='\033[38;5;75m'; P5='\033[38;5;81m'; P6='\033[38;5;87m'

# ── Utilities ─────────────────────────────────────────────────
_hr()  { printf "${D}"; printf '─%.0s' $(seq 1 60); printf "${NC}\n"; }
ok()   { printf " ${G}✓${NC}  %b\n" "$*"; }
warn() { printf " ${Y}!${NC}  %b\n" "$*"; }
fail() { printf " ${R}✗${NC}  %b\n" "$*"; }
dim()  { printf " ${D}%b${NC}\n" "$*"; }

spinner() {
    local pid=$1 msg="$2"
    local chars='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    local i=0
    while kill -0 "$pid" 2>/dev/null; do
        printf "\r ${C}%s${NC} %s" "${chars:i%10:1}" "$msg"
        i=$((i + 1))
        sleep 0.1
    done
    printf "\r\033[2K"
}

# ── Banner ────────────────────────────────────────────────────
show_banner() {
    printf "\n"
    printf "  ${P1}${BOLD}██╗   ██╗ █████╗ ███╗  ██╗  ██████╗ ██████╗  ██████╗ ████████╗${NC}\n"
    printf "  ${P2}${BOLD}████╗ ██║██╔══██╗████╗ ██║ ██╔═══██╗██╔══██╗██╔═══██╗╚══██╔══╝${NC}\n"
    printf "  ${P3}${BOLD}██╔████╔╝███████║██╔████╔╝ ██║   ██║██████╔╝██║   ██║   ██║   ${NC}\n"
    printf "  ${P4}${BOLD}██║╚██╔╝ ██╔══██║██║╚██╔╝  ██║   ██║██╔══██╗██║   ██║   ██║   ${NC}\n"
    printf "  ${P5}${BOLD}██║ ╚═╝  ██║  ██║██║ ╚═╝   ╚██████╔╝██████╔╝╚██████╔╝   ██║   ${NC}\n"
    printf "  ${P6}${BOLD}╚═╝      ╚═╝  ╚═╝╚═╝        ╚═════╝ ╚═════╝  ╚═════╝   ╚═╝   ${NC}\n"
    printf "\n"
    printf "  ${P3}%s${NC}\n" "$(printf '%.0s═' {1..56})"
    printf "  ${P2}${BOLD}智能机器人服务${NC} ${D}·${NC} ${D}Multi-Channel AI Agent${NC}\n"
    printf "  ${P3}%s${NC}\n" "$(printf '%.0s═' {1..56})"
    printf "\n"
    local _branch _py _time
    _branch=$(git branch --show-current 2>/dev/null || echo 'unknown')
    _py=$(python3 --version 2>/dev/null | cut -d' ' -f2 || echo 'N/A')
    _time=$(date '+%Y-%m-%d  %H:%M:%S')
    printf "  ${D}TIME${NC}   ${BW}%s${NC}    ${D}PORT${NC}   ${BC}${BOLD}:%s${NC}\n" "$_time" "$PORT"
    printf "  ${D}BRANCH${NC} ${Y}%s${NC}          ${D}PYTHON${NC} ${G}%s${NC}\n" "$_branch" "$_py"
    printf "  ${D}TARGET${NC} ${D}43.98.254.243${NC}    ${D}v%s${NC}\n" "$VERSION"
    printf "\n"
    _hr
}

# ── Environment ───────────────────────────────────────────────
validate_python() {
    python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null
}

get_python_ver() {
    python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "?"
}

ensure_venv() {
    local create="${1:-false}"
    [[ -n "${VIRTUAL_ENV:-}" && "$VIRTUAL_ENV" == "$VENV_DIR" ]] && return 0
    if [[ -f "$VENV_DIR/bin/activate" ]]; then
        # shellcheck disable=SC1091
        source "$VENV_DIR/bin/activate"
        return 0
    fi
    if [[ "$create" == "true" ]]; then
        python3 -m venv "$VENV_DIR" 2>/dev/null
        # shellcheck disable=SC1091
        source "$VENV_DIR/bin/activate"
        pip install --upgrade pip -q 2>/dev/null
        return 0
    fi
    return 1
}

validate_env_file() {
    if [[ ! -f "$ENV_FILE" ]]; then
        [[ -f "$PROJECT_DIR/.env.example" ]] && cp "$PROJECT_DIR/.env.example" "$ENV_FILE"
        return 0
    fi
    # Clean garbage from bad vim exits
    if grep -qE '^(exit\(\)|q|:q|:wq|:x)\s*$' "$ENV_FILE" 2>/dev/null; then
        if [[ "$(uname)" == "Darwin" ]]; then
            sed -i '' '/^exit()$/d; /^q$/d; /^:q$/d; /^:wq$/d; /^:x$/d' "$ENV_FILE"
        else
            sed -i '/^exit()$/d; /^q$/d; /^:q$/d; /^:wq$/d; /^:x$/d' "$ENV_FILE"
        fi
    fi
}

has_env_key() { grep -q "${1}=.\+" "$ENV_FILE" 2>/dev/null; }

install_deps() {
    cd "$PROJECT_DIR"
    pip install -e "." -q > /dev/null 2>&1 &
    local pid=$!
    spinner $pid "Installing Python dependencies..."
    wait $pid
}

install_extra_deps() {
    # supabase is needed by sentiment-monitor scripts but not in pyproject.toml
    pip install supabase -q > /dev/null 2>&1 &
    local pid=$!
    spinner $pid "Installing extra dependencies (supabase)..."
    wait $pid || true   # non-fatal
}

ensure_dirs() {
    mkdir -p "$LOG_DIR" "$NANOBOT_DIR/sessions" "$NANOBOT_DIR/workspace"
}

# Generate ~/.nanobot/config.json from .env if it doesn't exist
gen_config() {
    [[ -f "$CONFIG_FILE" ]] && return 0
    mkdir -p "$NANOBOT_DIR"
    python3 - <<'PYEOF'
import os, json
from pathlib import Path

config = {
    "agents": {
        "defaults": {
            "workspace": "~/.nanobot/workspace",
            "model": os.environ.get("NANOBOT_AGENTS__DEFAULTS__MODEL",
                                    "openrouter/anthropic/claude-sonnet-4-5"),
            "maxTokens": 8192,
            "temperature": 0.7,
            "maxToolIterations": 20
        }
    },
    "channels": {
        "dingtalk": {
            "enabled": True,
            "clientId":     os.environ.get("NANOBOT_CHANNELS__DINGTALK__CLIENT_ID", ""),
            "clientSecret": os.environ.get("NANOBOT_CHANNELS__DINGTALK__CLIENT_SECRET", ""),
            "allowFrom": []
        }
    },
    "providers": {
        "openrouter": {
            "apiKey":       os.environ.get("NANOBOT_PROVIDERS__OPENROUTER__API_KEY", ""),
            "apiBase":      None,
            "extraHeaders": None
        }
    },
    "gateway": {
        "host": "0.0.0.0",
        "port": int(os.environ.get("NANOBOT_GATEWAY__PORT", "18790"))
    }
}

config_path = Path.home() / ".nanobot" / "config.json"
with open(config_path, "w") as f:
    json.dump(config, f, indent=2)
print(f"  config → {config_path}")
PYEOF
}

# ── Git ───────────────────────────────────────────────────────
do_git_pull() {
    cd "$PROJECT_DIR"
    if ! git rev-parse --is-inside-work-tree &>/dev/null; then
        warn "Not a git repo — skipping pull"
        return 0
    fi
    local branch before after count
    branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
    before=$(git rev-parse HEAD 2>/dev/null)
    printf " ${C}⟳${NC}  Pulling latest code ${D}(%s)${NC}..." "$branch"
    if git pull --ff-only -q 2>/dev/null; then
        after=$(git rev-parse HEAD 2>/dev/null)
        if [[ "$before" == "$after" ]]; then
            printf "\r ${G}✓${NC}  Code is up-to-date ${D}(%s)${NC}        \n" "$branch"
        else
            count=$(git rev-list "$before".."$after" --count 2>/dev/null || echo "?")
            printf "\r ${G}✓${NC}  Pulled ${BOLD}%s${NC} new commit(s) ${D}(%s)${NC}       \n" "$count" "$branch"
        fi
    else
        printf "\r ${Y}!${NC}  Pull failed — continuing with local code\n"
    fi
}

# ── Service ───────────────────────────────────────────────────
_get_running_pid() {
    ps ax -o pid,command 2>/dev/null \
        | grep '[n]anobot gateway' | grep -v "$0" | awk '{print $1}' | head -1
}

_is_running() {
    local pid; pid=$(_get_running_pid)
    [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null
}

_stop_service() {
    local pid; pid=$(_get_running_pid)
    [[ -z "$pid" ]] && { rm -f "$PID_FILE"; return 0; }
    kill "$pid" 2>/dev/null || true
    local w=0
    while kill -0 "$pid" 2>/dev/null && [[ $w -lt 10 ]]; do sleep 1; w=$((w+1)); done
    kill -0 "$pid" 2>/dev/null && { kill -9 "$pid" 2>/dev/null || true; sleep 1; }
    rm -f "$PID_FILE"
}

_start_service() {
    mkdir -p "$LOG_DIR"
    rm -f "$PID_FILE"
    cd "$PROJECT_DIR"
    nohup "$VENV_DIR/bin/nanobot" gateway --port "$PORT" >> "$LOG_FILE" 2>&1 &
    local pid=$!
    echo "$pid" > "$PID_FILE"
    sleep 2
    kill -0 "$pid" 2>/dev/null
}

_wait_start() {
    local max=15 i=0
    local chars='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    printf " ${C}⟳${NC} Waiting for process to stabilize..."
    while [[ $i -lt $max ]]; do
        if _is_running; then
            printf "\r ${G}✓${NC}  Service is running ${D}(PID %s)${NC}    \n" "$(_get_running_pid)"
            return 0
        fi
        printf "\r ${C}%s${NC} Waiting for process..." "${chars:i%10:1}"
        sleep 1; i=$((i+1))
    done
    printf "\r ${R}✗${NC}  Service failed to start — check logs\n"
    return 1
}

# ── Dashboard ─────────────────────────────────────────────────
show_dashboard() {
    printf "\n"
    printf " ${BOLD}${C}◆ Dashboard${NC}\n"
    _hr

    if _is_running; then
        local pid; pid=$(_get_running_pid)
        local etime cpu mem_kb mem_mb
        etime=$(ps -p "$pid" -o etime= 2>/dev/null | xargs || echo "-")
        cpu=$(ps -p "$pid" -o %cpu= 2>/dev/null | xargs || echo "-")
        mem_kb=$(ps -p "$pid" -o rss= 2>/dev/null | xargs || echo "0")
        mem_mb=$(echo "$mem_kb" | awk '{printf "%.1f", $1/1024}')

        printf "\n"
        printf "   ${BOLD}SERVICE${NC}\n"
        printf "   %-18s ${G}● Running${NC}\n" "Status"
        printf "   %-18s %s\n" "PID" "$pid"
        printf "   %-18s %s\n" "Port" "$PORT"
        printf "   %-18s %s\n" "Uptime" "$etime"
        printf "\n"
        printf "   ${BOLD}RESOURCES${NC}\n"
        printf "   %-18s %s%%\n" "CPU" "$cpu"
        printf "   %-18s %s MB\n" "Memory" "$mem_mb"
        if [[ -f "$LOG_FILE" ]]; then
            local log_size; log_size=$(du -h "$LOG_FILE" | cut -f1 | xargs)
            printf "   %-18s %s\n" "Log size" "$log_size"
        fi
    else
        printf "\n"
        printf "   ${BOLD}SERVICE${NC}\n"
        printf "   %-18s ${R}● Stopped${NC}\n" "Status"
    fi

    # Channels
    printf "\n"
    printf "   ${BOLD}CHANNELS${NC}\n"
    if [[ -f "$CONFIG_FILE" ]]; then
        python3 - "$CONFIG_FILE" 2>/dev/null <<'PYEOF' || true
import json, sys
d = json.load(open(sys.argv[1]))
chs = d.get("channels", {})
items = [
    ("dingtalk",  "🔔 DingTalk",  ["clientId"]),
    ("feishu",    "🪐 Feishu",    ["appId"]),
    ("telegram",  "✈️  Telegram",  ["token"]),
    ("slack",     "💬 Slack",     ["botToken"]),
    ("discord",   "🎮 Discord",   ["token"]),
    ("qq",        "🐧 QQ",        ["appId"]),
]
for key, label, id_fields in items:
    ch = chs.get(key, {})
    if ch.get("enabled"):
        cid = next((ch.get(f, "") for f in id_fields if ch.get(f)), "")
        masked = (cid[:8] + "...") if len(cid) > 8 else cid
        print(f"   \033[32m●\033[0m {label:<18} {masked}")
    else:
        print(f"   \033[90m○\033[0m \033[90m{label}\033[0m")
PYEOF
    else
        if [[ -n "${NANOBOT_CHANNELS__DINGTALK__CLIENT_ID:-}" ]]; then
            local masked="${NANOBOT_CHANNELS__DINGTALK__CLIENT_ID:0:8}..."
            printf "   ${G}●${NC} %-18s %s\n" "🔔 DingTalk" "$masked"
        else
            printf "   ${Y}!${NC} %-18s ${Y}not configured${NC}\n" "🔔 DingTalk"
        fi
    fi

    # Integrations
    printf "\n"
    printf "   ${BOLD}INTEGRATIONS${NC}\n"
    if [[ -n "${SUPABASE_KEY:-}" && -n "${SUPABASE_URL:-}" ]]; then
        local url_id; url_id=$(echo "${SUPABASE_URL:-}" | sed 's|https://\([^.]*\).*|\1|')
        printf "   ${G}●${NC} %-18s %s.supabase.co\n" "☁  Supabase" "$url_id"
    else
        printf "   ${D}○${NC} ${D}%-18s not configured${NC}\n" "☁  Supabase"
    fi

    # Cron jobs
    local jobs_file="$NANOBOT_DIR/cron/jobs.json"
    if [[ -f "$jobs_file" ]]; then
        python3 - "$jobs_file" 2>/dev/null <<'PYEOF' || true
import json, sys
from datetime import datetime, timezone
data = json.load(open(sys.argv[1]))
jobs = [j for j in data.get("jobs", []) if j.get("enabled")]
print(f"   \033[32m●\033[0m \033[0mCron               {len(jobs)} active job(s)\033[0m")
for j in jobs:
    name = j.get("name", "")[:30]
    expr = j.get("schedule", {}).get("expr", "?")
    next_ms = j.get("state", {}).get("nextRunAtMs")
    if next_ms:
        next_dt = datetime.fromtimestamp(next_ms / 1000, tz=timezone.utc).strftime("%m-%d %H:%M UTC")
    else:
        next_dt = "—"
    print(f"   \033[90m  {expr:<14} {name:<30} next: {next_dt}\033[0m")
PYEOF
    else
        printf "   ${D}○${NC} ${D}Cron               no jobs${NC}\n"
    fi

    printf "\n"
    _hr
}

# ── Commands ──────────────────────────────────────────────────
cmd_deploy() {
    show_banner

    printf "\n ${BOLD}${C}◆ Deploy${NC}\n"
    _hr
    printf "\n"

    # 1. Git pull
    do_git_pull

    # 2. Python
    if validate_python; then
        ok "Python $(get_python_ver)"
    else
        fail "Python >= 3.11 required (found $(get_python_ver))"; return 1
    fi

    # 3. Venv
    if [[ -f "$VENV_DIR/bin/activate" ]]; then
        ensure_venv true; ok "Virtual environment ${D}.venv${NC}"
    else
        ensure_venv true; ok "Virtual environment ${D}.venv (created)${NC}"
    fi

    # 4. .env
    validate_env_file
    if [[ -f "$ENV_FILE" ]]; then
        set -o allexport; source "$ENV_FILE"; set +o allexport
        ok "Environment file ${D}.env${NC}"
        has_env_key "NANOBOT_CHANNELS__DINGTALK__CLIENT_ID" \
            && dim "   DingTalk credentials configured" \
            || warn "NANOBOT_CHANNELS__DINGTALK__CLIENT_ID not set"
        has_env_key "NANOBOT_PROVIDERS__OPENROUTER__API_KEY" \
            && dim "   LLM API key configured" \
            || warn "No LLM API key — check .env"
        has_env_key "SUPABASE_KEY" \
            && dim "   Supabase key configured" \
            || warn "SUPABASE_KEY not set — sentiment monitor disabled"
    else
        fail "No .env file — copy .env.example and fill in credentials"; return 1
    fi

    # 5. Dependencies
    local t0; t0=$(date +%s)
    install_deps && ok "Dependencies installed ${D}$(($(date +%s) - t0))s${NC}" \
        || { fail "pip install failed"; return 1; }

    install_extra_deps && ok "Extra dependencies ${D}(supabase)${NC}"

    # 6. Directories
    ensure_dirs && ok "Data directories"

    # 7. Config
    if [[ ! -f "$CONFIG_FILE" ]]; then
        gen_config && ok "Config generated ${D}~/.nanobot/config.json${NC}" \
            || warn "Config generation failed — check env vars"
    else
        ok "Config exists ${D}~/.nanobot/config.json${NC}"
    fi

    # 8. Restart
    printf "\n"
    if _is_running; then
        local old_pid; old_pid=$(_get_running_pid)
        printf " ${Y}⟳${NC}  Restarting service ${D}(was PID %s)${NC}...\n" "$old_pid"
        _stop_service; sleep 1
    fi

    if _start_service; then
        ok "Service started ${D}PID $(_get_running_pid)${NC}"
    else
        fail "Service failed to start"
        dim "  tail -50 $LOG_FILE"
        return 1
    fi

    show_dashboard

    printf " ${G}${BOLD}Deploy complete.${NC}\n\n"
    dim "  ./deploy.sh status    View dashboard"
    dim "  ./deploy.sh logs -f   Follow logs"
    dim "  ./deploy.sh stop      Stop service"
    printf "\n"
}

cmd_init() {
    show_banner

    printf "\n ${BOLD}${C}◆ Initialize${NC}\n"
    _hr
    printf "\n"

    validate_python && ok "Python $(get_python_ver)" \
        || { fail "Python >= 3.11 required"; return 1; }

    ensure_venv true && ok "Virtual environment"

    validate_env_file
    if [[ -f "$ENV_FILE" ]]; then
        ok "Environment file ${D}.env${NC}"
        warn "Edit .env and fill in your credentials before deploying"
    else
        fail "Could not create .env — check that .env.example exists"
    fi

    local t0; t0=$(date +%s)
    install_deps && ok "Dependencies ${D}$(($(date +%s) - t0))s${NC}" \
        || { fail "pip install failed"; return 1; }

    install_extra_deps && ok "Extra dependencies ${D}(supabase)${NC}"

    ensure_dirs && ok "Data directories"

    if [[ ! -f "$CONFIG_FILE" ]]; then
        if [[ -f "$ENV_FILE" ]]; then
            set -o allexport; source "$ENV_FILE"; set +o allexport
            gen_config && ok "Config generated ${D}~/.nanobot/config.json${NC}"
        else
            warn "Config skipped — set env vars in .env first"
        fi
    else
        ok "Config exists ${D}~/.nanobot/config.json${NC}"
    fi

    printf "\n"
    _hr
    printf "\n ${G}${BOLD}Init complete.${NC} Next steps:\n\n"
    dim "  nano .env             Edit credentials"
    dim "  ./deploy.sh           Full deploy"
    dim "  ./deploy.sh start     Start only"
    printf "\n"
}

cmd_start() {
    show_banner

    if ! ensure_venv; then
        fail "No virtual environment — run: ./deploy.sh init"; return 1
    fi

    if _is_running; then
        warn "Already running (PID $(_get_running_pid))"
        show_dashboard; return 0
    fi

    printf " ${C}⟳${NC}  Starting service...\n"
    if _start_service; then
        ok "Service started ${D}PID $(_get_running_pid)${NC}"
        show_dashboard
    else
        fail "Failed to start — check $LOG_FILE"
        dim "  tail -50 $LOG_FILE"
    fi
}

cmd_stop() {
    show_banner

    if ! _is_running; then
        dim "Service is not running."; return 0
    fi

    local pid; pid=$(_get_running_pid)
    printf " ${C}⟳${NC}  Stopping service (PID %s)...\n" "$pid"
    _stop_service
    ok "Service stopped"
}

cmd_restart() {
    show_banner

    if ! ensure_venv; then
        fail "No virtual environment — run: ./deploy.sh init"; return 1
    fi

    if _is_running; then
        local pid; pid=$(_get_running_pid)
        printf " ${C}⟳${NC}  Restarting (PID %s)...\n" "$pid"
        _stop_service; sleep 1
    fi

    if _start_service; then
        ok "Service started ${D}PID $(_get_running_pid)${NC}"
        show_dashboard
    else
        fail "Failed to start — check $LOG_FILE"
        dim "  tail -50 $LOG_FILE"
    fi
}

cmd_status() {
    show_banner
    show_dashboard
}

cmd_logs() {
    if [[ ! -f "$LOG_FILE" ]]; then
        warn "Log file not found: $LOG_FILE"; return 0
    fi
    if [[ "$FOLLOW" == "true" ]]; then
        dim "Tailing $LOG_FILE (Ctrl+C to stop)"
        printf "\n"
        tail -n "$TAIL_LINES" -f "$LOG_FILE"
    else
        tail -n "$TAIL_LINES" "$LOG_FILE"
    fi
}

cmd_help() {
    show_banner
    printf " ${BOLD}Usage${NC}  ./deploy.sh ${D}[command] [options]${NC}\n\n"

    printf " ${BOLD}Commands${NC}\n\n"
    printf "   ${G}deploy${NC}     Full deploy: pull → venv → deps → start  ${D}(default)${NC}\n"
    printf "   ${G}init${NC}       Initialize environment only\n"
    printf "   ${G}start${NC}      Start service\n"
    printf "   ${G}stop${NC}       Stop service\n"
    printf "   ${G}restart${NC}    Restart service\n"
    printf "   ${G}status${NC}     Show dashboard\n"
    printf "   ${G}logs${NC}       View logs ${D}(-f to follow)${NC}\n"
    printf "   ${G}monitor${NC}    Real-time resource dashboard\n"
    printf "   ${G}help${NC}       This message\n"

    printf "\n ${BOLD}Options${NC}\n\n"
    printf "   --port N          Gateway port ${D}(default: %s)${NC}\n" "$PORT"
    printf "   --tail N          Log lines ${D}(default: %s)${NC}\n" "$TAIL_LINES"
    printf "   -f, --follow      Follow log output\n"

    printf "\n ${BOLD}Server setup (first time)${NC}\n\n"
    printf "   ${D}\$${NC} git clone <repo> && cd nanobot\n"
    printf "   ${D}\$${NC} cp .env.example .env && nano .env    ${D}# fill in credentials${NC}\n"
    printf "   ${D}\$${NC} ./deploy.sh init                     ${D}# install deps${NC}\n"
    printf "   ${D}\$${NC} ./deploy.sh                          ${D}# deploy & start${NC}\n"

    printf "\n ${BOLD}Examples${NC}\n\n"
    printf "   ${D}\$${NC} ./deploy.sh              ${D}# one-command deploy${NC}\n"
    printf "   ${D}\$${NC} ./deploy.sh logs -f       ${D}# follow logs${NC}\n"
    printf "   ${D}\$${NC} ./deploy.sh status         ${D}# view dashboard${NC}\n"
    printf "\n"
}

cmd_monitor() {
    local script="$PROJECT_DIR/monitor.sh"
    if [[ ! -x "$script" ]]; then
        fail "monitor.sh not found or not executable"; return 1
    fi
    exec "$script" "$@"
}

# ── Parse Args ────────────────────────────────────────────────
COMMAND="${1:-deploy}"
shift 2>/dev/null || true

while [[ $# -gt 0 ]]; do
    case "$1" in
        --port)      PORT="$2"; shift 2 ;;
        --tail)      TAIL_LINES="$2"; shift 2 ;;
        --follow|-f) FOLLOW=true; shift ;;
        *) fail "Unknown option: $1"; cmd_help; exit 1 ;;
    esac
done

case "$COMMAND" in
    deploy)         cmd_deploy ;;
    init)           cmd_init ;;
    start)          cmd_start ;;
    stop)           cmd_stop ;;
    restart)        cmd_restart ;;
    status)         cmd_status ;;
    logs)           cmd_logs ;;
    monitor)        cmd_monitor ;;
    help|--help|-h) cmd_help ;;
    *)              fail "Unknown command: $COMMAND"; cmd_help; exit 1 ;;
esac
