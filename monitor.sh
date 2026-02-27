#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
#  Nanobot — Real-time Server Monitor Dashboard
#  Usage:  ./monitor.sh [-i SECONDS]
#  Requires: Linux with /proc filesystem
# ═══════════════════════════════════════════════════════════════
set -uo pipefail

# ── ANSI Colors (matching deploy.sh palette) ─────────────────
R='\033[0;31m';   G='\033[0;32m';  Y='\033[0;33m'
B='\033[0;34m';   C='\033[0;36m'
D='\033[0;90m';   BOLD='\033[1m'
BW='\033[1;97m';  NC='\033[0m'
P1='\033[38;5;57m'; P2='\033[38;5;63m'; P3='\033[38;5;69m'
P4='\033[38;5;75m'; P5='\033[38;5;81m'; P6='\033[38;5;87m'

# ── Config ───────────────────────────────────────────────────
INTERVAL=2
BAR_WIDTH=30

# ── Parse args ───────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        -i|--interval) INTERVAL="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: ./monitor.sh [-i SECONDS]"
            echo "  -i, --interval  Refresh interval (default: 2)"
            exit 0 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# ── Check /proc ──────────────────────────────────────────────
if [[ ! -d /proc/stat ]] && [[ ! -f /proc/stat ]]; then
    if [[ ! -f /proc/stat ]]; then
        printf "${R}Error:${NC} /proc/stat not found. This script requires Linux.\n"
        exit 1
    fi
fi

# ── Globals for CPU delta ────────────────────────────────────
declare -A PREV_CPU_TOTAL PREV_CPU_IDLE
declare -A PREV_NET_RX PREV_NET_TX
FIRST_RUN=true

# ── Helper: progress bar ────────────────────────────────────
# Usage: draw_bar <percent> <width>
draw_bar() {
    local pct=$1 width=$2
    local filled=$(( pct * width / 100 ))
    local empty=$(( width - filled ))
    local color

    if   (( pct >= 85 )); then color="$R"
    elif (( pct >= 60 )); then color="$Y"
    else                       color="$G"
    fi

    printf "${color}"
    (( filled > 0 )) && printf '█%.0s' $(seq 1 "$filled")
    printf "${D}"
    (( empty > 0 )) && printf '░%.0s' $(seq 1 "$empty")
    printf "${NC}"
}

# ── Helper: human-readable bytes ─────────────────────────────
human_bytes() {
    local bytes=$1
    if   (( bytes >= 1073741824 )); then
        printf "%.1f GB" "$(echo "$bytes / 1073741824" | bc -l 2>/dev/null || echo 0)"
    elif (( bytes >= 1048576 )); then
        printf "%.1f MB" "$(echo "$bytes / 1048576" | bc -l 2>/dev/null || echo 0)"
    elif (( bytes >= 1024 )); then
        printf "%.1f KB" "$(echo "$bytes / 1024" | bc -l 2>/dev/null || echo 0)"
    else
        printf "%d B" "$bytes"
    fi
}

# ── Helper: human-readable bytes/s ───────────────────────────
human_rate() {
    local bps=$1
    if   (( bps >= 1073741824 )); then
        printf "%.1f GB/s" "$(echo "$bps / 1073741824" | bc -l 2>/dev/null || echo 0)"
    elif (( bps >= 1048576 )); then
        printf "%.1f MB/s" "$(echo "$bps / 1048576" | bc -l 2>/dev/null || echo 0)"
    elif (( bps >= 1024 )); then
        printf "%.1f KB/s" "$(echo "$bps / 1024" | bc -l 2>/dev/null || echo 0)"
    else
        printf "%d B/s" "$bps"
    fi
}

# ── Helper: format uptime ────────────────────────────────────
format_uptime() {
    local secs=$1
    local days=$(( secs / 86400 ))
    local hours=$(( (secs % 86400) / 3600 ))
    local mins=$(( (secs % 3600) / 60 ))
    if (( days > 0 )); then
        printf "%dd %dh %dm" "$days" "$hours" "$mins"
    elif (( hours > 0 )); then
        printf "%dh %dm" "$hours" "$mins"
    else
        printf "%dm" "$mins"
    fi
}

