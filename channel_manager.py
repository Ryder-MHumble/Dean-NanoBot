#!/usr/bin/env python3
"""
Channel Manager - Interactive tool for managing enabled chat channels.
Allows users to enable/disable channels and configure credentials.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any

# ANSI colors
R = '\033[0;31m'
G = '\033[0;32m'
Y = '\033[0;33m'
B = '\033[0;34m'
C = '\033[0;36m'
D = '\033[0;90m'
NC = '\033[0m'
BOLD = '\033[1m'


def load_config() -> dict[str, Any]:
    """Load config.json from ~/.nanobot/"""
    config_path = Path.home() / ".nanobot" / "config.json"
    if not config_path.exists():
        print(f"{R}✗{NC} Config not found at {config_path}")
        print(f"  Run: ./deploy.sh init")
        sys.exit(1)

    with open(config_path) as f:
        return json.load(f)


def save_config(config: dict[str, Any]) -> None:
    """Save config.json to ~/.nanobot/"""
    config_path = Path.home() / ".nanobot" / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"{G}✓{NC} Config saved")


def load_env() -> dict[str, str]:
    """Load .env file from project root."""
    env_path = Path.cwd() / ".env"
    env = {}
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    env[key.strip()] = val.strip()
    return env


def save_env(env: dict[str, str]) -> None:
    """Save .env file."""
    env_path = Path.cwd() / ".env"
    with open(env_path, 'w') as f:
        for key, val in sorted(env.items()):
            f.write(f"{key}={val}\n")
    print(f"{G}✓{NC} .env updated")


def show_channels_status(config: dict[str, Any]) -> None:
    """Display current channel status."""
    print(f"\n{BOLD}Current Channel Status{NC}\n")

    channels_config = config.get("channels", {})
    channels = [
        ("dingtalk", "🔔 DingTalk", ["clientId"]),
        ("feishu", "🪐 Feishu", ["appId"]),
        ("telegram", "✈️  Telegram", ["token"]),
        ("slack", "💬 Slack", ["botToken"]),
        ("discord", "🎮 Discord", ["token"]),
        ("qq", "🐧 QQ", ["appId"]),
    ]

    for key, label, id_fields in channels:
        ch = channels_config.get(key, {})
        enabled = ch.get("enabled", False)

        if enabled:
            cid = next((ch.get(f, "") for f in id_fields if ch.get(f)), "")
            masked = (cid[:8] + "...") if len(cid) > 8 else cid
            print(f"  {G}●{NC} {label:<18} {masked}")
        else:
            print(f"  {D}○{NC} {D}{label}{NC}")


def prompt_channel_config(channel_name: str, env: dict[str, str]) -> dict[str, str]:
    """Prompt user to configure a channel."""
    print(f"\n{BOLD}Configure {channel_name.upper()}{NC}\n")

    if channel_name == "dingtalk":
        print("Get credentials from: https://open.dingtalk.com/")
        client_id = input(f"  {C}AppKey{NC} (or press Enter to skip): ").strip()
        client_secret = input(f"  {C}AppSecret{NC} (or press Enter to skip): ").strip()

        if client_id and client_secret:
            env["NANOBOT_CHANNELS__DINGTALK__ENABLED"] = "true"
            env["NANOBOT_CHANNELS__DINGTALK__CLIENT_ID"] = client_id
            env["NANOBOT_CHANNELS__DINGTALK__CLIENT_SECRET"] = client_secret
            return env

    elif channel_name == "feishu":
        print("Get credentials from: https://open.feishu.cn/")
        app_id = input(f"  {C}App ID{NC} (or press Enter to skip): ").strip()
        app_secret = input(f"  {C}App Secret{NC} (or press Enter to skip): ").strip()

        if app_id and app_secret:
            env["NANOBOT_CHANNELS__FEISHU__ENABLED"] = "true"
            env["NANOBOT_CHANNELS__FEISHU__APP_ID"] = app_id
            env["NANOBOT_CHANNELS__FEISHU__APP_SECRET"] = app_secret
            return env

    elif channel_name == "telegram":
        print("Get token from: https://t.me/BotFather")
        token = input(f"  {C}Bot Token{NC} (or press Enter to skip): ").strip()

        if token:
            env["NANOBOT_CHANNELS__TELEGRAM__ENABLED"] = "true"
            env["NANOBOT_CHANNELS__TELEGRAM__TOKEN"] = token
            return env

    return env


def cmd_list(config: dict[str, Any]) -> None:
    """List all available channels."""
    show_channels_status(config)
    print()


def cmd_enable(config: dict[str, Any], env: dict[str, str], channel: str) -> None:
    """Enable a channel."""
    channels_config = config.get("channels", {})

    if channel not in channels_config:
        print(f"{R}✗{NC} Unknown channel: {channel}")
        print(f"  Available: dingtalk, feishu, telegram, slack, discord, qq")
        return

    # Prompt for credentials
    env = prompt_channel_config(channel, env)

    if env.get(f"NANOBOT_CHANNELS__{channel.upper()}__ENABLED") == "true":
        save_env(env)
        print(f"{G}✓{NC} {channel} enabled and configured")
    else:
        print(f"{Y}!{NC} {channel} configuration skipped")


def cmd_disable(config: dict[str, Any], env: dict[str, str], channel: str) -> None:
    """Disable a channel."""
    env[f"NANOBOT_CHANNELS__{channel.upper()}__ENABLED"] = "false"
    save_env(env)
    print(f"{G}✓{NC} {channel} disabled")


def cmd_interactive(config: dict[str, Any], env: dict[str, str]) -> None:
    """Interactive channel configuration."""
    while True:
        print(f"\n{BOLD}Channel Manager{NC}\n")
        show_channels_status(config)

        print(f"\n{BOLD}Options{NC}\n")
        print("  1. Enable DingTalk")
        print("  2. Enable Feishu")
        print("  3. Enable Telegram")
        print("  4. Disable a channel")
        print("  5. Exit")

        choice = input(f"\n{C}Select option (1-5){NC}: ").strip()

        if choice == "1":
            env = prompt_channel_config("dingtalk", env)
            if env.get("NANOBOT_CHANNELS__DINGTALK__ENABLED") == "true":
                save_env(env)
                config = load_config()
        elif choice == "2":
            env = prompt_channel_config("feishu", env)
            if env.get("NANOBOT_CHANNELS__FEISHU__ENABLED") == "true":
                save_env(env)
                config = load_config()
        elif choice == "3":
            env = prompt_channel_config("telegram", env)
            if env.get("NANOBOT_CHANNELS__TELEGRAM__ENABLED") == "true":
                save_env(env)
                config = load_config()
        elif choice == "4":
            print("\nDisable which channel?")
            print("  1. DingTalk")
            print("  2. Feishu")
            print("  3. Telegram")
            ch_choice = input(f"\n{C}Select (1-3){NC}: ").strip()

            ch_map = {"1": "dingtalk", "2": "feishu", "3": "telegram"}
            if ch_choice in ch_map:
                cmd_disable(config, env, ch_map[ch_choice])
                config = load_config()
        elif choice == "5":
            print(f"\n{G}Goodbye!{NC}\n")
            break
        else:
            print(f"{Y}!{NC} Invalid option")


def main() -> None:
    """Main entry point."""
    config = load_config()
    env = load_env()

    if len(sys.argv) < 2:
        cmd_interactive(config, env)
    else:
        cmd = sys.argv[1]

        if cmd == "list":
            cmd_list(config)
        elif cmd == "enable" and len(sys.argv) > 2:
            cmd_enable(config, env, sys.argv[2])
        elif cmd == "disable" and len(sys.argv) > 2:
            cmd_disable(config, env, sys.argv[2])
        else:
            print(f"Usage: {sys.argv[0]} [list|enable|disable] [channel]")
            print(f"       {sys.argv[0]}  (interactive mode)")


if __name__ == "__main__":
    main()
