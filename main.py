import sys
from PyQt6.QtWidgets import QApplication
from ui.printer_manager_app import PrinterManagerApp

def main():
    app = QApplication(sys.argv)
    window = PrinterManagerApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()