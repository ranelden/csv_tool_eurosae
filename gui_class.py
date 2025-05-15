from PySide6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QMainWindow, QPushButton, QHBoxLayout, QFormLayout
import sys
import test_pandas

class MainWindow(QMainWindow):
    def __init__ (self):
        super().__init__()
        self.setWindowTitle("CSV handler")
        mainwidget = MainWidget()
        self.setCentralWidget(mainwidget)

class MainWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QFormLayout()

        button_1 = QPushButton("start csv processing")
        button_1.clicked.connect(self.button_1_action)

        layout.addWidget(button_1)

        self.setLayout(layout)

    def button_1_action(self):
        print("csv processing")
        try :
            test_pandas.main()
        except Exception as e:
            print(e)
        sys.exit()
        
    