# ── Helper: horizontal line ──────────────────────────────────
_hr() {
    local w=${1:-60}
    printf "${D}"
    printf '─%.0s' $(seq 1 "$w")
    printf "${NC}\n"
}

# ── Helper: section header ───────────────────────────────────
section() {
    printf "  ${BOLD}${P3}%-10s${NC}" "$1"
    shift
    [[ $# -gt 0 ]] && printf " ${D}%s${NC}" "$*"
    printf "\n"
}

# ── Data: read CPU ───────────────────────────────────────────
read_cpu() {
    local line name user nice system idle iowait irq softirq steal
    while IFS= read -r line; do
        if [[ "$line" =~ ^cpu ]]; then
            read -r name user nice system idle iowait irq softirq steal _ <<< "$line"
            local total=$(( user + nice + system + idle + iowait + irq + softirq + steal ))
            local idle_val=$(( idle + iowait ))
            local key="$name"

            if [[ "$FIRST_RUN" == "true" ]]; then
                PREV_CPU_TOTAL[$key]=$total
                PREV_CPU_IDLE[$key]=$idle_val
                CPU_PCT[$key]=0
            else
                local dt=$(( total - ${PREV_CPU_TOTAL[$key]:-0} ))
                local di=$(( idle_val - ${PREV_CPU_IDLE[$key]:-0} ))
                if (( dt > 0 )); then
                    CPU_PCT[$key]=$(( (dt - di) * 100 / dt ))
                else
                    CPU_PCT[$key]=0
                fi
                PREV_CPU_TOTAL[$key]=$total
                PREV_CPU_IDLE[$key]=$idle_val
            fi
        fi
    done < /proc/stat

    CPU_CORES=$(nproc 2>/dev/null || grep -c '^processor' /proc/cpuinfo 2>/dev/null || echo 1)
}

# ── Data: read memory ────────────────────────────────────────
read_memory() {
    local key val unit
    MEM_TOTAL=0; MEM_FREE=0; MEM_AVAIL=0; MEM_BUFFERS=0; MEM_CACHED=0
    SWAP_TOTAL=0; SWAP_FREE=0

    while IFS=': ' read -r key val unit; do
        case "$key" in
            MemTotal)     MEM_TOTAL=$val ;;
            MemFree)      MEM_FREE=$val ;;
            MemAvailable) MEM_AVAIL=$val ;;
            Buffers)      MEM_BUFFERS=$val ;;
            Cached)       MEM_CACHED=$val ;;
            SwapTotal)    SWAP_TOTAL=$val ;;
            SwapFree)     SWAP_FREE=$val ;;
        esac
    done < /proc/meminfo

    # All values in kB
    MEM_USED=$(( MEM_TOTAL - MEM_AVAIL ))
    SWAP_USED=$(( SWAP_TOTAL - SWAP_FREE ))

    if (( MEM_TOTAL > 0 )); then
        MEM_PCT=$(( MEM_USED * 100 / MEM_TOTAL ))
    else
        MEM_PCT=0
    fi
    if (( SWAP_TOTAL > 0 )); then
        SWAP_PCT=$(( SWAP_USED * 100 / SWAP_TOTAL ))
    else
        SWAP_PCT=0
    fi
}

