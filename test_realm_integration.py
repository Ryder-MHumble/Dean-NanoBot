#!/usr/bin/env python3
"""
Test script for Realm integration

This script tests the complete flow:
1. nanobot receives a Realm request
2. Realm skill dispatches to Realm API
3. Realm executes the task
4. Realm calls back to nanobot
5. nanobot forwards the result to the user
"""

import asyncio
import httpx
from nanobot.callback_server import CallbackServer
from nanobot.bus.queue import MessageBus
from nanobot.bus.events import OutboundMessage


async def test_callback_endpoint():
    """Test the callback endpoint directly."""
    print("=" * 60)
    print("Testing Callback Endpoint")
    print("=" * 60)

    # Setup
    bus = MessageBus()
    server = CallbackServer(bus)

    # Register a test task
    task_group_id = "test-task-123"
    server.register_task(task_group_id, "feishu", "test_user_456")

    # Start server
    await server.start()
    print("✓ Callback server started on http://0.0.0.0:18790")

    # Wait a bit for server to be ready
    await asyncio.sleep(1)

    # Test health endpoint
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:18790/health")
            print(f"✓ Health check: {response.json()}")
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        await server.stop()
        return

    # Simulate a callback from Realm
    callback_data = {
        "taskGroupId": task_group_id,
        "originalMessage": "分析 Athena 项目的整体架构",
        "results": [
            {
                "sessionId": "session-1",
                "sessionName": "Athena",
                "response": "Athena 项目是一个基于 TypeScript 的 Web 应用...",
                "status": "completed",
                "duration": 5000
            }
        ],
        "durationMs": 5500,
        "timestamp": 1234567890
    }

    print("\nSending test callback...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:18790/callback",
                json=callback_data,
                timeout=10.0
            )
            print(f"✓ Callback response: {response.json()}")
    except Exception as e:
        print(f"✗ Callback failed: {e}")

    # Check if message was published to bus
    print("\nChecking message bus...")
    try:
        msg = await asyncio.wait_for(bus.consume_outbound(), timeout=2.0)
        print(f"✓ Message received from bus:")
        print(f"  Channel: {msg.channel}")
        print(f"  Chat ID: {msg.chat_id}")
        print(f"  Content preview: {msg.content[:100]}...")
    except asyncio.TimeoutError:
        print("✗ No message received from bus")

    # Stop server
    await server.stop()
    print("\n✓ Test completed!")


async def test_realm_api_connection():
    """Test connection to Realm API."""
    print("\n" + "=" * 60)
    print("Testing Realm API Connection")
    print("=" * 60)

    realm_url = "http://localhost:4003"

    try:
        async with httpx.AsyncClient() as client:
            # Test /sessions endpoint
            response = await client.get(f"{realm_url}/sessions", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                sessions = data.get("sessions", [])
                print(f"✓ Realm API is running")
                print(f"  Found {len(sessions)} sessions:")
                for session in sessions[:3]:
                    print(f"    - {session['name']} ({session['id'][:8]}...)")
            else:
                print(f"✗ Realm API returned status {response.status_code}")
    except httpx.ConnectError:
        print(f"✗ Cannot connect to Realm API at {realm_url}")
        print("  Make sure Realm server is running: cd ~/Desktop/My\\ Projects/Realm && npm run server")
    except Exception as e:
        print(f"✗ Error connecting to Realm API: {e}")


async def main():
    """Run all tests."""
    print("\n🧪 Realm Integration Test Suite\n")

    # Test 1: Realm API connection
    await test_realm_api_connection()

    # Test 2: Callback endpoint
    await test_callback_endpoint()

    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
