import sys
import os
import glob
import pandas as pd
import re
from collections import defaultdict
import numpy as np
from PySide6.QtWidgets import (
    QApplication, QLabel, QWidget, QVBoxLayout, QMainWindow, QPushButton, QHBoxLayout, QFormLayout, QGridLayout, QMenuBar, QMenu, QFileDialog, QTabWidget, QLineEdit
)
from PySide6.QtCore import Qt, Signal

# ---------------------- CONFIGURATION EN MEMOIRE ----------------------

def_conf = {
    "input_folder": "excel_folder",
    "output_folder": "result_folder",
    "utils_list": [
        "utils/black_list.csv",
        "utils/mail.csv"
    ]
}

conf = def_conf.copy()

ban_list = []
ban_pattern = [
    r"MBDA.*",
    r".*@NIIT.*",
    r"DGA.*",
    r"PER.*"
]

mail_path = ""

# ---------------------- FONCTIONS DE CONF EN MEMOIRE ----------------------

def get_conf(target):
    return conf[target]

def set_conf(target, value):
    conf[target] = value

def reset_conf():
    global conf
    conf = def_conf.copy()

def get_ban_list():
    return ban_list

def add_ban(value):
    ban_list.append(str(value))

def reset_ban_list():
    global ban_list
    ban_list = []

def add_csv_as_ban(csv_path):
    df = pd.read_csv(csv_path, sep=";")
    bans = [i for i in df[df.columns[0]].unique().tolist()]
    for ban in bans:
        ban_list.append(ban)

def add_pattern(pattern):
    ban_pattern.append(rf"{pattern}.*")

def get_patt_list():
    return ban_pattern

def set_mail_path(path):
    global mail_path
    mail_path = path

def get_mail_path():
    return mail_path

def reset_mail_path():
    global mail_path
    mail_path = ""

# ---------------------- LOGIQUE METIER (test_pandas.py) ----------------------

CURRENT_YEAR = 2025
FINAL_DF_COLUMNS = ['list_code_stage', 'list_entreprise', 'list_email']
FINAL_DF_COLUMNS_2 = ['list_code_stage', 'list_email', 'list_entreprise']


def normaliser_code_stage(code):
    return re.sub(r'[12]I$', '', str(code))

def nettoyer_retours_ligne(df, colonne):
    df[colonne] = df[colonne].astype(str).str.replace(r'[\n\r]', ';', regex=True)
    return df

def exel_to_csv(dossier_source, dossier_destination):
    os.makedirs(dossier_destination, exist_ok=True)
    for fichier in os.listdir(dossier_destination):
        chemin_fichier = os.path.join(dossier_destination, fichier)
        if os.path.isfile(chemin_fichier):
            os.remove(chemin_fichier)
    for fichier in os.listdir(dossier_source):
        if fichier.endswith((".xlsx", ".xls")):
            chemin_excel = os.path.join(dossier_source, fichier)
            nom_csv = os.path.splitext(fichier)[0] + ".csv"
            chemin_csv = os.path.join(dossier_destination, nom_csv)
            try:
                df = pd.read_excel(chemin_excel)
                df.to_csv(chemin_csv, sep=";", encoding="ISO-8859-1", index=False)
            except Exception as e:
                print(f"Erreur avec {fichier} : {e}")

def black_listing(csv):
    csv = csv[~csv['Employeurcode'].isin(get_ban_list())]
    return csv

def clear_csv(df):
    df = df.drop_duplicates(subset='Employeuremail', keep='first')
    df = df[df['Stageannée'] <= CURRENT_YEAR]
    df['Employeuremail'] = df['Employeuremail'].replace("", pd.NA)
    df = df.dropna(subset=['Employeuremail'])
    for pattern in get_patt_list():
        df = df[~df['Employeuremail'].str.contains(pattern, regex=True, na=False)]
        df = df[~df['Employeurcode'].str.contains(pattern, regex=True, na=False)]
    df = black_listing(df)
    return df