# ── Data: read network ───────────────────────────────────────
read_network() {
    NET_IFACE=""
    NET_RX_RATE=0
    NET_TX_RATE=0

    local iface rx_bytes tx_bytes
    while IFS= read -r line; do
        [[ "$line" == *"lo:"* ]] && continue
        [[ "$line" == *"face"* ]] && continue
        if [[ "$line" =~ ^\ *([a-zA-Z0-9]+):\ *([0-9]+)\ +[0-9]+\ +[0-9]+\ +[0-9]+\ +[0-9]+\ +[0-9]+\ +[0-9]+\ +[0-9]+\ +([0-9]+) ]]; then
            iface="${BASH_REMATCH[1]}"
            rx_bytes="${BASH_REMATCH[2]}"
            tx_bytes="${BASH_REMATCH[3]}"

            # Pick the first non-lo interface with traffic
            if [[ -z "$NET_IFACE" ]] || [[ "$iface" == eth* ]] || [[ "$iface" == ens* ]]; then
                NET_IFACE="$iface"

                if [[ "$FIRST_RUN" == "true" ]]; then
                    PREV_NET_RX[$iface]=$rx_bytes
                    PREV_NET_TX[$iface]=$tx_bytes
                    NET_RX_RATE=0
                    NET_TX_RATE=0
                else
                    local prev_rx=${PREV_NET_RX[$iface]:-0}
                    local prev_tx=${PREV_NET_TX[$iface]:-0}
                    NET_RX_RATE=$(( (rx_bytes - prev_rx) / INTERVAL ))
                    NET_TX_RATE=$(( (tx_bytes - prev_tx) / INTERVAL ))
                    PREV_NET_RX[$iface]=$rx_bytes
                    PREV_NET_TX[$iface]=$tx_bytes
                fi
            fi
        fi
    done < /proc/net/dev
}

# ── Data: read disk ──────────────────────────────────────────
read_disk() {
    DISK_INFO=()
    while IFS= read -r line; do
        local fs size used avail pct mount
        read -r fs size used avail pct mount <<< "$line"
        # Skip headers and virtual filesystems
        [[ "$fs" == "Filesystem" ]] && continue
        [[ "$fs" == tmpfs ]] && continue
        [[ "$fs" == devtmpfs ]] && continue
        [[ "$fs" == overlay ]] && continue
        [[ "$fs" == none ]] && continue
        [[ "$mount" == /boot* ]] && continue
        [[ "$mount" == /snap* ]] && continue
        [[ "$mount" == /dev/shm ]] && continue
        [[ "$mount" == /run* ]] && continue
        [[ "$mount" == /sys* ]] && continue
        pct="${pct//%/}"
        # Validate pct is a number
        [[ "$pct" =~ ^[0-9]+$ ]] || continue
        DISK_INFO+=("${mount}|${used}|${size}|${pct}")
    done < <(df -h --output=source,size,used,avail,pcent,target 2>/dev/null || df -h 2>/dev/null)
}

# ── Data: read top processes ─────────────────────────────────
read_top_procs() {
    TOP_CPU=()
    TOP_MEM=()

    while IFS= read -r line; do
        TOP_CPU+=("$line")
    done < <(ps aux --sort=-%cpu 2>/dev/null | head -6 | tail -5)

    while IFS= read -r line; do
        TOP_MEM+=("$line")
    done < <(ps aux --sort=-%mem 2>/dev/null | head -6 | tail -5)
}

# ── Data: system info ────────────────────────────────────────
read_sysinfo() {
    SYS_HOSTNAME=$(hostname 2>/dev/null || cat /proc/sys/kernel/hostname 2>/dev/null || echo "unknown")
    SYS_KERNEL=$(uname -r 2>/dev/null || echo "unknown")
    SYS_OS=$(. /etc/os-release 2>/dev/null && echo "$PRETTY_NAME" || uname -s 2>/dev/null || echo "Linux")
    SYS_UPTIME_SEC=$(awk '{printf "%d", $1}' /proc/uptime 2>/dev/null || echo 0)
    SYS_UPTIME=$(format_uptime "$SYS_UPTIME_SEC")
    SYS_LOAD=$(awk '{print $1, $2, $3}' /proc/loadavg 2>/dev/null || echo "- - -")
    SYS_TIME=$(date '+%Y-%m-%d  %H:%M:%S')
}

