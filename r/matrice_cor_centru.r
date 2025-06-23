install.packages("RSQLite")
install.packages("corrplot")
install.packages("dplyr")

library(RSQLite)
library(corrplot)
library(dplyr)

# Conectare la baza de date SQLite
con <- dbConnect(SQLite(), "data.sqlite")

# Definirea judetelor din regiunea Centru
judete_centru <- c("Alba", "Brasov", "Sibiu", "Mures", "Covasna", "Harghita",
                   "Brașov", "Mureş", "Mureș", "ALBA", "BRASOV", "SIBIU", 
                   "MURES", "COVASNA", "HARGHITA")

# Functie pentru media valorilor pe fiecare judet din regiunea Centru
calculate_mean_by_county_centru <- function(data) {
  year_cols <- names(data)[grepl("Anul", names(data))]
  data %>%
    filter(!grepl("total", Judete, ignore.case = TRUE)) %>%
    filter(Judete %in% judete_centru | 
           grepl("Alba|Brasov|Brașov|Sibiu|Mures|Mureş|Mureș|Covasna|Harghita", 
                 Judete, ignore.case = TRUE)) %>%
    group_by(Judete) %>%
    summarise(
      across(all_of(year_cols), ~ mean(as.numeric(.), na.rm = TRUE)),
      .groups = 'drop'
    ) %>%
    mutate(
      mean_value = rowMeans(across(all_of(year_cols)), na.rm = TRUE)
    ) %>%
    select(Judete, mean_value)
}

# Extractie si procesare date pentru fiecare indicator (doar regiunea Centru)
pib_mean     <- dbGetQuery(con, "SELECT * FROM PIB")       %>% calculate_mean_by_county_centru() %>% rename(PIB          = mean_value)
sal_mean     <- dbGetQuery(con, "SELECT * FROM Salariu")   %>% calculate_mean_by_county_centru() %>% rename(Salariu      = mean_value)
imigr_mean   <- dbGetQuery(con, "SELECT * FROM Imigranti") %>% calculate_mean_by_county_centru() %>% rename(Imigranti    = mean_value)
somaj_mean   <- dbGetQuery(con, "SELECT * FROM Somaj")     %>% calculate_mean_by_county_centru() %>% rename(Rata_Somaj   = mean_value)
resurse_mean <- dbGetQuery(con, "SELECT * FROM Resurse")   %>% calculate_mean_by_county_centru() %>% rename(Rata_Ocupare = mean_value)
pop_mean     <- dbGetQuery(con, "SELECT * FROM PopActiva") %>% calculate_mean_by_county_centru() %>% rename(Pop_Activa   = mean_value)

# Verificare judete gasite
cat("Judete din regiunea Centru gasite in date:\n")
print(unique(c(pib_mean$Judete, sal_mean$Judete, imigr_mean$Judete, 
               somaj_mean$Judete, resurse_mean$Judete, pop_mean$Judete)))

# Combinare si curatare
combined_data <- pib_mean %>%
  full_join(sal_mean,     by = "Judete") %>%
  full_join(imigr_mean,   by = "Judete") %>%
  full_join(somaj_mean,   by = "Judete") %>%
  full_join(resurse_mean, by = "Judete") %>%
  full_join(pop_mean,     by = "Judete") %>%
  filter(complete.cases(.))

cat("\nNumarul de judete din regiunea Centru pentru analiza:", nrow(combined_data), "\n")
print(combined_data$Judete)

# Standardizare si calcul matrice de corelatie
numeric_data       <- combined_data %>% select(-Judete)
standardized_data  <- scale(numeric_data)
correlation_matrix <- cor(standardized_data, use = "complete.obs")

# Functie pentru testarea semnificatiei corelatiei (nivel 99%)
cor.mtest <- function(mat, conf.level = 0.99) {
  mat <- as.matrix(mat)
  n <- ncol(mat)
  p.mat <- matrix(NA, n, n)
  diag(p.mat) <- 0
  for (i in 1:(n-1)) {
    for (j in (i+1):n) {
      test <- cor.test(mat[, i], mat[, j], conf.level = conf.level)
      p.mat[i, j] <- p.mat[j, i] <- test$p.value
    }
  }
  colnames(p.mat) <- colnames(mat)
  rownames(p.mat) <- colnames(mat)
  list(p = p.mat)
}

test_results <- cor.mtest(standardized_data, conf.level = 0.99)

# Matrice de corelatie pentru regiunea Centru
corrplot.mixed(
  correlation_matrix,
  lower       = "number",
  upper       = "circle",
  order       = "AOE",
  tl.col      = "red",
  tl.pos      = "d",
  tl.cex      = 1.2,
  number.cex  = 1.4,
  number.font = 2,
  cl.cex      = 1,
  p.mat       = test_results$p,
  sig.level   = 0.01,
  insig       = "pch",
  pch.cex     = 1.5,
  pch.col     = "black",
  title       = "Matrice de corelatie - Regiunea Centru"
)

dbDisconnect(con)