def replace_email(csv, path):
    email_list = pd.read_csv(path, sep=";", encoding='latin1' )
    entreprise_list = [entreprise for entreprise in email_list['Code Employeur']]
    for idx in csv.index:
        case = csv.at[idx, 'Employeurcode']
        if case in entreprise_list:
            temp  = ", ".join([str(i) for i in email_list[email_list['Code Employeur'] == case]['email de contact'].unique()])
            csv.at[idx, 'Employeuremail'] = temp
    return csv

def groupping(csv):
    final_df = pd.DataFrame(columns=FINAL_DF_COLUMNS)
    distinct_emails = csv['Employeuremail'].unique()
    for email in distinct_emails:
        if pd.isna(email):
            continue
        email_rows = csv[csv['Employeuremail'] == email]
        merged_entreprises = email_rows['Employeurcode'].unique()
        merged_stages = email_rows['Stagecode'].unique()
        final_df.loc[len(final_df)] = [
            tuple(sorted(merged_stages)),
            tuple(sorted(merged_entreprises)),
            (email,)
        ]
    return final_df

def groupping_merged_stages(csv):
    stage_combinaison = csv[FINAL_DF_COLUMNS[0]].unique()
    grpouped_stages = pd.DataFrame(columns=FINAL_DF_COLUMNS_2)
    for stage in stage_combinaison: 
        grpouped_stages.loc[len(grpouped_stages)] = [
            [i for i in stage],
            [i[0] for i in csv[csv[FINAL_DF_COLUMNS[0]] == stage][FINAL_DF_COLUMNS[2]].to_list()],
            [i[0] for i in csv[csv[FINAL_DF_COLUMNS[0]] == stage][FINAL_DF_COLUMNS[1]].to_list()]
        ]
    return grpouped_stages

def I1_I2_fusion(csv):
    for idx in csv.index:
        list_stage = csv.at[idx, FINAL_DF_COLUMNS_2[0]]
        temp = []
        if not isinstance(list_stage, (list, tuple)) or len(list_stage) < 2:
            continue
        for i in range(len(list_stage) - 1):
            stage1 = normaliser_code_stage(list_stage[i])
            stage2 = normaliser_code_stage(list_stage[i + 1])
            if stage1 == stage2:
                continue
            temp.append(list_stage[i])
        last = normaliser_code_stage(list_stage[-1])
        if not temp or temp[-1] != last:
            temp.append(list_stage[-1])
        csv.at[idx, FINAL_DF_COLUMNS_2[0]] = temp
    return csv

def normalize_outplut(csv):
    for idx in csv.index:
        csv.at[idx, 'list_code_stage'] = "; ".join([str(code) for code in csv.at[idx, 'list_code_stage']])  
        csv.at[idx, 'list_email'] = "; ".join([str(email) for email in csv.at[idx, 'list_email']])  
        csv.at[idx, 'list_entreprise'] = "; ".join([str(entreprise) for entreprise in csv.at[idx, 'list_entreprise']])  
    return csv

def I1_I2_fusion_correction(csv):
    csv_copy = csv.copy()
    for idx in csv.index:
        for idx_ in csv.index:
            if idx_ == idx:
                continue
            if csv.at[idx, 'list_code_stage'] == csv.at[idx_, 'list_code_stage']:
                emails_1 = csv.at[idx, 'list_email']
                emails_2 = csv.at[idx_, 'list_email']
                entreprises_1 = csv.at[idx, 'list_entreprise']
                entreprises_2 = csv.at[idx_, 'list_entreprise']
                csv_copy.at[idx, 'list_email'] = emails_1 + emails_2
                csv_copy.at[idx, 'list_entreprise'] = entreprises_1 + entreprises_2
    csv_copy = csv_copy.drop_duplicates(subset='list_code_stage', keep='first')
    return csv_copy

