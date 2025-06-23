# Instalare librarii necesare
if (!require("RSQLite")) install.packages("RSQLite")
if (!require("plm")) install.packages("plm")
if (!require("dplyr")) install.packages("dplyr")
if (!require("tidyr")) install.packages("tidyr")
if (!require("stargazer")) install.packages("stargazer")

# Incarcarea librariilor necesare
library(RSQLite)
library(plm)
library(dplyr)
library(tidyr)

# Conectarea la baza de date SQLite
con <- dbConnect(SQLite(), "data.sqlite")

# Definirea judetelor din regiunea Centru
judete_centru <- c("Alba", "Brasov", "Sibiu", "Mures", "Covasna", "Harghita",
                   "Brașov", "Mureş", "Mureș", "ALBA", "BRASOV", "SIBIU", 
                   "MURES", "COVASNA", "HARGHITA")

# Functie pentru restructurarea datelor in format panel (long format) - doar regiunea Centru
prepare_panel_data_centru <- function(data, value_name, exclude_cols = c("ID", "Sexe", "Niveluri de educatie")) {
  # Verifica daca exista coloana "Sexe" si filtreaza pentru "Total"
  if("Sexe" %in% names(data)) {
    # Filtreaza pentru "Total" (case insensitive si cu variatii posibile)
    data <- data %>%
      filter(grepl("total|Total|TOTAL", Sexe, ignore.case = TRUE))
  }
  
  # Filtreaza pentru judetele din regiunea Centru
  data <- data %>%
    filter(Judete %in% judete_centru | 
           grepl("Alba|Brasov|Brașov|Sibiu|Mures|Mureş|Mureș|Covasna|Harghita", 
                 Judete, ignore.case = TRUE))
  
  # Identifica coloanele cu ani
  year_cols <- names(data)[grepl("Anul", names(data))]
  
  # Selecteaza doar coloanele necesare
  keep_cols <- c("Judete", year_cols)
  data_clean <- data[, names(data) %in% keep_cols]
  
  # Grupeaza pe judete si calculeaza media daca exista mai multe inregistrari
  data_grouped <- data_clean %>%
    group_by(Judete) %>%
    summarise(across(all_of(year_cols), ~ mean(as.numeric(.), na.rm = TRUE)), .groups = 'drop')
  
  # Transforma in format long
  data_long <- data_grouped %>%
    pivot_longer(cols = all_of(year_cols), 
                 names_to = "An", 
                 values_to = value_name) %>%
    mutate(An = as.numeric(gsub("Anul ", "", An)))
  
  return(data_long)
}

# Redirectionarea output-ului catre fisier
sink("rezultate_panel_data_centru.txt")

cat("ANALIZA PANEL DATA - REGIUNEA CENTRU\n")
cat("Judete incluse: Alba, Brasov, Sibiu, Mures, Covasna, Harghita\n")
cat(paste(rep("=", 60), collapse = ""))
cat("\n\n")

# Extragerea si procesarea datelor pentru fiecare variabila
salariu_data <- dbGetQuery(con, "SELECT * FROM Salariu")
salariu_panel <- prepare_panel_data_centru(salariu_data, "Salariu")

imigranti_data <- dbGetQuery(con, "SELECT * FROM Imigranti")
imigranti_panel <- prepare_panel_data_centru(imigranti_data, "Imigranti")

somaj_data <- dbGetQuery(con, "SELECT * FROM Somaj")
somaj_panel <- prepare_panel_data_centru(somaj_data, "Rata_Somaj")

resurse_data <- dbGetQuery(con, "SELECT * FROM Resurse")
resurse_panel <- prepare_panel_data_centru(resurse_data, "Rata_Ocupare")

popactiva_data <- dbGetQuery(con, "SELECT * FROM PopActiva")
popactiva_panel <- prepare_panel_data_centru(popactiva_data, "Pop_Activa")

