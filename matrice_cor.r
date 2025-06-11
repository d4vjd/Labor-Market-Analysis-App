# Instalare librarii necesar
install.packages("RSQLite")
install.packages("corrplot")
install.packages("dplyr")

# Încărcarea librăriilor necesare
library(RSQLite)
library(corrplot)
library(dplyr)

# Conectarea la baza de date SQLite
con <- dbConnect(SQLite(), "data.sqlite")

# Funcție pentru calcularea mediei pe anii disponibili pentru fiecare județ
calculate_mean_by_county <- function(data, exclude_cols = c("ID", "Judete", "Sexe", "Niveluri de educatie")) {
  # Identifică coloanele cu ani
  year_cols <- names(data)[grepl("Anul", names(data))]
  
  # Calculează media pentru fiecare județ
  data %>%
    group_by(Judete) %>%
    summarise(across(all_of(year_cols), ~ mean(as.numeric(.), na.rm = TRUE)), .groups = 'drop') %>%
    mutate(mean_value = rowMeans(select(., all_of(year_cols)), na.rm = TRUE)) %>%
    select(Judete, mean_value)
}

# Extragerea și procesarea datelor pentru fiecare variabilă

# 1. PIB - Produsul intern brut regional pe locuitor
pib_data <- dbGetQuery(con, "SELECT * FROM PIB")
pib_mean <- calculate_mean_by_county(pib_data)
names(pib_mean)[2] <- "PIB"

# 2. Salariu - Câștigul salarial nominal mediu net lunar
salariu_data <- dbGetQuery(con, "SELECT * FROM Salariu")
salariu_mean <- calculate_mean_by_county(salariu_data)
names(salariu_mean)[2] <- "Salariu"

# 3. Imigranti - Imigranti definitivi pe județe
imigranti_data <- dbGetQuery(con, "SELECT * FROM Imigranti")
imigranti_mean <- calculate_mean_by_county(imigranti_data)
names(imigranti_mean)[2] <- "Imigranti"

# 4. Somaj - Rata șomajului (procente)
somaj_data <- dbGetQuery(con, "SELECT * FROM Somaj")
somaj_mean <- calculate_mean_by_county(somaj_data)
names(somaj_mean)[2] <- "Rata_Somaj"

# 5. Resurse - Rata de ocupare a resurselor de muncă (procente)
resurse_data <- dbGetQuery(con, "SELECT * FROM Resurse")
resurse_mean <- calculate_mean_by_county(resurse_data)
names(resurse_mean)[2] <- "Rata_Ocupare"

# 6. PopActiva - Populația activă civilă (mii persoane)
popactiva_data <- dbGetQuery(con, "SELECT * FROM PopActiva")
popactiva_mean <- calculate_mean_by_county(popactiva_data)
names(popactiva_mean)[2] <- "Pop_Activa"

# Combinarea tuturor datelor într-un singur data frame
combined_data <- pib_mean %>%
  full_join(salariu_mean, by = "Judete") %>%
  full_join(imigranti_mean, by = "Judete") %>%
  full_join(somaj_mean, by = "Judete") %>%
  full_join(resurse_mean, by = "Judete") %>%
  full_join(popactiva_mean, by = "Judete")

# Eliminarea rândurilor cu valori lipsă
combined_data <- combined_data[complete.cases(combined_data), ]

# Standardizarea datelor (z-score normalization)
# Excludem coloana cu județele din standardizare
numeric_data <- combined_data[, -1]  # Excludem prima coloană (Judete)
standardized_data <- scale(numeric_data)

# Calcularea matricei de corelație
correlation_matrix <- cor(standardized_data, use = "complete.obs")

# Crearea graficului de corelație similar cu cel din imagine
corrplot(correlation_matrix, 
         method = "color",           # Folosește culori pentru reprezentare
         type = "full",              # Afișează matricea completă
         order = "original",         # Păstrează ordinea originală
         tl.col = "red",            # Culoarea etichetelor - roșu
         tl.srt = 45,               # Rotația etichetelor la 45 grade
         tl.cex = 0.8,              # Dimensiunea textului etichetelor
         cl.cex = 0.8,              # Dimensiunea scalei de culori
         addCoef.col = "black",     # Culoarea coeficienților
         number.cex = 0.7,          # Dimensiunea numerelor
         col = colorRampPalette(c("darkred", "white", "darkblue"))(200),  # Paleta de culori
         title = "Matricea de Corelație - Indicatori Economici Standardizați",
         mar = c(0,0,2,0))          # Marginile graficului

# Afișarea matricei de corelație în consolă cu valori rotunjite
print("Matricea de corelație (valori rotunjite la 2 zecimale):")
print(round(correlation_matrix, 2))

# Închiderea conexiunii la baza de date
dbDisconnect(con)

# Informații despre standardizare
cat("\nDatele au fost standardizate folosind z-score normalization.\n")
cat("Formula: (x - mean(x)) / sd(x)\n")
cat("Aceasta asigură că toate variabilele au media 0 și deviația standard 1.\n")