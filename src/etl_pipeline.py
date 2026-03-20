# =============================================================
# etl_pipeline.py
# Pipeline ETL complet — Qualité de production industrielle
# Simule le travail de migration R → Python chez X-FAB
# =============================================================

import pandas as pd
import numpy as np
import logging
import os
from datetime import datetime
from sqlalchemy import create_engine

# ── Configuration du logging ──────────────────────────────────
# Le logging trace toutes les étapes dans la console ET
# dans un fichier .log — bonne pratique DevOps obligatoire
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        # Affiche dans la console
        logging.StreamHandler(),
        # Sauvegarde dans un fichier horodaté
        logging.FileHandler(
            f"logs/etl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
    ]
)
log = logging.getLogger(__name__)


# =============================================================
# ÉTAPE 1 — EXTRACT : lire les données brutes
# =============================================================

def extract(input_path: str) -> pd.DataFrame:
    """
    Lit le fichier CSV brut généré par le système MES/SCADA.
    Retourne un DataFrame pandas.
    """
    log.info(f"[EXTRACT] Lecture du fichier : {input_path}")

    # Vérification que le fichier existe avant de lire
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Fichier introuvable : {input_path}")

    # Lecture avec parse_dates pour convertir la colonne date
    df = pd.read_csv(
        input_path,
        sep=";",
        parse_dates=["date_mesure"],
        encoding="utf-8"
    )

    log.info(f"[EXTRACT] {len(df)} lignes lues, {df.shape[1]} colonnes")
    log.info(f"[EXTRACT] Colonnes : {list(df.columns)}")

    return df


# =============================================================
# ÉTAPE 2 — TRANSFORM : nettoyer et enrichir les données
# =============================================================

