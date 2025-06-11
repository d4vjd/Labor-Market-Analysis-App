# Instalare librarii necesare
if (!require("RSQLite")) install.packages("RSQLite")
if (!require("plm")) install.packages("plm")
if (!require("dplyr")) install.packages("dplyr")
if (!require("tidyr")) install.packages("tidyr")
if (!require("stargazer")) install.packages("stargazer")

# Încărcarea librăriilor necesare
library(RSQLite)
library(plm)
library(dplyr)
library(tidyr)

# Conectarea la baza de date SQLite
con <- dbConnect(SQLite(), "data.sqlite")

# Funcție pentru restructurarea datelor în format panel (long format)
prepare_panel_data <- function(data, value_name, exclude_cols = c("ID", "Sexe", "Niveluri de educatie")) {
  # Verifică dacă există coloana "Sexe" și filtrează pentru "Total"
  if("Sexe" %in% names(data)) {
    # Verifică valorile unice din coloana Sexe pentru debugging
    unique_sexe <- unique(data$Sexe)
    cat("Valori unice în coloana Sexe pentru", value_name, ":", paste(unique_sexe, collapse = ", "), "\n")
    
    # Filtrează pentru "Total" (case insensitive și cu variații posibile)
    data <- data %>%
      filter(grepl("total|Total|TOTAL", Sexe, ignore.case = TRUE))
    
    cat("Numărul de rânduri după filtrarea pentru Total:", nrow(data), "\n")
  }
  
  # Identifică coloanele cu ani
  year_cols <- names(data)[grepl("Anul", names(data))]
  
  # Selectează doar coloanele necesare
  keep_cols <- c("Judete", year_cols)
  data_clean <- data[, names(data) %in% keep_cols]
  
  # Grupează pe județe și calculează media dacă există mai multe înregistrări
  data_grouped <- data_clean %>%
    group_by(Judete) %>%
    summarise(across(all_of(year_cols), ~ mean(as.numeric(.), na.rm = TRUE)), .groups = 'drop')
  
  # Transformă în format long
  data_long <- data_grouped %>%
    pivot_longer(cols = all_of(year_cols), 
                 names_to = "An", 
                 values_to = value_name) %>%
    mutate(An = as.numeric(gsub("Anul ", "", An)))
  
  return(data_long)
}

# Redirecționarea output-ului către fișier
sink("rezultate_panel_data.txt")

# Extragerea și procesarea datelor pentru fiecare variabilă
cat("Procesarea datelor pentru Salariu...\n")
salariu_data <- dbGetQuery(con, "SELECT * FROM Salariu")
salariu_panel <- prepare_panel_data(salariu_data, "Salariu")

cat("Procesarea datelor pentru Imigranti...\n")
imigranti_data <- dbGetQuery(con, "SELECT * FROM Imigranti")
imigranti_panel <- prepare_panel_data(imigranti_data, "Imigranti")

cat("Procesarea datelor pentru Rata Somaj...\n")
somaj_data <- dbGetQuery(con, "SELECT * FROM Somaj")
somaj_panel <- prepare_panel_data(somaj_data, "Rata_Somaj")

cat("Procesarea datelor pentru Rata Ocupare...\n")
resurse_data <- dbGetQuery(con, "SELECT * FROM Resurse")
resurse_panel <- prepare_panel_data(resurse_data, "Rata_Ocupare")

cat("Procesarea datelor pentru Populatia Activa...\n")
popactiva_data <- dbGetQuery(con, "SELECT * FROM PopActiva")
popactiva_panel <- prepare_panel_data(popactiva_data, "Pop_Activa")

# Combinarea tuturor datelor într-un singur panel dataset
cat("Combinarea datelor...\n")
panel_data <- salariu_panel %>%
  full_join(imigranti_panel, by = c("Judete", "An")) %>%
  full_join(somaj_panel, by = c("Judete", "An")) %>%
  full_join(resurse_panel, by = c("Judete", "An")) %>%
  full_join(popactiva_panel, by = c("Judete", "An"))

# Eliminarea rândurilor cu valori lipsă
panel_data <- panel_data[complete.cases(panel_data), ]

# STANDARDIZAREA DATELOR
cat("Standardizarea datelor...\n")
non_numeric_vars <- c("Judete", "An")
numeric_vars <- setdiff(names(panel_data), non_numeric_vars)

panel_data_standardized <- panel_data
panel_data_standardized[numeric_vars] <- scale(panel_data[numeric_vars])

# Verificarea structurii datelor
cat("Structura datelor panel:\n")
str(panel_data_standardized)
cat("\nPrimele 10 rânduri:\n")
print(head(panel_data_standardized, 10))

# Definirea structurii panel data pentru plm
cat("Definirea structurii panel data...\n")
panel_pdata <- pdata.frame(panel_data_standardized, index = c("Judete", "An"))

# Verificarea balanței panelului
cat("Informații despre panelul de date:\n")
print(pdim(panel_pdata))

# Model 1: Fixed Effects (Within Model)
cat("\n=== MODELUL 1: FIXED EFFECTS ===\n")
fixed_model <- plm(Salariu ~ Imigranti + Rata_Somaj + Rata_Ocupare + Pop_Activa, 
                   data = panel_pdata, 
                   model = "within")

print(summary(fixed_model))

# Model 2: Random Effects Model
cat("\n=== MODELUL 2: RANDOM EFFECTS ===\n")
random_model <- plm(Salariu ~ Imigranti + Rata_Somaj + Rata_Ocupare + Pop_Activa, 
                    data = panel_pdata, 
                    model = "random")

print(summary(random_model))

# COMPARAREA MODELELOR
cat("\n")
cat(paste(rep("=", 60), collapse = ""))
cat("\n")
cat("COMPARAREA MODELELOR\n")
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

# Oprirea redirecționării
sink()

# Închiderea conexiunii la baza de date
dbDisconnect(con)

cat("Analiza panel data completă! Rezultatele au fost salvate în 'rezultate_panel_data.txt'\n")