# ── Render: banner ───────────────────────────────────────────
render_banner() {
    printf "\n"
    printf "  ${P1}${BOLD}███╗  ██╗ █████╗ ███╗  ██╗  ██████╗ ██████╗  ██████╗ ████████╗${NC}\n"
    printf "  ${P2}${BOLD}████╗ ██║██╔══██╗████╗ ██║ ██╔═══██╗██╔══██╗██╔═══██╗╚══██╔══╝${NC}\n"
    printf "  ${P3}${BOLD}██╔████╔╝███████║██╔████╔╝ ██║   ██║██████╔╝██║   ██║   ██║   ${NC}\n"
    printf "  ${P4}${BOLD}██║╚██╔╝ ██╔══██║██║╚██╔╝  ██║   ██║██╔══██╗██║   ██║   ██║   ${NC}\n"
    printf "  ${P5}${BOLD}██║ ╚═╝  ██║  ██║██║ ╚═╝   ╚██████╔╝██████╔╝╚██████╔╝   ██║   ${NC}\n"
    printf "  ${P6}${BOLD}╚═╝      ╚═╝  ╚═╝╚═╝        ╚═════╝ ╚═════╝  ╚═════╝   ╚═╝   ${NC}\n"
    printf "  ${P4}${BOLD}M O N I T O R${NC}\n"
    printf "\n"
}

# ── Render: system info ──────────────────────────────────────
render_sysinfo() {
    printf "  ${P3}%s${NC}\n" "$(printf '%.0s═' {1..60})"
    printf "  ${BW}%s${NC}  ${D}·${NC}  ${D}%s${NC}\n" "$SYS_HOSTNAME" "$SYS_OS"
    printf "  ${D}KERNEL${NC} ${C}%s${NC}    ${D}UPTIME${NC} ${G}%s${NC}    ${D}LOAD${NC} ${Y}%s${NC}\n" "$SYS_KERNEL" "$SYS_UPTIME" "$SYS_LOAD"
    printf "  ${D}%s${NC}\n" "$SYS_TIME"
    printf "  ${P3}%s${NC}\n" "$(printf '%.0s═' {1..60})"
    printf "\n"
}

# ── Render: CPU ──────────────────────────────────────────────
render_cpu() {
    section "CPU" "${CPU_CORES} cores"
    local total_pct=${CPU_PCT[cpu]:-0}
    printf "  ${BOLD}TOTAL${NC}  ["
    draw_bar "$total_pct" "$BAR_WIDTH"
    printf "]  ${BOLD}%3d%%${NC}\n" "$total_pct"

    local i=0
    while (( i < CPU_CORES )); do
        local key="cpu${i}"
        local pct=${CPU_PCT[$key]:-0}
        printf "  ${D}%-6s${NC} [" "cpu${i}"
        draw_bar "$pct" "$BAR_WIDTH"
        printf "]  %3d%%\n" "$pct"
        (( i++ ))
    done
    printf "\n"
}

# ── Render: memory ───────────────────────────────────────────
render_memory() {
    section "MEMORY"

    local mem_used_h mem_total_h swap_used_h swap_total_h
    mem_used_h=$(echo "$MEM_USED" | awk '{printf "%.1f", $1/1048576}')
    mem_total_h=$(echo "$MEM_TOTAL" | awk '{printf "%.1f", $1/1048576}')

    printf "  ${BOLD}RAM ${NC}   ["
    draw_bar "$MEM_PCT" "$BAR_WIDTH"
    printf "]  ${BOLD}%3d%%${NC}  ${D}%sG / %sG${NC}\n" "$MEM_PCT" "$mem_used_h" "$mem_total_h"

    if (( SWAP_TOTAL > 0 )); then
        swap_used_h=$(echo "$SWAP_USED" | awk '{printf "%.1f", $1/1048576}')
        swap_total_h=$(echo "$SWAP_TOTAL" | awk '{printf "%.1f", $1/1048576}')
        printf "  ${BOLD}SWAP${NC}   ["
        draw_bar "$SWAP_PCT" "$BAR_WIDTH"
        printf "]  ${BOLD}%3d%%${NC}  ${D}%sG / %sG${NC}\n" "$SWAP_PCT" "$swap_used_h" "$swap_total_h"
    else
        printf "  ${D}SWAP    N/A${NC}\n"
    fi
    printf "\n"
}