def transform(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Nettoie les données brutes et calcule les indicateurs qualité.
    Retourne un tuple : (df_clean, df_agregats)
    """
    log.info("[TRANSFORM] Début du nettoyage...")
    nb_initial = len(df)

    # ── 2.1 Inspection initiale ───────────────────────────────
    log.info(f"[TRANSFORM] Valeurs manquantes :\n{df.isnull().sum()}")

    # ── 2.2 Suppression des doublons ─────────────────────────
    # Un doublon = même lot + même machine + même date + même type
    df = df.drop_duplicates(
        subset=["lot_id", "machine_id", "type_mesure", "date_mesure"]
    )
    log.info(f"[TRANSFORM] Doublons supprimés : {nb_initial - len(df)}")

    # ── 2.3 Suppression des lignes sans valeur mesurée ────────
    # Une mesure sans valeur est inutilisable pour la qualité
    nb_avant = len(df)
    df = df.dropna(subset=["valeur"])
    log.info(f"[TRANSFORM] Lignes sans valeur supprimées : {nb_avant - len(df)}")

    # ── 2.4 Remplacement des températures manquantes ──────────
    # On utilise la moyenne par machine (plus précis que global)
    # transform("mean") calcule la moyenne du groupe et la
    # réinsère sur chaque ligne — même longueur que df
    df["temperature"] = df.groupby("machine_id")["temperature"].transform(
        lambda x: x.fillna(x.mean())
    )
    log.info("[TRANSFORM] Températures manquantes remplacées par moyenne machine")

    # ── 2.5 Filtrage des valeurs aberrantes ───────────────────
    # Plage physiquement acceptable pour les mesures
    # (définie par le département qualité X-FAB)
    VALEUR_MIN = 0.0
    VALEUR_MAX = 15.0
    TEMP_MIN   = 70.0
    TEMP_MAX   = 100.0

    nb_avant = len(df)
    df = df[df["valeur"].between(VALEUR_MIN, VALEUR_MAX)]
    df = df[df["temperature"].between(TEMP_MIN, TEMP_MAX)]
    log.info(f"[TRANSFORM] Valeurs aberrantes supprimées : {nb_avant - len(df)}")

    # ── 2.6 Colonnes calculées ────────────────────────────────
    # Indicateur qualité : hors spécification si valeur > 7.0
    # C'est un seuil typique de yield enhancement
    SEUIL_SPEC = 7.0
    df["hors_spec"] = df["valeur"] > SEUIL_SPEC

    # Mois d'extraction pour l'analyse temporelle
    df["mois"] = df["date_mesure"].dt.to_period("M").astype(str)

    # Score qualité normalisé entre 0 et 1
    # Plus le score est proche de 1, meilleure est la mesure
    df["score_qualite"] = 1 - (df["valeur"] / VALEUR_MAX)
    df["score_qualite"] = df["score_qualite"].clip(0, 1).round(3)

    log.info(f"[TRANSFORM] Nettoyage terminé : {len(df)} lignes propres")
    log.info(f"[TRANSFORM] Taux hors spec : {df['hors_spec'].mean():.1%}")

    # ── 2.7 Agrégation par lot ────────────────────────────────
    # Résumé statistique par lot — c'est ce qui sera chargé en BDD
    # et visualisé dans Power BI
    df_agregats = df.groupby(
        ["lot_id", "machine_id", "mois"]
    ).agg(
        valeur_moyenne  = ("valeur",        "mean"),
        valeur_max      = ("valeur",        "max"),
        valeur_min      = ("valeur",        "min"),
        ecart_type      = ("valeur",        "std"),
        nb_mesures      = ("valeur",        "count"),
        nb_hors_spec    = ("hors_spec",     "sum"),
        temp_moyenne    = ("temperature",   "mean"),
        score_moyen     = ("score_qualite", "mean"),
    ).reset_index()

    # Taux de conformité par lot (% de mesures dans les specs)
    df_agregats["taux_conformite"] = (
        1 - df_agregats["nb_hors_spec"] / df_agregats["nb_mesures"]
    ).round(3)

    # Arrondi des colonnes numériques pour la lisibilité
    cols_num = ["valeur_moyenne", "valeur_max", "valeur_min",
                "ecart_type", "temp_moyenne", "score_moyen"]
    df_agregats[cols_num] = df_agregats[cols_num].round(3)

    log.info(f"[TRANSFORM] Agrégats calculés : {len(df_agregats)} lots")

    return df, df_agregats


# =============================================================
# ÉTAPE 3 — LOAD : écrire les résultats
# =============================================================

def load(df_clean: pd.DataFrame,
         df_agregats: pd.DataFrame,
         db_url: str) -> None:
    """
    Écrit les données transformées :
    - En base SQLite (pour Power BI et R)
    - En CSV (pour partage et archivage)
    - En Parquet (pour performance)
    """
    log.info("[LOAD] Début de l'écriture...")

    os.makedirs("data/processed", exist_ok=True)
    os.makedirs("data/exports", exist_ok=True)

    # ── 3.1 Écriture en base SQLite ───────────────────────────
    # SQLite crée un fichier .db local — pas besoin de serveur
    # Parfait pour tester en local avant de passer à PostgreSQL
    engine = create_engine(db_url)

    df_clean.to_sql(
        "mesures_clean",      # nom de la table
        con=engine,
        if_exists="replace",  # recrée la table à chaque run
        index=False
    )
    log.info("[LOAD] Table 'mesures_clean' écrite en base")

    df_agregats.to_sql(
        "agregats_qualite",
        con=engine,
        if_exists="replace",
        index=False
    )
    log.info("[LOAD] Table 'agregats_qualite' écrite en base")

    # ── 3.2 Écriture en CSV ───────────────────────────────────
    # Pour Power BI (import direct) et partage avec l'équipe
    df_clean.to_csv(
        "data/processed/mesures_clean.csv",
        sep=";", index=False, encoding="utf-8"
    )
    df_agregats.to_csv(
        "data/exports/agregats_qualite.csv",
        sep=";", index=False, encoding="utf-8"
    )
    log.info("[LOAD] Fichiers CSV exportés")

    # ── 3.3 Écriture en Parquet ───────────────────────────────
    # Format optimisé pour les gros volumes — standard Data Eng.
    df_clean.to_parquet(
        "data/processed/mesures_clean.parquet",
        index=False
    )
    log.info("[LOAD] Fichier Parquet sauvegardé")

    log.info("[LOAD] Écriture terminée")


# =============================================================
# POINT D'ENTRÉE PRINCIPAL
# =============================================================

def run_pipeline():
    """Lance le pipeline ETL complet de bout en bout"""
    log.info("=" * 55)
    log.info("DÉMARRAGE DU PIPELINE ETL — Qualité Production X-FAB")
    log.info("=" * 55)

    try:
        # Chemins des fichiers
        INPUT_PATH = "data/raw/mesures_production.csv"
        DB_URL     = "sqlite:///data/xfab_quality.db"

        # Lancement des 3 étapes ETL
        df_raw      = extract(INPUT_PATH)
        df_clean, df_agregats = transform(df_raw)
        load(df_clean, df_agregats, DB_URL)

        log.info("=" * 55)
        log.info("PIPELINE TERMINÉ AVEC SUCCÈS")
        log.info(f"  Lignes nettoyées  : {len(df_clean)}")
        log.info(f"  Lots agrégés      : {len(df_agregats)}")
        log.info("=" * 55)

    except Exception as e:
        # En cas d'erreur, on log le message et on arrête proprement
        log.error(f"ERREUR PIPELINE : {e}")
        raise


if __name__ == "__main__":
    run_pipeline()
