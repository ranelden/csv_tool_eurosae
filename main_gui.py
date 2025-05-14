from PySide6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QMainWindow, QPushButton 
import sys
#import test_pandas
from gui_class import MainWindow

def choisir_fichier():
    pass
        


def main_window(): 
    
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()

if __name__ == '__main__':
    main_window()
