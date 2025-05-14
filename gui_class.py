from PySide6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QMainWindow, QPushButton 
import sys

class MainWindow(QMainWindow):
    def __init__ (self):
        super().__init__()
        self.setWindowTitle("CSV handler")
        button = QPushButton("press me")
        self.setCentralWidget(button)

class MainWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.
    