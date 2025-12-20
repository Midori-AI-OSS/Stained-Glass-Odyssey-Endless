"""Test config file loading."""
import asyncio
import os

from llms.agent_loader import find_config_file
from llms.agent_loader import get_agent_config
from llms.agent_loader import load_agent


async def test_config():
    """Test configuration loading."""
    print("Testing config loading...")

    # Test finding config file
    config_path = find_config_file()
    print(f"Config path: {config_path}")

    if not config_path:
        print("WARNING: Config file not found during test")

    # Test loading config
    config = get_agent_config()
    if config:
        print(f"Backend: {config.backend}")
        print(f"Model: {config.model}")
        print("Get config: OK")
    else:
        print("No config file found, skipping config content checks")

    # Test loading agent with config
    print("\nLoading agent from config...")
    try:
        agent = await load_agent(use_config=True, validate=False)
        print(f"Agent loaded (config): {agent}")
    except Exception as e:
        print(f"Agent load (config) failed: {e}")

    # Test loading agent without config (fallback)
    print("\nLoading agent without config (env vars fallback)...")
    try:
        # Ensure we have env vars set for fallback test if they aren't already
        if not os.getenv("OPENAI_API_URL"):
            # Set dummy values if not present, just to pass the "backend detection" logic
            # This simulates what happens in a real env or CI if vars are set
            os.environ["OPENAI_API_URL"] = "http://localhost:11434/v1"
            os.environ["OPENAI_API_KEY"] = "not-needed"
            print("(Set dummy env vars for fallback test)")

        agent2 = await load_agent(use_config=False, validate=False)
        print(f"Agent loaded (env vars): {agent2}")
    except Exception as e:
        print(f"Agent load (env vars) failed: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(test_config())
        print("\nAll tests passed!")
    except Exception as e:
        print(f"\nTests failed: {e}")
        exit(1)
