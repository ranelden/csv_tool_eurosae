from PySide6.QtWidgets import QApplication, QLineEdit, QLabel, QWidget, QVBoxLayout, QMainWindow, QPushButton, QHBoxLayout, QFormLayout, QGridLayout, QMenuBar, QMenu, QFileDialog, QTabWidget
from PySide6.QtCore import Qt, Signal
import sys
import test_pandas
import conf_manager
import ban_list_manager
import mail_manager

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

class FileSelector(QWidget):
    fileSelected = Signal(str)  # Signal émis avec le chemin sélectionné

    def __init__(self, label_text):
        super().__init__()
        self.label = QLabel(label_text)
        self.path_display = QLabel("  (no file selected)")
        self.path_display.setStyleSheet("color: white; font-size: 10px; background-color: grey; ")

        self.button = QPushButton("Browse")
        self.button.clicked.connect(self.select_file)

        layout = QHBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.path_display)
        layout.addWidget(self.button)

        self.setLayout(layout)

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if file_path:
            file = file_path.split("/")
            self.path_display.setText("  " + file[-1])
            
            self.fileSelected.emit(file_path)
    
    def reset_label(self):
        self.path_display.setText("(no file selected)")

class TextSaver(QWidget):
    lign_added = Signal(str)  # Signal émis avec le chemin sélectionné
    

    def __init__(self, label_text):
        super().__init__()
        self.label = QLabel(label_text)
        self.entreprise_field = QLineEdit()
        self.entreprise_field.setStyleSheet("color: white; font-size: 10px; background-color: grey; ")

        self.button_add = QPushButton("ADD")
        self.button_add.clicked.connect(self.save_ban)

        self.button_reset = QPushButton("reset")
        self.button_reset.clicked.connect(self.reset_text)

        layout = QHBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.entreprise_field)
        layout.addWidget(self.button_add)
        layout.addWidget(self.button_reset)

        self.setLayout(layout)

    def save_ban(self):
        text = self.entreprise_field.text()
        if text:
            self.lign_added.emit(text)
            self.reset_text()
    
    def reset_text(self):
        self.entreprise_field.clear()

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

class BanWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        self.title = QLabel("Ban List")
        self.title.setAlignment(Qt.AlignCenter)

        self.ban_field = TextSaver("add a ban :")
        self.ban_field.lign_added.connect(self.add_ban)

        self.ban_patt_field = TextSaver("add a pattern:")
        self.ban_patt_field.lign_added.connect(self.add_pattern)

        self.ban_file_selector = FileSelector("choose a csv file as ban list:")
        self.ban_file_selector.fileSelected.connect(self.add_ban_file)


        self.reset_button = QPushButton("Reset Ban List")
        self.reset_button.clicked.connect(self.reset_bans)

        layout.addWidget(self.title)
        layout.addWidget(self.ban_field)
        layout.addWidget(self.ban_patt_field)
        layout.addWidget(self.ban_file_selector)
        layout.addWidget(self.reset_button, alignment=Qt.AlignCenter)

        self.setLayout(layout)
    
    def reset_bans(self):
        ban_list_manager.reset_ban_list()

    def add_ban(self, ban):
        ban_list_manager.add_ban(ban)
        print(ban)
    
    def add_ban_file(self, path):
        ban_list_manager.add_csv_as_ban(path)

    def add_pattern(self, pattern):
        ban_list_manager.add_pattern(pattern)

class MailWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        self.title = QLabel("Mail Replacement")
        self.title.setAlignment(Qt.AlignCenter)

        self.mail_file_selector = FileSelector("choose a csv file as mail list:")
        self.mail_file_selector.fileSelected.connect(self.add_mail_file)


        self.reset_button = QPushButton("Reset mail List")
        self.reset_button.clicked.connect(self.reset_mail)

        layout.addWidget(self.title)
        layout.addWidget(self.mail_file_selector)
        layout.addWidget(self.reset_button, alignment=Qt.AlignCenter)

        self.setLayout(layout)
    
    def reset_mail(self):
        self.add_mail_file("")

    def add_mail_file(self, path):
        mail_manager.csv_as_list(path)
        
class MainWindow(QMainWindow):
    def __init__ (self):
        super().__init__()
        self.setWindowTitle("CSV handler")

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs) 

        self.tab1 = AcceuilWidget()  
        self.tab2 = BanWidget()
        self.tab3 = MailWidget()

        self.tabs.addTab(self.tab1, "Acceuil")
        self.tabs.addTab(self.tab2, "Ban List")
        self.tabs.addTab(self.tab3, "mail replacement")

        
        
        
