from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))

from idle_game.core.game_state import GameState
from idle_game.gui.character_window import CharacterWindow
from PySide6.QtWidgets import QApplication


def test_rebirth():
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    print("Initializing GameState...")
    state = GameState()
    state.load_characters()

    char_id = "carly"
    char = state.characters_map[char_id]
    runtime = char["runtime"]

    # Reset for clean test
    runtime["exp_multiplier"] = 1.0
    runtime["req_multiplier"] = 1.0
    state.mods["shared_exp"] = False

    # 1. Test Default Growth
    print("\n--- Testing Default Growth ---")
    runtime["level"] = 1
    runtime["exp"] = 0
    state.start_viewing(char_id)
    state._on_tick()  # Gain 1.0 EXP
    if runtime["exp"] == 1.0:
        print("PASS: Gained 1.0 EXP (Default).")
    else:
        print(f"FAIL: Gained {runtime['exp']} EXP.")

    # 2. Test Max Level Rebirth Eligibility
    print("\n--- Testing Rebirth Eligibility ---")
    runtime["level"] = 49
    if state.rebirth_character(char_id):
        print("FAIL: Allowed rebirth at level 49.")
    else:
        print("PASS: Prevented rebirth at level 49.")

    runtime["level"] = 50

    # 3. Test Rebirth Mechanics
    print("\n--- Testing Rebirth Execution ---")
    if state.rebirth_character(char_id):
        print("PASS: Rebirth successful at level 50.")
    else:
        print("FAIL: Rebirth failed at level 50.")

    # Check Reset
    if runtime["level"] == 1 and runtime["exp"] == 0:
        print("PASS: Level reset to 1.")
    else:
        print(f"FAIL: Level not reset. Lvl: {runtime['level']}")

    # Check Multipliers
    exp_mult = runtime.get("exp_multiplier", 1.0)
    req_mult = runtime.get("req_multiplier", 1.0)

    if exp_mult == 1.25:  # 1.0 + 0.25
        print(f"PASS: Exp Multiplier is {exp_mult}")
    else:
        print(f"FAIL: Exp Multiplier is {exp_mult} (Expected 1.25)")

    if req_mult == 1.05:  # 1.0 + 0.05
        print(f"PASS: Req Multiplier is {req_mult}")
    else:
        print(f"FAIL: Req Multiplier is {req_mult} (Expected 1.05)")

    # 4. Test Multiplier Effect
    print("\n--- Testing Multiplier Effect ---")
    runtime["exp"] = 0
    state.start_viewing(char_id)
    state._on_tick()  # Should gain 1.25 EXP
    if runtime["exp"] == 1.25:
        print("PASS: Gained 1.25 EXP.")
    else:
        print(f"FAIL: Gained {runtime['exp']} EXP.")

    # Level 1 req should be 30 * 1.05 = 31.5
    req = (runtime["level"] * 30) * req_mult
    if abs(req - 31.5) < 0.01:
        print("PASS: Exp Req is 31.5.")
    else:
        print(f"FAIL: Exp Req is {req}.")

    print("\n--- Testing UI Integration ---")
    # Mock window
    window = CharacterWindow(char, state)

    # Should be hidden (Lvl 1)
    window.update_stats(0)
    if window.rebirth_btn.isHidden():
        print("PASS: Rebirth button hidden at Level 1.")
    else:
        print("FAIL: Rebirth button visible at Level 1.")

    # Level up to 50 manually
    runtime["level"] = 50
    window.update_stats(0)
    if not window.rebirth_btn.isHidden():
        print("PASS: Rebirth button visible at Level 50.")
    else:
        print("FAIL: Rebirth button hidden at Level 50.")


if __name__ == "__main__":
    test_rebirth()
