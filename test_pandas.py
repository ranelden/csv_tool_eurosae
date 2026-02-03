import os
import glob
import pandas as pd
import re
from collections import defaultdict
import numpy as np
import conf_manager
import ban_list_manager
import json

CURRENT_YEAR = 2026
FINAL_DF_COLUMNS = ['list_code_stage', 'list_entreprise', 'list_email']
FINAL_DF_COLUMNS_2 = ['list_code_stage', 'list_email', 'list_entreprise']
#BAN_LIST_PAT = [r"MBDA.*", r"DGA.*", r"PER.*", r".*@NIIT.*"]
BAN_LIST_PAT = ban_list_manager.get_patt_list()

def normaliser_code_stage(code):
    return re.sub(r'[12]I$', '', str(code))

def nettoyer_retours_ligne(df, colonne):
    df[colonne] = df[colonne].astype(str).str.replace(r'[\n\r]', ';', regex=True)
    return df

def dossier_utils_to_csv():# inutil pour l instant
    excel = pd.read_excel('utils/black_list.xlsx')
    print(excel)
    excel.to_csv('utils/black_list.csv', index=False)

def exel_to_csv(dossier_source, dossier_destination):
    
    os.makedirs(dossier_destination, exist_ok=True)  # Crée si inexistant
    
    # Suppression du contenu du dossier de destination
    for fichier in os.listdir(dossier_destination):
        chemin_fichier = os.path.join(dossier_destination, fichier)
        if os.path.isfile(chemin_fichier):
            os.remove(chemin_fichier)
    
    # Conversion des fichiers Excel en CSV
    for fichier in os.listdir(dossier_source):
        if fichier.endswith((".xlsx", ".xls")):
            chemin_excel = os.path.join(dossier_source, fichier)
            nom_csv = os.path.splitext(fichier)[0] + ".csv"
            chemin_csv = os.path.join(dossier_destination, nom_csv)
            print(chemin_excel)
            try:
                df = pd.read_excel(chemin_excel)
                df.to_csv(chemin_csv, sep=";", encoding="ISO-8859-1", index=False)
                print(f"✅ Converti : {fichier} → {nom_csv}")
            except Exception as e:
                print(f"❌ Erreur avec {fichier} : {e}")

def nettoyer_dico(dico):
    nouveau_dico = {}
    for k, v in dico.items():
        if isinstance(v, np.ndarray) and v.size > 0 and isinstance(k, str) and len(k) > 2:
            nouveau_dico[k] = v
    return nouveau_dico

def fusionner_fichiers_par_code(dossier):
    print("🔍 Searching for CSV files to merge...")
    fichiers_csv = glob.glob(os.path.join(dossier, "*.csv"))
    groupes = defaultdict(list)
    chemins_groupes = defaultdict(list)

    for chemin_fichier in fichiers_csv:
        try:
            df = pd.read_csv(chemin_fichier, encoding='iso-8859-1', sep=';')
            df.columns = df.columns.str.replace('\n', '').str.strip()

            if 'Stagecode' not in df.columns:
                continue

            code_base = str(df['Stagecode'].iloc[0])
            groupes[code_base].append(df)
            chemins_groupes[code_base].append(chemin_fichier)

        except Exception as e:
            print(f"❌ Error reading file {chemin_fichier} : {e}")

    print("📦 Merging files by stage code...")
    for code, liste_df in groupes.items():
        fusion = pd.concat(liste_df, ignore_index=True)
        chemin_sortie = os.path.join(dossier, f"{code}.csv")
        fusion.to_csv(chemin_sortie, index=False, sep=';', encoding='iso-8859-1')
        print(f"✅ File created: {chemin_sortie}")

        for chemin in chemins_groupes[code]:
            try:
                os.remove(chemin)
            except Exception as e:
                print(f"❌ Error deleting {chemin} : {e}")

def black_listing(csv):
    
    #black_list = pd.read_csv('utils/black_list.csv', sep=";")
    #black_list = [i for i in black_list['Code Employeur']]

    black_list = ban_list_manager.get_ban_list()

    csv = csv[~csv['Employeurcode'].isin(black_list)]
    
    return csv

