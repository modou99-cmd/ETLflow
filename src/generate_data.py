# script pour generer des données de test
# j'utilise numpy pour les distributions aleatoires

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

# seed fixe pour avoir toujours les memes données
np.random.seed(42)


def generate_mesures(nb_lignes: int = 200) -> pd.DataFrame:
    # genere un dataframe avec des mesures simulées
    # j'ai ajouté des erreurs expres pour tester le nettoyage

    # liste des lots
    lots = [f"LOT{str(i).zfill(3)}" for i in range(1, 51)]

    machines = ["M1", "M2", "M3"]
    types_mesure = ["epaisseur", "resistance", "tension"]

    # dates sur 3 mois
    date_debut = datetime(2025, 1, 1)
    dates = [date_debut + timedelta(days=np.random.randint(0, 90))
             for _ in range(nb_lignes)]

    # valeurs autour de 5.0 avec un peu de bruit
    valeurs = np.random.normal(loc=5.0, scale=1.2, size=nb_lignes)

    # temperature entre 80 et 95 degres
    temperatures = np.random.normal(loc=87.0, scale=3.0, size=nb_lignes)

    df = pd.DataFrame({
        "lot_id":      np.random.choice(lots, nb_lignes),
        "machine_id":  np.random.choice(machines, nb_lignes),
        "type_mesure": np.random.choice(types_mesure, nb_lignes),
        "valeur":      np.round(valeurs, 2),
        "temperature": np.round(temperatures, 1),
        "operateur":   np.random.choice(["Dupont", "Martin", "Bernard"], nb_lignes),
        "date_mesure": [d.strftime("%Y-%m-%d") for d in dates],
    })

    # ajout des erreurs -- environ 5% de valeurs manquantes
    idx_manquants = np.random.choice(df.index, size=int(nb_lignes * 0.05))
    df.loc[idx_manquants, "valeur"] = np.nan

    # quelques temperatures manquantes aussi
    idx_temp = np.random.choice(df.index, size=int(nb_lignes * 0.03))
    df.loc[idx_temp, "temperature"] = np.nan

    # valeurs aberantes pour tester le filtrge
    idx_aberrants = np.random.choice(df.index, size=int(nb_lignes * 0.03))
    df.loc[idx_aberrants, "valeur"] = np.random.choice([-5.0, 50.0, 99.9],
                                                        size=int(nb_lignes * 0.03))

    # doublons -- 2% des lignes
    idx_doublons = np.random.choice(df.index, size=int(nb_lignes * 0.02))
    df = pd.concat([df, df.loc[idx_doublons]], ignore_index=True)

    return df


def save_raw_data(df: pd.DataFrame, path: str) -> None:
    # sauvegarde en csv 
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, sep=";", index=False, encoding="utf-8")
    print(f"fichier sauvegardé : {path}")
    print(f"  {len(df)} lignes, {df.shape[1]} colonnes")


if __name__ == "__main__":
    df = generate_mesures(nb_lignes=200)
    save_raw_data(df, "data/raw/mesures_production.csv")