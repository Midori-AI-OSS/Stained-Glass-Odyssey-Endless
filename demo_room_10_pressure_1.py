#!/usr/bin/env python3
"""
Demonstration script showing that Room 10 is reachable with Pressure 1 enabled.

This script demonstrates the core functionality by:
1. Starting a run with pressure=1
2. Showing that room 10 exists in the map
3. Validating all rooms have pressure=1 applied
"""

import asyncio
import json
import sys
from pathlib import Path

# Add backend path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from services.run_service import start_run
from services.run_service import get_map


async def demonstrate_room_10_pressure_1():
    """Demonstrate that room 10 is reachable with pressure=1."""
    print("🎮 Midori AI AutoFighter - Room 10 Pressure 1 Demonstration")
    print("=" * 60)
    
    try:
        # Start a run with pressure=1
        print("📍 Starting new run with pressure=1...")
        result = await start_run(["player"], pressure=1)
        run_id = result["run_id"]
        map_data = result["map"]
        
        print(f"✅ Run started successfully! Run ID: {run_id}")
        print(f"📊 Map generated with {len(map_data['rooms'])} rooms")
        print(f"🎯 Current room index: {map_data['current']}")
        
        # Check room 10 specifically (0-based index 9)
        room_10_index = 9
        room_10 = map_data["rooms"][room_10_index]
        
        print("\n🏠 Room 10 Details:")
        print(f"   Index: {room_10['index']} (Room {room_10['index'] + 1} in 1-based numbering)")
        print(f"   Pressure: {room_10['pressure']}")
        print(f"   Floor: {room_10['floor']}")
        print(f"   Loop: {room_10['loop']}")
        print(f"   Room Type: {room_10['room_type']}")
        print(f"   Room ID: {room_10['room_id']}")
        
        # Validate all rooms have pressure=1
        print("\n🔍 Validating pressure across all rooms...")
        pressure_mismatches = []
        for i, room in enumerate(map_data["rooms"]):
            if room["pressure"] != 1:
                pressure_mismatches.append(f"Room {i}: pressure={room['pressure']}")
        
        if pressure_mismatches:
            print(f"❌ Found {len(pressure_mismatches)} rooms with incorrect pressure:")
            for mismatch in pressure_mismatches:
                print(f"   {mismatch}")
        else:
            print(f"✅ All {len(map_data['rooms'])} rooms correctly have pressure=1")
        
        # Show room type distribution
        print("\n📈 Room Type Distribution:")
        room_types = {}
        for room in map_data["rooms"]:
            rt = room["room_type"]
            room_types[rt] = room_types.get(rt, 0) + 1
        
        for room_type, count in sorted(room_types.items()):
            print(f"   {room_type}: {count}")
        
        # Verify map structure
        print("\n🏗️  Map Structure Validation:")
        start_room = map_data["rooms"][0]
        boss_room = map_data["rooms"][-1]
        
        print(f"   Start room (index 0): {start_room['room_type']} ✅" if start_room["room_type"] == "start" else f"   Start room (index 0): {start_room['room_type']} ❌")
        print(f"   Boss room (index {len(map_data['rooms'])-1}): {boss_room['room_type']} ✅" if boss_room["room_type"] == "battle-boss-floor" else f"   Boss room (index {len(map_data['rooms'])-1}): {boss_room['room_type']} ❌")
        
        # Final validation
        print("\n🎯 Final Validation:")
        room_10_reachable = (
            room_10_index < len(map_data["rooms"]) and
            room_10["pressure"] == 1 and
            room_10["room_type"] in {"battle-weak", "battle-normal", "shop", "rest"}
        )
        
        if room_10_reachable:
            print("✅ CONFIRMED: Room 10 is reachable with Pressure 1 enabled!")
            print(f"   Room 10 is accessible as a {room_10['room_type']} room")
            print(f"   Pressure scaling is correctly applied (pressure={room_10['pressure']})")
        else:
            print("❌ ISSUE: Room 10 may not be properly reachable")
            
        return room_10_reachable
        
    except Exception as e:
        print(f"❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Run the demonstration
    success = asyncio.run(demonstrate_room_10_pressure_1())
    if success:
        print("\n🎉 Demonstration completed successfully!")
        exit(0)
    else:
        print("\n💥 Demonstration failed!")
        exit(1)