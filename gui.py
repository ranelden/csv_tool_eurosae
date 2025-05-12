import tkinter as tk
from tkinter import filedialog
import test_pandas

def choisir_fichier():
    fichier = filedialog.askopenfilename(title="Choisir un fichier CSV")
    if fichier:
        global dossier_selectioner 
        dossier_selectioner = fichier
        


def main_window(): 
    
    # Créer la fenêtre principale
    fenetre = tk.Tk()
    fenetre.title("Ma première interface")
    fenetre.geometry("400x300")  # largeur x hauteur

    # Créer un widget (ex : label)
    label = tk.Label(fenetre, text="Bonjour !")
    label.pack()
    """
    btn = tk.Button(fenetre, text="Sélectionner un fichier CSV", command=choisir_fichier())
    btn.pack(pady=20)
    """
    # Démarrer la boucle d’événement
    fenetre.mainloop()



if __name__ == '__main__':
    main_window()
