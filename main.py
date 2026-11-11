import sys
import os
from PyQt6.QtWidgets import QApplication
from ui.main_window import AudioLabWindow

def main():
    app = QApplication(sys.argv)
    window = AudioLabWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
