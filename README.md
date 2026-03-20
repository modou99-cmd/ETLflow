# ETLflow

Pipeline ETL de qualité de production industrielle.  
Projet personnel pour apprendre Python, R et Power BI dans un contexte de Data Engineering industriel.

---

## Contexte

Ce projet simule le travail d'un Data Engineer dans une usine de production industrielle :

- Les machines de production génèrent des milliers de mesures par jour (épaisseur, résistance, tension)
- Ces mesures sont exportées par le système MES/SCADA en CSV
- Le pipeline Python nettoie, transforme et stocke ces données
- R génère des analyses statistiques et des graphiques
- Power BI affiche un dashboard de suivi qualité en temps réel

---

## Structure du projet

```
ETLflow/
│
├── data/
│   ├── raw/                    ← données brutes (CSV MES/SCADA)
│   ├── processed/              ← données nettoyées par le pipeline Python
│   └── exports/                ← exports CSV + graphiques R pour Power BI
│
├── src/
│   ├── generate_data.py        ← génère les données de test simulées
│   └── etl_pipeline.py         ← pipeline ETL complet (Extract Transform Load)
│
├── r_analysis/
│   └── analyse_qualite.R       ← analyse statistique + graphiques avec R
│
├── tests/
│   └── test_etl.py             ← 7 tests unitaires avec pytest
│
├── dashboard/
│   └── POWERBI_GUIDE.md        ← guide étape par étape pour Power BI
│
├── logs/                       ← fichiers de log horodatés (créés automatiquement)
│
├── requirements.txt            ← librairies Python nécessaires
└── README.md                   ← ce fichier
```

---

## Installation

### Prérequis

- [Anaconda](https://www.anaconda.com/download) installé
- [R](https://cran.r-project.org) installé (pour la partie analyse)
- [Power BI Desktop](https://powerbi.microsoft.com/fr-fr/desktop) installé (pour le dashboard)

### Étape 1 — Cloner ou télécharger le projet

```bash
# Avec Git
git clone https://github.com/modou99-cmd/ETLflow.git
cd ETLflow

# Sinon : télécharge le ZIP et décompresse-le
```

### Étape 2 — Créer l'environnement Anaconda

Ouvre **Anaconda Prompt** et tape :

```bash
conda create -n ETLflow python=3.11 -y
conda activate ETLflow
```

### Étape 3 — Installer les dépendances Python

```bash
conda install pandas sqlalchemy pyarrow pytest -y
```

### Étape 4 — Vérifier l'installation

```bash
python -c "import pandas; print('pandas OK')"
python -c "import sqlalchemy; print('sqlalchemy OK')"
python -c "import pyarrow; print('pyarrow OK')"
```

Tu dois voir les 3 lignes OK sans erreur.

---

## Utilisation

### 1. Générer les données de test

```bash
python src/generate_data.py
```

Crée le fichier `data/raw/mesures_production.csv` avec 200 lignes de mesures simulées.

### 2. Lancer le pipeline ETL Python

```bash
python src/etl_pipeline.py
```

Le pipeline :
- Lit les données brutes
- Nettoie (doublons, valeurs manquantes, aberrantes)
- Calcule les indicateurs qualité (hors_spec, score_qualite, taux_conformite)
- Écrit les résultats dans la base SQLite, en CSV et en Parquet
- Génère un fichier de log dans `logs/`

### 3. Lancer l'analyse R

Ouvre RStudio et exécute :

```r
setwd("C:/chemin/vers/ETLflow")
source("r_analysis/analyse_qualite.R")
```

Génère 3 graphiques PNG dans `data/exports/r_plots/` et 2 CSV pour Power BI.

### 4. Lancer les tests

```bash
pytest tests/test_etl.py -v
```

Tu dois voir 7 tests passer en vert.

### 5. Ouvrir le dashboard Power BI

Suis les instructions dans `dashboard/POWERBI_GUIDE.md`.  
Importe les fichiers CSV de `data/exports/` dans Power BI Desktop.

---

## Ce que ce projet couvre

| Technologie | Concepts couverts |
|-------------|------------------|
| Python | pandas, SQLAlchemy, logging, pytest, ETL complet |
| R | dplyr, ggplot2, readr, analyse statistique, export graphiques |
| Power BI | Import CSV, DAX, visuels, actualisation des données |
| DevOps | Git, structure de projet, tests unitaires, logs |

---

## Ordre d'apprentissage recommandé

1. Lance `generate_data.py` et inspecte le CSV brut généré
2. Lis et comprends `etl_pipeline.py` ligne par ligne
3. Lance le pipeline et vérifie les fichiers produits
4. Lance les tests avec pytest — essaie de comprendre chaque test
5. Ouvre `analyse_qualite.R` dans RStudio et lance-le
6. Crée le dashboard Power BI en suivant le guide

---

## Auteur

WADE Modou — Master 2 Transformation Numérique pour l'Industrie  
Université Paris-Saclay
