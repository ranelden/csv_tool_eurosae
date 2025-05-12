import os
import glob
import pandas as pd
import re
from collections import defaultdict
import numpy as np

CURRENT_YEAR = 2025
FINAL_DF_COLUMNS = ['list_code_stage', 'list_entrprise', 'list_email']

def normaliser_code_stage(code):
    return re.sub(r'[12]I$', '', str(code))

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
            
            try:
                df = pd.read_excel(chemin_excel)
                df.to_csv(chemin_csv, sep=";", encoding="ISO-8859-1", index=False)
                print(f"✅ Converti : {fichier} → {nom_csv}")
            except Exception as e:
                print(f"❌ Erreur avec {fichier} : {e}")


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

def clear_csv(csv_path):
    df = pd.read_csv(csv_path, encoding='iso-8859-1', sep=';')
    df.columns = df.columns.str.replace('\n', '').str.strip()

    entreprise_2025 = df[df['Stageannée'] == CURRENT_YEAR]['Employeurcode'].unique()
    df = df[~df['Employeurcode'].isin(entreprise_2025)]
    df = df.drop_duplicates(subset='Employeurcode', keep='first')

    return df

def groupping(csv): 
    entreprise_dico = {}
    email_duplicate = {}
    final_df = pd.DataFrame(columns=FINAL_DF_COLUMNS)

    dinstinct_stage = csv['Stagecode'].unique()
    dinstinct_entreprise = csv['Employeurcode'].unique()
    doublon_email = csv['Employeuremail'][csv['Employeuremail'].duplicated(keep=False)].unique()

    print("🔎 Grouping employers by unique codes and emails...")

    for entreprise in dinstinct_entreprise:
        entreprise_dico[entreprise] = csv[csv['Employeurcode'] == entreprise]['Stagecode'].unique()

    for email in doublon_email:
        if pd.isna(email):
            continue
        email_duplicate[email] = csv[csv['Employeuremail'] == email]['Employeurcode'].unique()

    for email, entreprise_list in email_duplicate.items():
        if not isinstance(email, str):
            continue
        list_list_entreprise = [
            entreprise_dico[entreprise]
            for entreprise in entreprise_list
            if entreprise in entreprise_dico and entreprise_dico[entreprise] is not None
        ]
        if not list_list_entreprise:
            continue

        fusion = np.concatenate(list_list_entreprise)
        entreprise_dico[email[0]] = fusion
        for cle in email[1:]:
            entreprise_dico[cle] = None

    entreprise_dico = nettoyer_dico(entreprise_dico)

    for entreprise in entreprise_dico.keys():
        if entreprise_dico[entreprise] is None:
            continue

        temp_list_entreprise = [entreprise]
        for entreprise_to_compare in entreprise_dico.keys():
            if (
                entreprise != entreprise_to_compare and
                np.array_equal(np.sort(entreprise_dico[entreprise]), np.sort(entreprise_dico[entreprise_to_compare]))
            ):
                temp_list_entreprise.append(entreprise_to_compare)

        final_df.loc[len(final_df)] = [
            tuple(entreprise_dico[entreprise].tolist()),
            tuple(sorted(temp_list_entreprise)),
            tuple(csv[csv['Employeurcode'].isin(temp_list_entreprise)]['Employeuremail'].unique().tolist())
        ]

    final_df = final_df.drop_duplicates(keep='first')    
    return final_df

def nettoyer_dico(dico):
    nouveau_dico = {}
    for k, v in dico.items():
        if isinstance(v, np.ndarray) and v.size > 0 and isinstance(k, str) and len(k) > 5:
            nouveau_dico[k] = v
    return nouveau_dico

def csv_traitement(dossier):
    print("📁 Processing cleaned CSV files...")
    fichiers_csv = glob.glob(os.path.join(dossier, "*.csv"))
    csv_list = []

    for fichier in fichiers_csv:
        try:
            df = pd.read_csv(fichier, encoding='iso-8859-1', sep=';')
            df.columns = df.columns.str.replace('\n', '').str.strip()
            csv_list.append(df)
        except Exception as e:
            print(f"❌ Error reading file {fichier} : {e}")

    if not csv_list:
        print("❌ No valid CSV files found.")
        return

    csv = pd.concat(csv_list, ignore_index=True)
    final_csv = groupping(csv)
    return final_csv

def main():
    dossier_cible = "csv_folder"
    dossier_source = "exel_folder"

    print("🚀 Starting process...")

    exel_to_csv(dossier_source, dossier_cible)

    fusionner_fichiers_par_code(dossier_cible)

    df = csv_traitement(dossier_cible)

    if df is not None:
        df.to_csv('result_folder/result.csv', index=False)
        print("✅ Final CSV written to result_folder/result.csv")
    else:
        print("❌ No data to write.")

main()