def csv_traitement(dossier):
    fichiers_csv = glob.glob(os.path.join(dossier, "*.csv"))
    csv_list = []
    for fichier in fichiers_csv:
        try:
            df = pd.read_csv(fichier, encoding='iso-8859-1', sep=';')
            df.columns = df.columns.str.replace('\n', '').str.strip()
            df = clear_csv(df)
            csv_list.append(df)
        except Exception as e:
            print(f"Erreur lecture {fichier} : {e}")
    if not csv_list:
        print("Aucun CSV valide trouvé.")
        return
    csv = pd.concat(csv_list, ignore_index=True)
    csv = nettoyer_retours_ligne(csv, 'Employeuremail')
    path = get_mail_path()
    if path:
        csv = replace_email(csv, path)
    csv_cp = csv
    output_folder = get_conf("output_folder")
    csv_cp.to_excel(f'{output_folder}/result-1.xlsx')
    csv_cp.to_csv(f'{output_folder}/result-1.csv')
    final_csv = groupping(csv)
    final_csv.to_csv(f'{output_folder}/result+1.csv')
    final_csv = groupping_merged_stages(final_csv)
    final_csv = I1_I2_fusion(final_csv)
    final_csv = normalize_outplut(final_csv)
    final_csv = I1_I2_fusion_correction(final_csv)
    return final_csv

def main():
    dossier_cible = "csv_folder"
    dossier_source = get_conf("input_folder")
    print(dossier_source)
    exel_to_csv(dossier_source, dossier_cible)
    df = csv_traitement(dossier_cible)
    result_folder = get_conf("output_folder")
    if df is not None:
        df.to_excel(f'{result_folder}/result.xlsx', index=False)
        df.to_csv(f'{result_folder}/result.csv', index=False)
        print("Final CSV écrit dans result_folder/result.csv")
    else:
        print("Aucune donnée à écrire.")

def sub_main(source):
    df = sub_csv_traitement(source)
    result_folder = "sub_output"
    if df is not None:
        df.to_excel(f'{result_folder}/result.xlsx', index=False)
        df.to_csv(f'{result_folder}/result.csv', index=False)
        print("Final CSV écrit dans result_folder/result.csv")
    else:
        print("Aucune donnée à écrire.")

def sub_csv_traitement(fichier):
    try:
        df = pd.read_csv(fichier, encoding='iso-8859-1')
        df.columns = df.columns.str.replace('\n', '').str.strip()
    except Exception as e:
        print(f"Erreur lecture {fichier} : {e}")
        return None
    final_csv = groupping(df)
    final_csv = groupping_merged_stages(final_csv)
    final_csv = I1_I2_fusion(final_csv)
    final_csv = normalize_outplut(final_csv)
    final_csv = I1_I2_fusion_correction(final_csv)
    return final_csv

# ---------------------- UI Qt (fusion de gui_class.py) ----------------------

def quit_():
    sys.exit()

class FolderSelector(QWidget):
    folderSelected = Signal(str)
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
    fileSelected = Signal(str)
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
    lign_added = Signal(str)
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
        set_conf("input_folder", path)
    def output_chosen(self, path):
        set_conf("output_folder", path)
    def start_process(self):
        try:
            main()
        except Exception as e:
            sys.exit()
    def reset_conf(self):
        reset_conf()
        self.input_selector.reset_label()
        self.output_selector.reset_label()

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
        reset_ban_list()
    def add_ban(self, ban):
        add_ban(ban)
    def add_ban_file(self, path):
        add_csv_as_ban(path)
    def add_pattern(self, pattern):
        add_pattern(pattern)

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
        reset_mail_path()
    def add_mail_file(self, path):
        set_mail_path(path)

class SubMainWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.title = QLabel("SUB processing")
        self.title.setAlignment(Qt.AlignCenter)
        self.mail_file_selector = FileSelector("choose compiled file :")
        self.mail_file_selector.fileSelected.connect(self.add_file)
        layout.addWidget(self.title)
        layout.addWidget(self.mail_file_selector)
        self.setLayout(layout)
    def add_file(self, path):
        sub_main(path)

class MainWindow(QMainWindow):
    def __init__ (self):
        super().__init__()
        self.setWindowTitle("CSV handler")
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs) 
        self.tab1 = AcceuilWidget()  
        self.tab2 = BanWidget()
        self.tab3 = MailWidget()
        self.tab4 = SubMainWidget()
        self.tabs.addTab(self.tab1, "Acceuil")
        self.tabs.addTab(self.tab2, "Ban List")
        self.tabs.addTab(self.tab3, "mail replacement")
        self.tabs.addTab(self.tab4, "sub process")

# ---------------------- MAIN ----------------------

def main_window(): 
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()

if __name__ == '__main__':
    main_window() 
