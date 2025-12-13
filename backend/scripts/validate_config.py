"""Validate config.toml file."""
import sys
from pathlib import Path

# Add backend directory to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from llms.agent_loader import load_agent_config


def validate_config(config_path: str = "config.toml") -> bool:
    """Validate a config file.

    Args:
        config_path: Path to config file

    Returns:
        True if valid, False otherwise
    """
    if load_agent_config is None:
        print("✗ Agent framework not installed. Cannot validate config.")
        print("  Install with: uv sync --extra llm-cpu")
        return False

    try:
        config = load_agent_config(config_path=config_path)

        print(f"✓ Config file is valid: {config_path}")
        print(f"  Backend: {config.backend}")
        print(f"  Model: {config.model}")
        print(f"  Base URL: {config.base_url or '(not set)'}")

        if config.reasoning_effort:
            print(f"  Reasoning Effort: {config.reasoning_effort.effort}")

        if config.extra:
            print(f"  Extra settings: {list(config.extra.keys())}")

        return True
    except FileNotFoundError:
        print(f"✗ Config file not found: {config_path}")
        return False
    except Exception as e:
        print(f"✗ Config validation failed: {e}")
        return False


if __name__ == "__main__":
    import sys

    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.toml"
    success = validate_config(config_path)
    sys.exit(0 if success else 1)