# Combinarea tuturor datelor intr-un singur panel dataset
cat("Combinarea datelor pentru regiunea Centru...\n")
panel_data <- salariu_panel %>%
  full_join(imigranti_panel, by = c("Judete", "An")) %>%
  full_join(somaj_panel, by = c("Judete", "An")) %>%
  full_join(resurse_panel, by = c("Judete", "An")) %>%
  full_join(popactiva_panel, by = c("Judete", "An"))

# Eliminarea randurilor cu valori lipsa
panel_data <- panel_data[complete.cases(panel_data), ]

# Afisarea judetelor incluse in analiza
cat("Judete din regiunea Centru incluse in analiza:\n")
print(unique(panel_data$Judete))
cat("Numar total de observatii:", nrow(panel_data), "\n")

# STANDARDIZAREA DATELOR
cat("Standardizarea datelor folosind functia scale()...\n")
non_numeric_vars <- c("Judete", "An")
numeric_vars <- setdiff(names(panel_data), non_numeric_vars)

panel_data_standardized <- panel_data
panel_data_standardized[numeric_vars] <- scale(panel_data[numeric_vars])

# Verificarea structurii datelor
cat("Structura datelor panel pentru regiunea Centru:\n")
str(panel_data_standardized)
cat("\nPrimele 10 randuri:\n")
print(head(panel_data_standardized, 10))

# Definirea structurii panel data pentru plm
cat("Definirea structurii panel data...\n")
panel_pdata <- pdata.frame(panel_data_standardized, index = c("Judete", "An"))

# Verificarea balantei panelului
cat("Informatii despre panelul de date pentru regiunea Centru:\n")
print(pdim(panel_pdata))

# Model 1: Fixed Effects (Within Model)
cat("\n=== MODELUL 1: FIXED EFFECTS (REGIUNEA CENTRU) ===\n")
fixed_model <- plm(Salariu ~ Imigranti + Rata_Somaj + Rata_Ocupare + Pop_Activa, 
                   data = panel_pdata, 
                   model = "within")

print(summary(fixed_model))

# Model 2: Random Effects Model
cat("\n=== MODELUL 2: RANDOM EFFECTS (REGIUNEA CENTRU) ===\n")
random_model <- plm(Salariu ~ Imigranti + Rata_Somaj + Rata_Ocupare + Pop_Activa, 
                    data = panel_pdata, 
                    model = "random")

print(summary(random_model))

# COMPARAREA MODELELOR
cat("\n")
cat(paste(rep("=", 60), collapse = ""))
cat("\n")
cat("COMPARAREA MODELELOR - REGIUNEA CENTRU\n")
cat(paste(rep("=", 60), collapse = ""))
cat("\n")

# 1. Hausman Test (Fixed vs Random Effects)
cat("\n1. HAUSMAN TEST (Fixed Effects vs Random Effects):\n")
cat("H0: Random Effects model este preferat\n")
cat("H1: Fixed Effects model este preferat\n")
hausman_test <- phtest(fixed_model, random_model)
print(hausman_test)

if(hausman_test$p.value < 0.05) {
  cat("Rezultat: Fixed Effects model este preferat (p < 0.05)\n")
} else {
  cat("Rezultat: Random Effects model este preferat (p >= 0.05)\n")
}

# 2. Compararea R-squared
cat("\n2. COMPARAREA R-SQUARED:\n")
fixed_r2 <- summary(fixed_model)$r.squared
random_r2 <- summary(random_model)$r.squared

cat("Fixed Effects R-squared:", round(fixed_r2[1], 4), "\n")
cat("Random Effects R-squared:", round(random_r2[1], 4), "\n")

# Oprirea redirectionarii
sink()

# Inchiderea conexiunii la baza de date
dbDisconnect(con)

cat("Analiza panel data pentru regiunea Centru completa! Rezultatele au fost salvate in 'rezultate_panel_data_centru.txt'\n")