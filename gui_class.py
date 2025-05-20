from PySide6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QMainWindow, QPushButton, QHBoxLayout, QFormLayout, QGridLayout, QMenuBar, QMenu, QFileDialog
from PySide6.QtCore import Qt, Signal
import sys
import test_pandas
import conf_manager

def quit_():
    sys.exit()

def select_folder(target):
    print("folder")

class FolderSelector(QWidget):
    folderSelected = Signal(str)  # Signal émis avec le chemin sélectionné
    

    def __init__(self, label_text):
        super().__init__()
        self.label = QLabel(label_text)
        self.path_display = QLabel("(no folder selected)")
        self.path_display.setStyleSheet("color: white; font-size: 10px; background-color: grey; ")

        self.button = QPushButton("Browse")
        self.button.clicked.connect(self.select_folder)

        layout = QHBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.path_display)
        layout.addWidget(self.button)

        self.setLayout(layout)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.path_display.setText(folder)
            self.folderSelected.emit(folder)
    
    def reset_label(self):
        self.path_display.setText("(no folder selected)")


class AcceuilWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        self.title = QLabel("Main Page")
        self.title.setAlignment(Qt.AlignCenter)

        self.input_selector = FolderSelector("Input Folder:")
        self.output_selector = FolderSelector("Output Folder:")

        self.input_selector.folderSelected.connect(self.input_chosen)
        self.output_selector.folderSelected.connect(self.output_chosen)

        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_conf)

        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_process)

        layout.addWidget(self.title)
        layout.addWidget(self.input_selector)
        layout.addWidget(self.output_selector)
        layout.addWidget(self.reset_button, alignment=Qt.AlignCenter)
        layout.addWidget(self.start_button, alignment=Qt.AlignCenter)

        self.setLayout(layout)

    def input_chosen(self, path):
        print(f"[INFO] Input folder selected: {path}")
        conf_manager.set("input_folder", path)

    def output_chosen(self, path):
        print(f"[INFO] Output folder selected: {path}")
        conf_manager.set("output_folder", path)

    def start_process(self):
        print("Start button pressed")
        try:
            test_pandas.main()
        except Exception as e:
            sys.exit()
    
    def reset_conf(self):
        conf_manager.set_to_default()
        self.input_selector.reset_label()
        self.output_selector.reset_label()
        print("reset")

  
        
class MenuBar(QMenuBar):
    def __init__(self, parent):
        super().__init__(parent)
        
        nav_menu = self.addMenu("Nav")

        
class MainWindow(QMainWindow):
    def __init__ (self):
        super().__init__()
        self.setWindowTitle("CSV handler")
        mainwidget = AcceuilWidget()
        self.setCentralWidget(mainwidget)   
        
