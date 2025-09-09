#!/usr/bin/env python3
"""
Player Editor Backend Test Script

This script tests the player editor backend endpoints directly using HTTP requests.
Use this to verify the backend is working correctly independent of the frontend.

Usage:
    python3 test_player_editor_backend.py [backend_url]

Example:
    python3 test_player_editor_backend.py http://localhost:8000
"""

import json
import sys
from typing import Any
from typing import Dict
import urllib.error
import urllib.parse
import urllib.request


def make_request(
    url: str,
    method: str = "GET",
    data: Dict[str, Any] | None = None,
    headers: Dict[str, str] | None = None,
) -> tuple[int, Dict[str, Any] | str]:
    """Make an HTTP request and return status code and response data."""
    if headers is None:
        headers = {}

    if data is not None:
        data_bytes = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
        headers["Content-Length"] = str(len(data_bytes))
    else:
        data_bytes = None

    req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            response_data = response.read().decode("utf-8")
            try:
                return response.status, json.loads(response_data)
            except json.JSONDecodeError:
                return response.status, response_data
    except urllib.error.HTTPError as e:
        try:
            error_data = e.read().decode("utf-8")
            return e.status, json.loads(error_data)
        except json.JSONDecodeError:
            return e.status, error_data
    except Exception as e:
        return 0, str(e)


def test_player_editor_endpoints(base_url: str):
    """Test the player editor endpoints."""
    print(f"Testing player editor endpoints at: {base_url}")
    print("=" * 60)

    # Test 1: Get current player editor settings
    print("\n1. Getting current player editor settings...")
    status, data = make_request(f"{base_url}/player/editor")
    print(f"   GET /player/editor -> Status: {status}")
    if status == 200:
        print(f"   Current settings: {data}")
    else:
        print(f"   Error: {data}")
        return False

    # Test 2: Update player editor settings
    print("\n2. Updating player editor settings...")
    test_settings = {
        "pronouns": "they",
        "damage_type": "Fire",
        "hp": 50,
        "attack": 20,
        "defense": 20,
        "crit_rate": 5,
        "crit_damage": 5,
    }
    status, data = make_request(f"{base_url}/player/editor", "PUT", test_settings)
    print(f"   PUT /player/editor -> Status: {status}")
    print(f"   Settings sent: {test_settings}")
    if status == 200:
        print(f"   Response: {data}")
    else:
        print(f"   Error: {data}")
        return False

    # Test 3: Verify settings were saved
    print("\n3. Verifying settings were saved...")
    status, data = make_request(f"{base_url}/player/editor")
    print(f"   GET /player/editor -> Status: {status}")
    if status == 200:
        print(f"   Saved settings: {data}")
        # Check if the settings match what we sent
        for key in ["hp", "attack", "defense", "crit_rate", "crit_damage"]:
            if data.get(key) != test_settings[key]:
                print(
                    f"   WARNING: {key} mismatch! Expected {test_settings[key]}, got {data.get(key)}"
                )
    else:
        print(f"   Error: {data}")
        return False

    # Test 4: Get player stats (should show customized values)
    print("\n4. Getting player stats (should show customized values)...")
    status, data = make_request(f"{base_url}/player/stats")
    print(f"   GET /player/stats -> Status: {status}")
    if status == 200:
        core = data.get("stats", {}).get("core", {})
        offense = data.get("stats", {}).get("offense", {})
        defense_stats = data.get("stats", {}).get("defense", {})

        print(f"   Core stats: HP={core.get('hp')}, Max HP={core.get('max_hp')}")
        print(
            f"   Offense stats: ATK={offense.get('atk')}, CRIT Rate={offense.get('crit_rate')}, CRIT DMG={offense.get('crit_damage')}"
        )
        print(f"   Defense stats: DEF={defense_stats.get('defense')}")

        # Calculate expected values
        expected_max_hp = int(1000 * 1.5)  # 50% boost
        expected_atk = int(100 * 1.2)  # 20% boost
        expected_def = int(50 * 1.2)  # 20% boost
        expected_cr = 0.05 * 1.05
        expected_cd = 2.0 * 1.05

        print("\n   Expected values:")
        print(f"   Max HP: {expected_max_hp} (got {core.get('max_hp')})")
        print(f"   ATK: {expected_atk} (got {offense.get('atk')})")
        print(f"   DEF: {expected_def} (got {defense_stats.get('defense')})")

        # Check if values match expectations
        if core.get("max_hp") == expected_max_hp:
            print("   ✓ Max HP is correct!")
        else:
            print("   ✗ Max HP mismatch - customization may not be applied")

        if offense.get("atk") == expected_atk:
            print("   ✓ ATK is correct!")
        else:
            print("   ✗ ATK mismatch - customization may not be applied")

        if defense_stats.get("defense") == expected_def:
            print("   ✓ DEF is correct!")
        else:
            print("   ✗ DEF mismatch - customization may not be applied")

        if abs(offense.get("crit_rate", 0) - expected_cr) < 1e-6:
            print("   ✓ CRIT Rate is correct!")
        else:
            print("   ✗ CRIT Rate mismatch")

        if abs(offense.get("crit_damage", 0) - expected_cd) < 1e-6:
            print("   ✓ CRIT DMG is correct!")
        else:
            print("   ✗ CRIT DMG mismatch")

    else:
        print(f"   Error: {data}")
        return False

    print("\n" + "=" * 60)
    print("Test completed! Check the results above.")
    return True


def main():
    if len(sys.argv) > 1:
        base_url = sys.argv[1].rstrip("/")
    else:
        base_url = "http://localhost:8000"

    print("Player Editor Backend Test Script")
    print("This script tests the backend player editor functionality directly.")
    print("Make sure the backend server is running before using this script.")
    print()

    try:
        test_player_editor_endpoints(base_url)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed with error: {e}")


if __name__ == "__main__":
    main()
