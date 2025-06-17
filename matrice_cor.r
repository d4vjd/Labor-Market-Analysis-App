# Instalare librarii necesare
install.packages("RSQLite")
install.packages("corrplot")
install.packages("dplyr")

# Incarcarea librariilor necesare
library(RSQLite)
library(corrplot)
library(dplyr)

# Conectarea la baza de date SQLite
con <- dbConnect(SQLite(), "data.sqlite")

# Functie pentru calcularea mediei pe anii disponibili pentru fiecare judet
calculate_mean_by_county <- function(data, exclude_cols = c("ID", "Judete", "Sexe", "Niveluri de educatie")) {
  # Identifica coloanele cu ani
  year_cols <- names(data)[grepl("Anul", names(data))]
  
  # Calculeaza media pentru fiecare judet
  data %>%
    group_by(Judete) %>%
    summarise(across(all_of(year_cols), ~ mean(as.numeric(.), na.rm = TRUE)), .groups = 'drop') %>%
    mutate(mean_value = rowMeans(select(., all_of(year_cols)), na.rm = TRUE)) %>%
    select(Judete, mean_value)
}

# Extragerea si procesarea datelor pentru fiecare variabila

# 1. PIB - Produsul intern brut regional pe locuitor
pib_data <- dbGetQuery(con, "SELECT * FROM PIB")
pib_mean <- calculate_mean_by_county(pib_data)
names(pib_mean)[2] <- "PIB"

# 2. Salariu - Castigul salarial nominal mediu net lunar
salariu_data <- dbGetQuery(con, "SELECT * FROM Salariu")
salariu_mean <- calculate_mean_by_county(salariu_data)
names(salariu_mean)[2] <- "Salariu"

# 3. Imigranti - Imigranti definitivi pe judete
imigranti_data <- dbGetQuery(con, "SELECT * FROM Imigranti")
imigranti_mean <- calculate_mean_by_county(imigranti_data)
names(imigranti_mean)[2] <- "Imigranti"

# 4. Somaj - Rata somajului (procente)
somaj_data <- dbGetQuery(con, "SELECT * FROM Somaj")
somaj_mean <- calculate_mean_by_county(somaj_data)
names(somaj_mean)[2] <- "Rata_Somaj"

# 5. Resurse - Rata de ocupare a resurselor de munca (procente)
resurse_data <- dbGetQuery(con, "SELECT * FROM Resurse")
resurse_mean <- calculate_mean_by_county(resurse_data)
names(resurse_mean)[2] <- "Rata_Ocupare"

# 6. PopActiva - Populatia activa civila (mii persoane)
popactiva_data <- dbGetQuery(con, "SELECT * FROM PopActiva")
popactiva_mean <- calculate_mean_by_county(popactiva_data)
names(popactiva_mean)[2] <- "Pop_Activa"

# Combinarea tuturor datelor intr-un singur data frame
combined_data <- pib_mean %>%
  full_join(salariu_mean, by = "Judete") %>%
  full_join(imigranti_mean, by = "Judete") %>%
  full_join(somaj_mean, by = "Judete") %>%
  full_join(resurse_mean, by = "Judete") %>%
  full_join(popactiva_mean, by = "Judete")

# Eliminarea randurilor cu valori lipsa
combined_data <- combined_data[complete.cases(combined_data), ]

# Standardizarea datelor (z-score normalization)
# Excludem coloana cu judetele din standardizare
numeric_data <- combined_data[, -1]  # Excludem prima coloana (Judete)
standardized_data <- scale(numeric_data)

# Calcularea matricei de corelatie
correlation_matrix <- cor(standardized_data, use = "complete.obs")

# Crearea graficului de corelatie similar cu cel din imagine
corrplot(correlation_matrix, 
         method = "color",           # Foloseste culori pentru reprezentare
         type = "full",              # Afiseaza matricea completa
         order = "original",         # Pastreaza ordinea originala
         tl.col = "red",            # Culoarea etichetelor - rosu
         tl.srt = 45,               # Rotatia etichetelor la 45 grade
         tl.cex = 0.8,              # Dimensiunea textului etichetelor
         cl.cex = 0.8,              # Dimensiunea scalei de culori
         addCoef.col = "black",     # Culoarea coeficientilor
         number.cex = 0.7,          # Dimensiunea numerelor
         col = colorRampPalette(c("darkred", "white", "darkblue"))(200),  # Paleta de culori
         title = "Matricea de Corelatie - Indicatori Economici Standardizati",
         mar = c(0,0,2,0))          # Marginile graficului

# Afisarea matricei de corelatie in consola cu valori rotunjite
print("Matricea de corelatie (valori rotunjite la 2 zecimale):")
print(round(correlation_matrix, 2))

# Inchiderea conexiunii la baza de date
dbDisconnect(con)

# Informatii despre standardizare
cat("\nDatele au fost standardizate folosind z-score normalization.\n")
cat("Formula: (x - mean(x)) / sd(x)\n")
cat("Aceasta asigura ca toate variabilele au media 0 si deviatia standard 1.\n")