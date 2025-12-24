
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from idle_game.core.game_state import GameState
from idle_game.gui.mainwindow import MainWindow
from PySide6.QtWidgets import QApplication


def main():
    app = QApplication(sys.argv)

    # Initialize Game Logic
    game_state = GameState()
    game_state.load_characters()
    game_state.load_game_state()

    # Initialize Main Window
    window = MainWindow(game_state)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
