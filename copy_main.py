import os
import glob
import pandas as pd
import re
from collections import defaultdict
import numpy as np
import re

CURRENT_YEAR = 2025
FINAL_DF_COLUMNS = ['list_code_stage', 'list_entrprise', 'list_email']
FINAL_DF_COLUMNS_2 = ['list_code_stage', 'list_email', 'list_entrprise']
BAN_LIST = [r"MBDA.*", r"DGA.*", r"PER.*", r".*@NIIT.*"]

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
    for pattern in BAN_LIST:
        df = df[~df['Employeuremail'].str.contains(pattern, regex=True, na=False)]
        df = df[~df['Employeurcode'].str.contains(pattern, regex=True, na=False)]
    

    return df

def groupping(csv): 
    entreprise_dico = {}
    final_df = pd.DataFrame(columns=FINAL_DF_COLUMNS)

    # Get unique values
    dinstinct_entreprise = csv['Employeurcode'].unique()
    doublon_email = csv['Employeuremail'][csv['Employeuremail'].duplicated(keep=False)].unique()

    print("🔎 Grouping employers by unique codes and emails...")

    # Populate entreprise_dico with unique stage codes for each enterprise
    for entreprise in dinstinct_entreprise:
        entreprise_dico[entreprise] = csv[csv['Employeurcode'] == entreprise]['Stagecode'].unique()

    # Handle duplicate emails
    for email in doublon_email:
        if pd.isna(email):
            continue

        

        # Get all enterprises associated with this email
        entreprises_with_email = csv[csv['Employeuremail'] == email]['Employeurcode'].unique()

        # Merge stage lists for all enterprises with this email
        merged_stages = np.concatenate([
            entreprise_dico[entreprise]
            for entreprise in entreprises_with_email
            if entreprise in entreprise_dico and entreprise_dico[entreprise] is not None
        ])

        # Update the first enterprise with the merged stages
        if len(entreprises_with_email) > 0:
            entreprise_dico[entreprises_with_email[0]] = np.unique(merged_stages)

        # Set other enterprises to None (mark for deletion)
        for entreprise in entreprises_with_email[1:]:
            entreprise_dico[entreprise] = None

    # Clean up the dictionary to remove marked entries
    entreprise_dico = nettoyer_dico(entreprise_dico)
    print(f"🔍 Found {len(entreprise_dico)} unique employers after cleaning. {entreprise_dico}")

    # Build the final DataFrame
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

def groupping_merged_stages(csv):

    stage_combinaison = csv[csv[FINAL_DF_COLUMNS[0]]].unique()
    grpouped_stages = pd.DataFrame(columns=FINAL_DF_COLUMNS_2)

    for stage in stage_combinaison: 
        grpouped_stages.loc[len(grpouped_stages)] = [
            stage,
            csv[csv[FINAL_DF_COLUMNS[0]] == stage][FINAL_DF_COLUMNS[2]],
            csv[csv[FINAL_DF_COLUMNS[0]] == stage][FINAL_DF_COLUMNS[1]]
        ]
    return grpouped_stages

def nettoyer_dico(dico):
    nouveau_dico = {}
    for k, v in dico.items():
        if isinstance(v, np.ndarray) and v.size > 0 and isinstance(k, str) and len(k) > 2:
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
            df = clear_csv(df)
            csv_list.append(df)
        except Exception as e:
            print(f"❌ Error reading file {fichier} : {e}")

    if not csv_list:
        print("❌ No valid CSV files found.")
        return

    csv = pd.concat(csv_list, ignore_index=True)

    csv_cp = csv
    csv_cp.to_excel('result_folder/result-1.xlsx')
    csv_cp.to_csv('result_folder/result-1.csv')

    final_csv = groupping(csv)
    final_csv.to_csv('result_folder/result+1.csv')
    final_csv = groupping_merged_stages(final_csv)
    return final_csv

def main():
    dossier_cible = "csv_folder"
    dossier_source = "exel_folder"

    print("🚀 Starting process...")

    exel_to_csv(dossier_source, dossier_cible)

    fusionner_fichiers_par_code(dossier_cible)

    df = csv_traitement(dossier_cible)

    if df is not None:
        df.to_excel('result_folder/result.xlsx', index=False)
        df.to_csv('result_folder/result.csv', index=False)
        print("✅ Final CSV written to result_folder/result.csv")
    else:
        print("❌ No data to write.")

if __name__ == "__main__":
    main()