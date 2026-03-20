# =============================================================
# analyse_qualite.R
# Analyse statistique des données de qualité production
# Génère des graphiques exportés pour Power BI
# =============================================================

# ── Installation automatique des packages manquants ──────────
# Cette fonction vérifie si un package est installé
# et l'installe automatiquement si ce n'est pas le cas
install_if_missing <- function(pkg) {
  if (!require(pkg, character.only = TRUE, quietly = TRUE)) {
    install.packages(pkg, repos = "https://cran.r-project.org")
    library(pkg, character.only = TRUE)
  }
}

# Packages nécessaires
install_if_missing("dplyr")    # manipulation de données (équivalent pandas)
install_if_missing("ggplot2")  # visualisation (équivalent matplotlib)
install_if_missing("readr")    # lecture de fichiers CSV
install_if_missing("tidyr")    # mise en forme des données

# Chargement des librairies
library(dplyr)
library(ggplot2)
library(readr)
library(tidyr)

# Création du dossier pour les exports
dir.create("data/exports/r_plots", recursive = TRUE, showWarnings = FALSE)

cat("=== Démarrage de l'analyse R ===\n")


# =============================================================
# ÉTAPE 1 — LECTURE DES DONNÉES
# Équivalent Python : pd.read_csv("...", sep=";")
# =============================================================

# read_delim() lit un CSV avec un séparateur personnalisé
# col_types = NULL : R détecte automatiquement les types
df <- read_delim(
  "data/processed/mesures_clean.csv",
  delim = ";",
  col_types = NULL,
  show_col_types = FALSE
)

cat(sprintf("Données chargées : %d lignes, %d colonnes\n",
            nrow(df), ncol(df)))

# Aperçu des données — équivalent Python : df.head()
cat("\n=== Aperçu des données ===\n")
print(head(df, 5))

# Résumé statistique — équivalent Python : df.describe()
cat("\n=== Résumé statistique ===\n")
print(summary(df$valeur))


# =============================================================
# ÉTAPE 2 — NETTOYAGE ET TRANSFORMATION
# Équivalent Python : df.groupby().agg()
# =============================================================

# Le pipe %>% enchaîne les opérations (comme .groupby().agg() en pandas)
# filter()   = df[df["col"] == valeur]
# group_by() = df.groupby("col")
# summarise() = .agg(...)
# arrange()  = df.sort_values()

# Statistiques par machine
stats_machine <- df %>%
  group_by(machine_id) %>%
  summarise(
    nb_mesures     = n(),                      # count()
    valeur_moyenne = mean(valeur, na.rm = TRUE),
    valeur_max     = max(valeur, na.rm = TRUE),
    ecart_type     = sd(valeur, na.rm = TRUE),
    taux_hors_spec = mean(hors_spec, na.rm = TRUE)
  ) %>%
  arrange(desc(valeur_moyenne))                # sort_values() décroissant

cat("\n=== Statistiques par machine ===\n")
print(stats_machine)


# Statistiques par type de mesure
stats_type <- df %>%
  group_by(type_mesure) %>%
  summarise(
    nb_mesures     = n(),
    valeur_moyenne = round(mean(valeur, na.rm = TRUE), 3),
    taux_hors_spec = round(mean(hors_spec, na.rm = TRUE), 3)
  )

cat("\n=== Statistiques par type de mesure ===\n")
print(stats_type)


# =============================================================
# ÉTAPE 3 — VISUALISATIONS
# Exportées en PNG pour intégration dans Power BI
# =============================================================

# ── Graphique 1 : Distribution des valeurs par machine ────────
# geom_boxplot() = boîte à moustaches
# facet_wrap()   = divise en sous-graphiques par type de mesure
p1 <- ggplot(df, aes(x = machine_id, y = valeur, fill = machine_id)) +
  geom_boxplot(alpha = 0.7, outlier.color = "red") +
  facet_wrap(~type_mesure) +
  labs(
    title    = "Distribution des valeurs par machine et type de mesure",
    subtitle = "Points rouges = valeurs aberrantes détectées",
    x        = "Machine",
    y        = "Valeur mesurée",
    fill     = "Machine"
  ) +
  theme_minimal() +
  theme(legend.position = "bottom")

# Sauvegarde du graphique en PNG
ggsave(
  "data/exports/r_plots/distribution_par_machine.png",
  plot   = p1,
  width  = 10,
  height = 6,
  dpi    = 150
)
cat("Graphique 1 sauvegardé : distribution_par_machine.png\n")


# ── Graphique 2 : Taux de conformité par machine ─────────────
# geom_bar(stat="identity") = graphique en barres avec valeurs réelles
# geom_hline() = ligne horizontale de référence
p2 <- ggplot(stats_machine,
             aes(x = machine_id,
                 y = (1 - taux_hors_spec) * 100,
                 fill = machine_id)) +
  geom_bar(stat = "identity", alpha = 0.8) +
  geom_hline(yintercept = 95, linetype = "dashed",
             color = "red", linewidth = 1) +
  labs(
    title    = "Taux de conformité par machine (%)",
    subtitle = "Ligne rouge = objectif qualité 95%",
    x        = "Machine",
    y        = "Taux de conformité (%)",
    fill     = "Machine"
  ) +
  ylim(0, 100) +
  theme_minimal()

ggsave(
  "data/exports/r_plots/taux_conformite.png",
  plot   = p2,
  width  = 8,
  height = 5,
  dpi    = 150
)
cat("Graphique 2 sauvegardé : taux_conformite.png\n")


# ── Graphique 3 : Évolution temporelle ───────────────────────
# On calcule la moyenne quotidienne pour voir les tendances
evolution <- df %>%
  group_by(date_mesure, machine_id) %>%
  summarise(
    valeur_moyenne = mean(valeur, na.rm = TRUE),
    .groups = "drop"
  )

p3 <- ggplot(evolution,
             aes(x = as.Date(date_mesure),
                 y = valeur_moyenne,
                 color = machine_id)) +
  geom_line(alpha = 0.7) +
  geom_smooth(method = "loess", se = FALSE, linewidth = 1.2) +
  labs(
    title  = "Évolution de la valeur moyenne par machine",
    x      = "Date",
    y      = "Valeur moyenne",
    color  = "Machine"
  ) +
  theme_minimal()

ggsave(
  "data/exports/r_plots/evolution_temporelle.png",
  plot   = p3,
  width  = 10,
  height = 5,
  dpi    = 150
)
cat("Graphique 3 sauvegardé : evolution_temporelle.png\n")


# =============================================================
# ÉTAPE 4 — EXPORT DES RÉSULTATS R
# Pour intégration dans Power BI
# =============================================================

# write_delim() = équivalent Python : df.to_csv(sep=";", index=False)
write_delim(
  stats_machine,
  "data/exports/stats_machine_r.csv",
  delim = ";"
)

write_delim(
  stats_type,
  "data/exports/stats_type_mesure_r.csv",
  delim = ";"
)

cat("\n=== Fichiers CSV exportés pour Power BI ===\n")
cat("  - data/exports/stats_machine_r.csv\n")
cat("  - data/exports/stats_type_mesure_r.csv\n")
cat("  - data/exports/r_plots/*.png\n")
cat("\n=== Analyse R terminée ===\n")
