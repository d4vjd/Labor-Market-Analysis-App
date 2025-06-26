# 📊 Analiză Economică și Demografică - Regiunea Centru România

---

## 🇷🇴 **PARTEA I - ROMÂNĂ**

### 📋 **Descrierea Proiectului**

Această aplicație oferă o analiză comprehensivă a indicatorilor economici și demografici pentru regiunea Centru a României. Proiectul combină analiza statistică avansată în **R** cu vizualizări interactive moderne în **Python/Streamlit**.

### 🌐 **Accesează Aplicația**

🔗 **[Deschide aplicația aici: https://davidpupaza.streamlit.app/](https://davidpupaza.streamlit.app/)**

---

### 🎯 **Caracteristici Principale**

#### 📈 **Analize Statistice Avansate**
- **Matrice de corelație** pentru indicatorii economici
- **Analiză de regresie panel** pentru date longitudinale
- **Statistici descriptive** complete pentru fiecare indicator
- **Teste de semnificație statistică** (nivel de încredere 99%)

#### 🗺️ **Vizualizări Interactive**
- **Hărți choropleth** pentru analiza spațială
- **Grafice temporale** pentru evoluția indicatorilor
- **Hărți termice** pentru comparații multi-dimensionale
- **Diagrame circulare** pentru structura datelor
- **Scatter plots** pentru analiza corelațiilor

#### 📊 **Indicatori Analizați**
- 💰 **PIB regional pe locuitor**
- 💵 **Câștigul salarial mediu net**
- 👥 **Imigrația definitivă**
- 📉 **Rata șomajului**
- 🏢 **Rata de ocupare a resurselor de muncă**
- 👨‍💼 **Populația activă**
- 🎓 **Numărul de absolvenți**
- 🏛️ **Sectorul public vs. privat**

---

### 🏛️ **Regiunea Centru**

Analiza se concentrează pe cele **6 județe** din regiunea Centru:
- 🏔️ **Alba**
- 🏰 **Brașov**
- 🌲 **Covasna**
- ⛰️ **Harghita**
- 🏞️ **Mureș**
- 🏛️ **Sibiu**

---

### 🛠️ **Structura Tehnică**

#### 📁 **Organizarea Proiectului**
```
📂 Licenta/
├── 📊 r/                    # Analize statistice în R
│   ├── matrice_cor.r        # Matrice corelație națională
│   ├── matrice_cor_centru.r # Matrice corelație regiunea Centru
│   ├── regresie_panel.r     # Analiză regresie panel
│   └── regresie_panel_centru.r
├── 🐍 python/               # Aplicația Streamlit
│   ├── main.py              # Aplicația principală
│   └── requirements.txt     # Dependențe Python
├── 📊 date/                 # Baza de date
│   └── data.sqlite          # Date economice și demografice
├── 📈 figuri/               # Grafice și vizualizări
└── 🗺️ date_licenta_tempo/   # Date TEMPO (Eurostat)
```

#### 🔧 **Tehnologii Utilizate**

**R (Analiză Statistică):**
- `RSQLite` - Conectivitate bază de date
- `corrplot` - Matrice de corelație
- `plm` - Modele panel data
- `dplyr` - Manipularea datelor
- `stargazer` - Rapoarte statistice

**Python (Interfață Web):**
- `streamlit` - Framework aplicație web
- `plotly` - Vizualizări interactive
- `geopandas` - Analiză spațială
- `folium` - Hărți interactive
- `pandas` - Procesarea datelor
- `scipy` - Analize statistice

---

### 🚀 **Instalare și Rulare**

#### **Cerințe Preliminare**
- Python 3.8+
- R 4.0+
- SQLite

#### **Pași de Instalare**

1. **Clonează repository-ul:**
```bash
git clone [repository-url]
cd Licenta
```

2. **Instalează dependențele Python:**
```bash
cd python
pip install -r requirements.txt
```

3. **Rulează aplicația Streamlit:**
```bash
streamlit run main.py
```

4. **Pentru analizele R:**
```bash
cd ../r
Rscript matrice_cor_centru.r
Rscript regresie_panel_centru.r
```

---

### 📊 **Funcționalități Aplicație**

#### 🗺️ **Analiză Spațială**
- Hărți interactive pentru fiecare indicator
- Filtrare pe ani și categorii demografice
- Comparații între regiunea Centru și România
- Animații temporale pentru evoluția indicatorilor

#### 📈 **Analiză Temporală**
- Grafice de evoluție în timp
- Tendințe și pattern-uri sezoniere
- Comparații multi-județ

#### 🔢 **Statistici Descriptive**
- Media, mediana, dispersia
- Teste de normalitate
- Intervale de încredere
- Teste de semnificație

#### 🔗 **Analiză de Corelație**
- Matrice de corelație interactive
- Teste de semnificație pentru corelații
- Identificarea relațiilor între variabile

---

### 📚 **Surse de Date**

- **TEMPO Online** (Institutul Național de Statistică)
- **Eurostat** (Oficiul de Statistică al Uniunii Europene)
- **Date geografice** pentru județele României

---

### 👨‍💻 **Autor**

**David Pupăză**  
📧 Contact: [email]  
🎓 Lucrare de licență - Analiza economică și demografică

---

## 🇬🇧 **PART II - ENGLISH**

### 📋 **Project Description**

This application provides a comprehensive analysis of economic and demographic indicators for Romania's Central region. The project combines advanced statistical analysis in **R** with modern interactive visualizations in **Python/Streamlit**.

### 🌐 **Access the Application**

🔗 **[Open the app here: https://davidpupaza.streamlit.app/](https://davidpupaza.streamlit.app/)**

---

### 🎯 **Key Features**

#### 📈 **Advanced Statistical Analysis**
- **Correlation matrices** for economic indicators
- **Panel regression analysis** for longitudinal data
- **Comprehensive descriptive statistics** for each indicator
- **Statistical significance tests** (99% confidence level)

#### 🗺️ **Interactive Visualizations**
- **Choropleth maps** for spatial analysis
- **Time series charts** for indicator evolution
- **Heat maps** for multi-dimensional comparisons
- **Pie charts** for data structure analysis
- **Scatter plots** for correlation analysis

#### 📊 **Analyzed Indicators**
- 💰 **Regional GDP per capita**
- 💵 **Average net salary**
- 👥 **Definitive immigration**
- 📉 **Unemployment rate**
- 🏢 **Labor resource employment rate**
- 👨‍💼 **Active population**
- 🎓 **Number of graduates**
- 🏛️ **Public vs. private sector**

---

### 🏛️ **Central Region**

The analysis focuses on the **6 counties** of the Central region:
- 🏔️ **Alba**
- 🏰 **Brașov**
- 🌲 **Covasna**
- ⛰️ **Harghita**
- 🏞️ **Mureș**
- 🏛️ **Sibiu**

---

### 🛠️ **Technical Structure**

#### 📁 **Project Organization**
```
📂 Licenta/
├── 📊 r/                    # Statistical analysis in R
│   ├── matrice_cor.r        # National correlation matrix
│   ├── matrice_cor_centru.r # Central region correlation matrix
│   ├── regresie_panel.r     # Panel regression analysis
│   └── regresie_panel_centru.r
├── 🐍 python/               # Streamlit application
│   ├── main.py              # Main application
│   └── requirements.txt     # Python dependencies
├── 📊 date/                 # Database
│   └── data.sqlite          # Economic and demographic data
├── 📈 figuri/               # Charts and visualizations
└── 🗺️ date_licenta_tempo/   # TEMPO data (Eurostat)
```

#### 🔧 **Technologies Used**

**R (Statistical Analysis):**
- `RSQLite` - Database connectivity
- `corrplot` - Correlation matrices
- `plm` - Panel data models
- `dplyr` - Data manipulation
- `stargazer` - Statistical reports

**Python (Web Interface):**
- `streamlit` - Web application framework
- `plotly` - Interactive visualizations
- `geopandas` - Spatial analysis
- `folium` - Interactive maps
- `pandas` - Data processing
- `scipy` - Statistical analysis

---

### 🚀 **Installation and Setup**

#### **Prerequisites**
- Python 3.8+
- R 4.0+
- SQLite

#### **Installation Steps**

1. **Clone the repository:**
```bash
git clone [repository-url]
cd Licenta
```

2. **Install Python dependencies:**
```bash
cd python
pip install -r requirements.txt
```

3. **Run the Streamlit application:**
```bash
streamlit run main.py
```

4. **For R analyses:**
```bash
cd ../r
Rscript matrice_cor_centru.r
Rscript regresie_panel_centru.r
```

---

### 📊 **Application Features**

#### 🗺️ **Spatial Analysis**
- Interactive maps for each indicator
- Filtering by years and demographic categories
- Comparisons between Central region and Romania
- Temporal animations for indicator evolution

#### 📈 **Temporal Analysis**
- Time evolution charts
- Trends and seasonal patterns
- Multi-county comparisons

#### 🔢 **Descriptive Statistics**
- Mean, median, variance
- Normality tests
- Confidence intervals
- Significance tests

#### 🔗 **Correlation Analysis**
- Interactive correlation matrices
- Significance tests for correlations
- Variable relationship identification

---

### 📚 **Data Sources**

- **TEMPO Online** (National Institute of Statistics)
- **Eurostat** (Statistical Office of the European Union)
- **Geographic data** for Romanian counties

---

### 👨‍💻 **Author**

**David Pupăză**  
📧 Contact: [email]  
🎓 Bachelor's thesis - Economic and demographic analysis

---

### 📄 **License**

This project is developed for academic purposes as part of a bachelor's thesis.

---

**⭐ If you find this project useful, please consider giving it a star!**

---

*Last updated: January 2025*