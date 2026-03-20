# Guide Power BI — Dashboard Qualité Production X-FAB

## Fichiers à importer dans Power BI

Une fois le pipeline Python lancé, ces fichiers sont disponibles :

| Fichier | Contenu |
|---------|---------|
| `data/processed/mesures_clean.csv` | Toutes les mesures nettoyées |
| `data/exports/agregats_qualite.csv` | KPIs par lot et machine |
| `data/exports/stats_machine_r.csv` | Statistiques R par machine |

---

## Étapes d'import dans Power BI Desktop

1. Ouvre Power BI Desktop
2. `Obtenir des données` → `Texte/CSV`
3. Sélectionne `agregats_qualite.csv`
4. Dans l'aperçu : clique `Transformer les données`
5. Vérifie que les types sont corrects :
   - `valeur_moyenne` → Nombre décimal
   - `nb_mesures` → Nombre entier
   - `taux_conformite` → Nombre décimal
6. Clique `Fermer et appliquer`

Répète pour `mesures_clean.csv` et `stats_machine_r.csv`.

---

## Visuels recommandés

### Page 1 — Vue globale

- **Carte KPI** : Taux de conformité moyen global
  - Champ : `taux_conformite` → Moyenne
  - Format : Pourcentage

- **Carte KPI** : Nombre total de lots analysés
  - Champ : `lot_id` → Nombre de valeurs distinctes

- **Graphique en barres** : Conformité par machine
  - Axe X : `machine_id`
  - Axe Y : `taux_conformite` → Moyenne
  - Ligne de référence constante à 0.95 (objectif 95%)

### Page 2 — Détail des mesures

- **Graphique en courbes** : Évolution temporelle
  - Axe X : `mois`
  - Axe Y : `valeur_moyenne` → Moyenne
  - Légende : `machine_id`

- **Tableau** : Top 10 lots hors spécification
  - Colonnes : `lot_id`, `machine_id`, `nb_hors_spec`, `taux_conformite`
  - Filtre : `nb_hors_spec` > 0
  - Tri : `nb_hors_spec` décroissant

### Page 3 — Analyse qualité

- **Nuage de points** : Valeur vs Température
  - Axe X : `temp_moyenne`
  - Axe Y : `valeur_moyenne`
  - Légende : `machine_id`

- **Histogramme** : Distribution des scores qualité
  - Champ : `score_moyen`

---

## Mesures DAX utiles

Copie ces formules dans `Nouvelle mesure` dans Power BI :

```dax
// Taux de conformité global
Taux Conformite = AVERAGE(agregats_qualite[taux_conformite])

// Nombre de lots hors spec
Lots Hors Spec = COUNTROWS(FILTER(agregats_qualite, agregats_qualite[nb_hors_spec] > 0))

// Objectif qualité atteint (OUI/NON)
Objectif Atteint = IF([Taux Conformite] >= 0.95, "OUI", "NON")
```

---

## Actualisation automatique des données

Pour que Power BI recharge les données après chaque run du pipeline :

1. `Accueil` → `Actualiser`
2. Ou planifie une actualisation automatique dans Power BI Service