# ── Render: disk ─────────────────────────────────────────────
render_disk() {
    section "DISK"
    local entry
    for entry in "${DISK_INFO[@]}"; do
        IFS='|' read -r mount used size pct <<< "$entry"
        printf "  ${BOLD}%-7s${NC}["
        draw_bar "$pct" "$BAR_WIDTH"
        printf "]  ${BOLD}%3d%%${NC}  ${D}%s / %s${NC}\n" "$mount" "$pct" "$used" "$size"
    done
    printf "\n"
}

# ── Render: network ──────────────────────────────────────────
render_network() {
    section "NETWORK" "${NET_IFACE:-N/A}"
    if [[ -n "$NET_IFACE" ]]; then
        local rx_h tx_h
        rx_h=$(human_rate "$NET_RX_RATE")
        tx_h=$(human_rate "$NET_TX_RATE")
        printf "  ${G}▼${NC} Download  ${BOLD}%-14s${NC}  ${R}▲${NC} Upload  ${BOLD}%s${NC}\n" "$rx_h" "$tx_h"
    else
        printf "  ${D}No active network interface found${NC}\n"
    fi
    printf "\n"
}

# ── Render: top processes ────────────────────────────────────
render_procs() {
    section "TOP PROCESSES" "by CPU"
    printf "  ${D}%-8s %6s %6s  %-40s${NC}\n" "PID" "CPU%" "MEM%" "COMMAND"
    local line
    for line in "${TOP_CPU[@]}"; do
        local user pid cpu mem vsz rss tty stat start time cmd
        read -r user pid cpu mem vsz rss tty stat start time cmd <<< "$line"
        # Truncate command
        cmd="${cmd:0:40}"
        printf "  %-8s ${Y}%5s${NC} %5s  %s\n" "$pid" "$cpu" "$mem" "$cmd"
    done
    printf "\n"

    section "           " "by MEM"
    printf "  ${D}%-8s %6s %6s  %-40s${NC}\n" "PID" "CPU%" "MEM%" "COMMAND"
    for line in "${TOP_MEM[@]}"; do
        local user pid cpu mem vsz rss tty stat start time cmd
        read -r user pid cpu mem vsz rss tty stat start time cmd <<< "$line"
        cmd="${cmd:0:40}"
        printf "  %-8s %5s ${C}%5s${NC}  %s\n" "$pid" "$cpu" "$mem" "$cmd"
    done
    printf "\n"
}

# ── Render: footer ───────────────────────────────────────────
render_footer() {
    _hr 60
    printf "  ${D}Press ${BW}q${NC}${D} to quit  ·  Refresh: ${BW}%ds${NC}\n" "$INTERVAL"
}

# ── Main loop ────────────────────────────────────────────────
declare -A CPU_PCT

cleanup() {
    tput cnorm 2>/dev/null   # show cursor
    tput sgr0 2>/dev/null    # reset attributes
    stty echo 2>/dev/null    # restore echo
    printf "\n${G}Monitor stopped.${NC}\n"
    exit 0
}

trap cleanup EXIT INT TERM

# Hide cursor, disable echo for key detection
tput civis 2>/dev/null
stty -echo 2>/dev/null

tput clear

while true; do
    # Collect data
    read_sysinfo
    read_cpu
    read_memory
    read_disk
    read_network
    read_top_procs

    # Move cursor to top (no flicker)
    tput cup 0 0

    # Render
    render_banner
    render_sysinfo
    render_cpu
    render_memory
    render_disk
    render_network
    render_procs
    render_footer

    # Clear remaining lines from previous render
    tput el
    tput el

    FIRST_RUN=false

    # Wait for interval, check for 'q' key
    local_i=0
    while (( local_i < INTERVAL * 10 )); do
        if read -rsn1 -t 0.1 key 2>/dev/null; then
            [[ "$key" == "q" || "$key" == "Q" ]] && exit 0
        fi
        (( local_i++ ))
    done
done
