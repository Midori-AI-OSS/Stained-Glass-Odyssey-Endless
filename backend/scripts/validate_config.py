"""Validate config.toml file for Midori AI Agent Framework.

This script validates the structure and contents of a config.toml file
to ensure it contains valid configuration for the agent framework.

Usage:
    uv run python scripts/validate_config.py [config_path]

Examples:
    uv run python scripts/validate_config.py
    uv run python scripts/validate_config.py config.toml
    uv run python scripts/validate_config.py ../config.toml
"""

from pathlib import Path
import sys

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def validate_config(config_path: str = "config.toml") -> bool:
    """Validate a config file.

    Args:
        config_path: Path to config file

    Returns:
        True if valid, False otherwise
    """
    try:
        # Try importing the agent framework
        from midori_ai_agent_base import load_agent_config

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
    except ImportError:
        print(
            "✗ Midori AI Agent Framework not installed. "
            "Install with: uv sync --extra llm-cpu"
        )
        return False
    except FileNotFoundError:
        print(f"✗ Config file not found: {config_path}")
        print(
            f"  Create one by copying: cp {Path(config_path).stem}.example {config_path}"
        )
        return False
    except Exception as e:
        print(f"✗ Config validation failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.toml"
    success = validate_config(config_path)
    sys.exit(0 if success else 1)