def clear_csv(df):
    """
    Cleans the DataFrame by:
    - Filtering rows based on the current year (`Stageannée`).
    - Removing duplicates based on `Employeuremail`, keeping only the first occurrence.
    - Removing rows with invalid or empty emails.
    - Filtering out banned patterns in `Employeuremail` and `Employeurcode`.
    """
    

    # Drop duplicate emails, keeping only the first occurrence
    df = df.drop_duplicates(subset='Employeuremail', keep='first')
    
    # Filter rows for the current year
    df = df[df['Stageannée'] != CURRENT_YEAR]
    
    
    # Remove rows with empty or invalid emails
    df['Employeuremail'] = df['Employeuremail'].replace("", pd.NA)
    df = df.dropna(subset=['Employeuremail'])

    # Filter out banned patterns
    for pattern in BAN_LIST_PAT:
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
    """
    Groups data by `Employeuremail` and merges associated `Employeurcode` and `Stagecode`.
    """
    final_df = pd.DataFrame(columns=FINAL_DF_COLUMNS)

    # Get distinct emails
    distinct_emails = csv['Employeuremail'].unique()

    print("🔎 Grouping data by unique emails...")

    for email in distinct_emails:
        if pd.isna(email):
            continue

        # Filter rows for the current email
        email_rows = csv[csv['Employeuremail'] == email]

        # Merge associated `Employeurcode` and `Stagecode`
        merged_entreprises = email_rows['Employeurcode'].unique()
        merged_stages = email_rows['Stagecode'].unique()

        # Add to final DataFrame
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
        #print(", ".join([i[0] for i in csv[csv[FINAL_DF_COLUMNS[0]] == stage][FINAL_DF_COLUMNS[2]].to_list()]))
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
        
        # Ajouter le dernier stage s’il est unique
        last = normaliser_code_stage(list_stage[-1])
        if not temp or temp[-1] != last:
            temp.append(list_stage[-1])

        csv.at[idx, FINAL_DF_COLUMNS_2[0]] = temp

    
    

    return csv

def normalize_outplut (csv):
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

                # Concatène les listes directement
                csv_copy.at[idx, 'list_email'] = emails_1 + emails_2
                csv_copy.at[idx, 'list_entreprise'] = entreprises_1 + entreprises_2

    csv_copy = csv_copy.drop_duplicates(subset='list_code_stage', keep='first')

    return csv_copy

def csv_traitement(dossier):
    print("📁 Processing cleaned CSV files...")
    fichiers_csv = glob.glob(os.path.join(dossier, "*.csv"))
    csv_list = []

    for fichier in fichiers_csv:
        try:
            df = pd.read_csv(fichier, encoding='iso-8859-1', sep=';')
            df.columns = df.columns.str.replace('\n', '').str.strip()
            df = clear_csv(df)
            csv_list.append(df)
        except Exception as e:
            print(f"❌ Error reading file {fichier} : {e}")

    if not csv_list:
        print("❌ No valid CSV files found.")
        return

    csv = pd.concat(csv_list, ignore_index=True)

    csv = nettoyer_retours_ligne(csv, 'Employeuremail')

    with open('conf/mail.json') as f:
        path = json.load(f)
    if path["path"]:
        csv = replace_email(csv, path["path"])

    csv_cp = csv
    csv_cp.to_excel('result_folder/result-1.xlsx')
    csv_cp.to_csv('result_folder/result-1.csv')

    final_csv = groupping(csv)
    final_csv.to_csv('result_folder/result+1.csv')

    final_csv = groupping_merged_stages(final_csv)
    final_csv = I1_I2_fusion(final_csv)

    final_csv = normalize_outplut(final_csv)

    final_csv = I1_I2_fusion_correction(final_csv)

    return final_csv

def main():
    dossier_cible = "csv_folder"
    dossier_source = conf_manager.get("input_folder")
    print(dossier_source)

    print("🚀 Starting process...")

    #dossier_utils_to_csv()

    exel_to_csv(dossier_source, dossier_cible)

    #fusionner_fichiers_par_code(dossier_cible)

    df = csv_traitement(dossier_cible)

    result_folder = conf_manager.get("output_folder")

    if df is not None:
        df.to_excel(f'{result_folder}/result.xlsx', index=False)
        df.to_csv(f'{result_folder}/result.csv', index=False)
        print("✅ Final CSV written to result_folder/result.csv")
    else:
        print("❌ No data to write.")

def sub_main(source):

    print("🚀 Starting process...")

    #fusionner_fichiers_par_code(dossier_cible)

    df = sub_csv_traitement(source)

    result_folder = "sub_output"

    if df is not None:
        df.to_excel(f'{result_folder}/result.xlsx', index=False)
        df.to_csv(f'{result_folder}/result.csv', index=False)
        print("✅ Final CSV written to result_folder/result.csv")
    else:
        print("❌ No data to write.")

def sub_csv_traitement(fichier):
    print("📁 Processing cleaned CSV files...")

    try:
        df = pd.read_csv(fichier, encoding='iso-8859-1')
        df.columns = df.columns.str.replace('\n', '').str.strip()
            
    except Exception as e:
            print(f"❌ Error reading file {fichier} : {e}")

    final_csv = groupping(df)
    final_csv = groupping_merged_stages(final_csv)
    final_csv = I1_I2_fusion(final_csv)

    final_csv = normalize_outplut(final_csv)

    final_csv = I1_I2_fusion_correction(final_csv)

    return final_csv

if __name__ == "__main__":
    main()
