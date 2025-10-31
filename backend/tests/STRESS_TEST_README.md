# Stress Test: 100 Room Battle

This stress test verifies the game engine can handle extended gameplay with:
- 5 party members (Player, Carly, Lady Echo, Lady Darkness, Lady Light)
- All relics and cards enabled
- Multiple foes per battle (determined by FoeFactory based on party size and pressure)
- 100 consecutive battles
- Relic stacking after each battle

## Purpose

The test validates:
- **Relics**: All relic plugins work correctly and can be stacked
- **Cards**: All card plugins can be added to the party
- **Async Operations**: No timeouts or deadlocks over 100 battles
- **Characters**: All party members function properly in combat
- **Passives**: Character abilities and passives trigger correctly

## Running the Test

### Option 1: Docker Compose with Separate File (Recommended)

```bash
# Run with dedicated compose file
docker compose -f compose.stress-test.yaml run stress-test
```

### Option 2: Direct Docker Command

```bash
# Build and run in backend container
docker compose run backend uv run pytest -v -m stress tests/test_stress_100_rooms.py
```

### Option 3: Local Environment

```bash
# From the backend directory
cd backend
uv run pytest -v -m stress tests/test_stress_100_rooms.py
```

## Docker Compose Configuration

The stress test uses a dedicated `compose.stress-test.yaml` file with the following configuration:
- `tty: true` - Enables interactive terminal for better output display
- `restart: "no"` - Prevents automatic restart on failure (test should run once)
- External network - Uses the existing `autofighter-network`

To run the test, ensure the main application network exists:
```bash
# Create network if it doesn't exist
docker network create autofighter-network

# Run stress test
docker compose -f compose.stress-test.yaml run stress-test
```

## Test Behavior

The test will:
1. Discover all available relic and card plugins
2. Create a party with 5 specific characters
3. Initialize the party with 1 of every relic and card
4. Run 100 battles sequentially:
   - Each battle generates foes using FoeFactory (count based on party size and pressure)
   - Floor difficulty increases with pressure and loop values
   - After each battle, a random relic is added (stacking)
5. Log progress every 10 floors
6. Report final statistics

## Expected Duration

The test typically takes **10-30 minutes** depending on:
- System performance
- Battle complexity with all relics/cards active
- Number of async operations per turn

## Skipping in Regular Tests

This test is marked with `@pytest.mark.stress` and will NOT run during:
- Regular test suite execution (`pytest`)
- CI/CD pipeline runs
- The `./run-tests.sh` script

It must be explicitly invoked using the `-m stress` marker.

## Interpreting Results

Success criteria:
- All 100 battles complete without timeout
- No catastrophic errors or crashes
- Async operations handle properly

The test does NOT require winning all battles - some losses are expected depending on foe count and difficulty. The key validation is that the system remains stable throughout extended play.

## Troubleshooting

If the test fails or hangs:
1. Check the logs for the specific floor where failure occurred
2. Verify all plugin dependencies are installed
3. Ensure sufficient system resources (CPU/memory)
4. Check for infinite loops in relic/passive interactions

## Modifying the Test

To adjust test parameters, edit `backend/tests/test_stress_100_rooms.py`:
- `range(1, 101)`: Change to test fewer/more battles
- `pressure=floor * 5`: Adjust pressure scaling
- Party members: Add/remove characters from the party
- FoeFactory config: Modify ROOM_BALANCE_CONFIG for different foe counts
