# =============================================================
# test_etl.py
# Tests unitaires du pipeline ETL
# Lance avec : pytest tests/test_etl.py -v
# =============================================================

import pytest
import pandas as pd
import numpy as np
from io import StringIO
import sys
import os

# On ajoute le dossier src au chemin Python
# pour pouvoir importer etl_pipeline
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from etl_pipeline import transform


# ── Données de test réutilisables ─────────────────────────────
# @pytest.fixture crée un objet réutilisable dans tous les tests
@pytest.fixture
def df_sample():
    """DataFrame de test avec des cas typiques"""
    data = """lot_id;machine_id;type_mesure;valeur;temperature;operateur;date_mesure;hors_spec
LOT001;M1;epaisseur;3.2;85.0;Dupont;2025-01-10;False
LOT002;M2;resistance;;92.0;Martin;2025-01-11;False
LOT003;M1;tension;4.1;85.5;Dupont;2025-01-12;False
LOT003;M1;tension;4.1;85.5;Dupont;2025-01-12;False
LOT004;M3;epaisseur;-5.0;88.0;Bernard;2025-01-13;False
LOT005;M2;resistance;5.5;91.0;Martin;2025-01-14;False
LOT006;M1;tension;8.5;87.0;Dupont;2025-01-15;False
"""
    df = pd.read_csv(StringIO(data), sep=";", parse_dates=["date_mesure"])
    return df


# ── Tests ─────────────────────────────────────────────────────

def test_transform_supprime_doublons(df_sample):
    """LOT003 apparaît 2 fois → doit être réduit à 1 après transform"""
    df_clean, _ = transform(df_sample)
    nb_lot003 = len(df_clean[df_clean["lot_id"] == "LOT003"])
    assert nb_lot003 == 1, f"Attendu 1 ligne pour LOT003, obtenu {nb_lot003}"


def test_transform_supprime_valeurs_manquantes(df_sample):
    """LOT002 n'a pas de valeur → doit être supprimé"""
    df_clean, _ = transform(df_sample)
    assert "LOT002" not in df_clean["lot_id"].values


def test_transform_supprime_valeurs_aberrantes(df_sample):
    """LOT004 a valeur=-5.0 → hors plage [0,15] → doit être supprimé"""
    df_clean, _ = transform(df_sample)
    assert "LOT004" not in df_clean["lot_id"].values


def test_transform_colonne_hors_spec(df_sample):
    """LOT006 a valeur=8.5 > seuil 7.0 → hors_spec doit être True"""
    df_clean, _ = transform(df_sample)
    lot006 = df_clean[df_clean["lot_id"] == "LOT006"]
    assert len(lot006) > 0, "LOT006 doit exister dans df_clean"
    assert lot006["hors_spec"].values[0] == True


def test_transform_aucune_valeur_manquante(df_sample):
    """Après transform, aucune valeur nulle ne doit rester dans 'valeur'"""
    df_clean, _ = transform(df_sample)
    assert df_clean["valeur"].isnull().sum() == 0


def test_agregats_colonnes_presentes(df_sample):
    """Les agrégats doivent contenir les colonnes attendues"""
    _, df_agregats = transform(df_sample)
    colonnes_attendues = [
        "lot_id", "machine_id", "valeur_moyenne",
        "nb_mesures", "taux_conformite"
    ]
    for col in colonnes_attendues:
        assert col in df_agregats.columns, f"Colonne manquante : {col}"


def test_taux_conformite_entre_0_et_1(df_sample):
    """Le taux de conformité doit toujours être entre 0 et 1"""
    _, df_agregats = transform(df_sample)
    assert df_agregats["taux_conformite"].between(0, 1).all()
