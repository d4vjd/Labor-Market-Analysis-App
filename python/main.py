import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
import json
import folium
from streamlit_folium import st_folium
from scipy import stats
from scipy.stats import shapiro, kstest, ttest_1samp
import warnings
warnings.filterwarnings('ignore')

@st.cache_data
def incarca_date(nume_tabel):
    # Functie pentru a incarca date din baza SQLite intr-un DataFrame pandas
    conexiune = sqlite3.connect('data.sqlite')
    df = pd.read_sql_query(f"SELECT * FROM {nume_tabel}", conexiune)
    conexiune.close()
    return df

@st.cache_data
def incarca_date_geografice():
    # Incarca datele geografice pentru judetele Romaniei
    try:
        # Incearca sa incarce din fisierul GeoJSON
        with open('ro.json', 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
        return geojson_data, 'geojson'
    except:
        try:
            #
            # Fallback la shapefile
            gdf = gpd.read_file('ro.shp')
            return gdf, 'shapefile'
        except:
            st.error("Nu s-au putut incarca datele geografice. Verifica fisierele ro.json sau ro.shp")
            return None, None

def filtreaza_regiunea_centru_si_romania(df):
    # Filtreaza doar datele pentru judetele din regiunea Centru si pentru Romania
    judete_centru = ['Alba', 'Brasov', 'Covasna', 'Harghita', 'Mures', 'Sibiu', 'Romania']
    return df[df['Judete'].isin(judete_centru)]

def extrage_ani(lista_ani):
    # Preia doar anul din coloanele de forma "Anul YYYY"
    return [col.split()[-1] for col in lista_ani]

def converteste_ani_la_float(df, ani):
    # Converteste valorile din coloanele de ani la tip float (numeric)
    for an in ani:
        df[an] = pd.to_numeric(df[an], errors='coerce')
    return df

# Definitii de culori pentru fiecare judet
JUD_COLORS = {
    "Alba": "#1976D2",
    "Brasov": "#FF9800",
    "Covasna": "#388E3C",
    "Harghita": "#7B1FA2",
    "Mures": "#D32F2F",
    "Sibiu": "#00B8D4",
    "Romania": "#FFFFFF"
}

# Paleta generala de culori fara includerea Romaniei
PALETA = [JUD_COLORS[j] for j in ["Alba", "Brasov", "Covasna", "Harghita", "Mures", "Sibiu"]]

# Dictionar pentru prescurtarea denumirilor activitatilor economice
PRESCURTARI_ACTIVITATI = {
    "C INDUSTRIA PRELUCRATOARE": "Industria prelucratoare",
    "G COMERT CU RIDICATA SI CU AMANUNTUL; REPARAREA AUTOVEHICULELOR SI MOTOCICLETELOR": "Comert si reparatii auto",
    "Q SANATATE SI ASISTENTA SOCIALA": "Sanatate si asistenta sociala",
    "P INVATAMANT": "Invatamant",
    "F CONSTRUCTII": "Constructii",
    "H TRANSPORT SI DEPOZITARE": "Transport si depozitare",
    "O ADMINISTRATIE PUBLICA SI APARARE; ASIGURARI SOCIALE DIN SISTEMUL PUBLIC": "Administratie publica si aparare",
    "A AGRICULTURA, SILVICULTURA SI PESCUIT": "Agricultura si silvicultura",
    "I HOTELURI SI RESTAURANTE": "Hoteluri si restaurante",
    "E DISTRIBUTIA APEI; SALUBRITATE, GESTIONAREA DESEURILOR, ACTIVITATI DE DECONTAMINARE": "Distributia apei si salubritate",
    "M ACTIVITATI PROFESIONALE, STIINTIFICE SI TEHNICE": "Activitati profesionale si tehnice",
    "N ACTIVITATI DE SERVICII ADMINISTRATIVE SI ACTIVITATI DE SERVICII SUPORT": "Servicii administrative si suport",
    "K INTERMEDIERI FINANCIARE SI ASIGURARI": "Finante si asigurari",
    "B INDUSTRIA EXTRACTIVA": "Industria extractiva",
    "D PRODUCTIA SI FURNIZAREA DE ENERGIE ELECTRICA SI TERMICA, GAZE, APA CALDA SI AER COND": "Energie si utilitati",
    "J INFORMATII SI COMUNICATII": "IT si comunicatii",
    "L TRANZACTII IMOBILIARE": "Tranzactii imobiliare",
    "R ACTIVITATI DE SPECTACOLE, CULTURALE SI RECREATIVE": "Spectacole si recreere",
    "S ALTE ACTIVITATI DE SERVICII": "Alte servicii",
    "U ACTIVITATI ALE ORGANIZATIILOR SI ORGANISMELOR EXTRATERESTRE": "Organizatii internationale",
}

# Maparea numelor judetelor pentru concordanta cu datele geografice
MAPARE_JUDETE = {
    'Alba': ['Alba', 'ALBA'],
    'Brasov': ['Brasov', 'BRASOV', 'Brașov', 'BRAȘOV'],
    'Covasna': ['Covasna', 'COVASNA'],
    'Harghita': ['Harghita', 'HARGHITA'],
    'Mures': ['Mures', 'MURES', 'Mureș', 'MUREȘ'],
    'Sibiu': ['Sibiu', 'SIBIU']
}

# Lista cu toate judetele Romaniei pentru mapare
TOATE_JUDETELE = [
    'Alba', 'Arad', 'Arges', 'Bacau', 'Bihor', 'Bistrita-Nasaud', 'Botosani', 'Braila',
    'Brasov', 'Buzau', 'Calarasi', 'Caras-Severin', 'Cluj', 'Constanta', 'Covasna',
    'Dambovita', 'Dolj', 'Galati', 'Giurgiu', 'Gorj', 'Harghita', 'Hunedoara', 'Ialomita',
    'Iasi', 'Ilfov', 'Maramures', 'Mehedinti', 'Mures', 'Neamt', 'Olt', 'Prahova',
    'Salaj', 'Satu Mare', 'Sibiu', 'Suceava', 'Teleorman', 'Timis', 'Tulcea',
    'Valcea', 'Vaslui', 'Vrancea', 'Municipiul Bucuresti'
]

# Coordonatele ajustate ale centrelor judetelor din regiunea Centru
COORDONATE_JUDETE = {
    'Alba': (46.0667, 23.5833),
    'Brasov': (45.6500, 25.6000),
    'Covasna': (45.8667, 26.1833),
    'Harghita': (46.3600, 25.8000),
    'Mures': (46.5500, 24.5667),
    'Sibiu': (45.7833, 24.1500)
}

# Prescurtari pentru judete conform sistemului auto din Romania
PRESCURTARI_JUDETE = {
    'Alba': 'AB',
    'Brasov': 'BV', 
    'Covasna': 'CV',
    'Harghita': 'HR',
    'Mures': 'MS',
    'Sibiu': 'SB'
}

def standardizeaza_nume_judete(nume_judet):
    # Standardizeaza numele judetelor pentru mapare
    for standard, variante in MAPARE_JUDETE.items():
        if nume_judet in variante:
            return standard
    return nume_judet

def prescurteaza_activitate(activitate):
    # Intoarce prescurtarea corespunzatoare activitatii economice
    activitate_norm = activitate.strip().upper()
    for cheie in PRESCURTARI_ACTIVITATI:
        if activitate_norm.startswith(cheie):
            return PRESCURTARI_ACTIVITATI[cheie]
    # Daca nu gaseste, returneaza primele 30 de caractere urmate de "..."
    return activitate[:30] + "..."

def replace_total_with_romania(df):
    # Inlocuieste valorile "TOTAL" sau variante cu "Romania"
    df = df.copy()
    df['Judete'] = df['Judete'].replace({
        'TOTAL': 'Romania',
        'Total': 'Romania',
        'MEDIA ROMÂNIA': 'Romania',
        'Media România': 'Romania'
    })
    return df

def filtreaza_judete_pentru_harta(df, doar_centru=False):
    # Filtreaza judetele pentru afisare pe harta
    if doar_centru:
        judete_target = ['Alba', 'Brasov', 'Covasna', 'Harghita', 'Mures', 'Sibiu']
    else:
        judete_target = TOATE_JUDETELE
    
    return df[df['Judete'].isin(judete_target)]

def analiza_spatiala_choropleth():
    # Analiza spatiala cu choropleth maps pentru Romania
    st.header("Analiza spatiala - Choropleth Maps")
    st.info(
        "Aceasta analiza afiseaza date statistice pe harta interactiva a Romaniei. "
        "Puteti selecta tipul de date si anul pentru vizualizare spatiala."
    )
    
    # Incarca datele geografice
    geo_data, geo_type = incarca_date_geografice()
    if geo_data is None:
        st.error("Nu s-au putut incarca datele geografice.")
        return
    
    # Selecteaza tipul de analiza spatiala
    tip_analiza = st.selectbox(
        "Alege tipul de date pentru afisare:",
        [
            "Rata somajului",
            "Rata de ocupare a resurselor de munca",
            "Populatia activa",
            "Numarul total de absolventi",
            "Numarul total de salariati",
            "Numarul de salariati pe activitati economice",
            "PIB regional pe locuitor",
            "Castigul salarial mediu net",
            "Imigranti definitivi"
        ]
    )
    
    if tip_analiza == "Rata somajului":
        choropleth_rata_somaj(geo_data, geo_type)
    elif tip_analiza == "Rata de ocupare a resurselor de munca":
        choropleth_rata_ocupare(geo_data, geo_type)
    elif tip_analiza == "Populatia activa":
        choropleth_populatie_activa(geo_data, geo_type)
    elif tip_analiza == "Numarul total de absolventi":
        choropleth_absolventi(geo_data, geo_type)
    elif tip_analiza == "Numarul total de salariati":
        choropleth_salariati_total(geo_data, geo_type)
    elif tip_analiza == "Numarul de salariati pe activitati economice":
        choropleth_salariati_activitati(geo_data, geo_type)
    elif tip_analiza == "PIB regional pe locuitor":
        choropleth_pib(geo_data, geo_type)
    elif tip_analiza == "Castigul salarial mediu net":
        choropleth_salariu_mediu(geo_data, geo_type)
    elif tip_analiza == "Imigranti definitivi":
        choropleth_imigranti(geo_data, geo_type)

def choropleth_pib(geo_data, geo_type):
    # Creeaza choropleth map pentru PIB regional pe locuitor
    st.subheader("PIB regional pe locuitor - Harta interactiva")

    # Incarca datele de PIB
    df_pib = incarca_date('PIB')
    df_pib = replace_total_with_romania(df_pib)

    # Selecteaza parametrii
    ani = sorted([col for col in df_pib.columns if col.startswith('Anul')],
                 key=lambda x: int(x.split()[-1]), reverse=True)
    an = st.selectbox("Alege anul:", ani, index=0)
    doar_centru = st.checkbox("Afiseaza doar regiunea Centru", value=False)

    # Filtreaza datele
    df_filtrat = filtreaza_judete_pentru_harta(df_pib, doar_centru)
    df_filtrat = converteste_ani_la_float(df_filtrat, [an])
    df_filtrat['Judete_std'] = df_filtrat['Judete'].apply(standardizeaza_nume_judete)

    # Coordonatele și prescurtările județelor din regiunea Centru
    coordonate_judete = {
        'Alba': (46.0667, 23.5833),
        'Brasov': (45.6500, 25.6000),
        'Covasna': (45.8667, 26.1833),
        'Harghita': (46.3600, 25.8000),
        'Mures': (46.5500, 24.5667),
        'Sibiu': (45.7833, 24.1500)
    }
    
    prescurtari_judete = {
        'Alba': 'AB',
        'Brasov': 'BV', 
        'Covasna': 'CV',
        'Harghita': 'HR',
        'Mures': 'MS',
        'Sibiu': 'SB'
    }

    # Creeaza harta cu Plotly
    if geo_type == 'geojson':
        fig = px.choropleth(
            df_filtrat,
            geojson=geo_data,
            locations='Judete_std',
            color=an,
            hover_name='Judete',
            hover_data={an: ':.0f'},
            featureidkey="properties.name",
            projection="mercator",
            color_continuous_scale="PuRd",
            title=f"PIB regional pe locuitor in anul {an.split()[-1]} - {'Regiunea Centru' if doar_centru else 'Romania'}"
        )

        # Adauga labeluri DOAR pentru regiunea Centru
        if doar_centru:
            for _, row in df_filtrat.iterrows():
                if row['Judete'] in coordonate_judete and row['Judete'] in prescurtari_judete:
                    lat, lon = coordonate_judete[row['Judete']]
                    prescurtare = prescurtari_judete[row['Judete']]
                    
                    fig.add_scattergeo(
                        lat=[lat],
                        lon=[lon],
                        text=[prescurtare],
                        mode='text',
                        textfont=dict(
                            size=14,
                            color="black",
                            family="Arial Black"
                        ),
                        textposition='middle center',
                        showlegend=False,
                        hoverinfo='skip'
                    )

    fig.update_geos(
        fitbounds="locations",
        visible=False,
        bgcolor="rgba(0,0,0,0)"
    )
    fig.update_layout(
        width=1200,
        height=800,
        title=dict(font=dict(size=20)),
        coloraxis_colorbar=dict(title="PIB pe locuitor (lei)"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    st.plotly_chart(fig, use_container_width=True)
    st.markdown("#### Datele afisate pe harta")
    st.dataframe(df_filtrat[['Judete', an]].set_index('Judete'))

def choropleth_salariu_mediu(geo_data, geo_type):
    # Creeaza choropleth map pentru castigul salarial mediu net
    st.subheader("Castigul salarial mediu net - Harta interactiva")

    # Incarca datele de salariu
    df_salariu = incarca_date('Salariu')
    df_salariu = replace_total_with_romania(df_salariu)

    # Selecteaza parametrii
    ani = sorted([col for col in df_salariu.columns if col.startswith('Anul')],
                 key=lambda x: int(x.split()[-1]), reverse=True)
    sex = st.selectbox("Alege sexul:", df_salariu['Sexe'].unique())
    an = st.selectbox("Alege anul:", ani, index=0)
    doar_centru = st.checkbox("Afiseaza doar regiunea Centru", value=False)

    # Filtreaza datele
    df_filtrat = filtreaza_judete_pentru_harta(df_salariu, doar_centru)
    df_filtrat = df_filtrat[df_filtrat['Sexe'] == sex]
    df_filtrat = converteste_ani_la_float(df_filtrat, [an])
    df_filtrat['Judete_std'] = df_filtrat['Judete'].apply(standardizeaza_nume_judete)

    # Coordonatele și prescurtările județelor din regiunea Centru
    coordonate_judete = {
        'Alba': (46.0667, 23.5833),
        'Brasov': (45.6500, 25.6000),
        'Covasna': (45.8667, 26.1833),
        'Harghita': (46.3600, 25.8000),
        'Mures': (46.5500, 24.5667),
        'Sibiu': (45.7833, 24.1500)
    }
    
    prescurtari_judete = {
        'Alba': 'AB',
        'Brasov': 'BV', 
        'Covasna': 'CV',
        'Harghita': 'HR',
        'Mures': 'MS',
        'Sibiu': 'SB'
    }

    # Creeaza harta cu Plotly
    if geo_type == 'geojson':
        fig = px.choropleth(
            df_filtrat,
            geojson=geo_data,
            locations='Judete_std',
            color=an,
            hover_name='Judete',
            hover_data={an: ':.0f'},
            featureidkey="properties.name",
            projection="mercator",
            color_continuous_scale="amp",
            title=f"Castigul salarial mediu net ({sex}) in anul {an.split()[-1]} - {'Regiunea Centru' if doar_centru else 'Romania'}"
        )

        # Adauga labeluri DOAR pentru regiunea Centru
        if doar_centru:
            for _, row in df_filtrat.iterrows():
                if row['Judete'] in coordonate_judete and row['Judete'] in prescurtari_judete:
                    lat, lon = coordonate_judete[row['Judete']]
                    prescurtare = prescurtari_judete[row['Judete']]
                    
                    fig.add_scattergeo(
                        lat=[lat],
                        lon=[lon],
                        text=[prescurtare],
                        mode='text',
                        textfont=dict(
                            size=14,
                            color="black",
                            family="Arial Black"
                        ),
                        textposition='middle center',
                        showlegend=False,
                        hoverinfo='skip'
                    )

    fig.update_geos(
        fitbounds="locations",
        visible=False,
        bgcolor="rgba(0,0,0,0)"
    )
    fig.update_layout(
        width=1200,
        height=800,
        title=dict(font=dict(size=20)),
        coloraxis_colorbar=dict(title="Salariu mediu net (lei)"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    st.plotly_chart(fig, use_container_width=True)
    st.markdown("#### Datele afisate pe harta")
    st.dataframe(df_filtrat[['Judete', an]].set_index('Judete'))

def choropleth_imigranti(geo_data, geo_type):
    # Creeaza choropleth map pentru imigranti definitivi
    st.subheader("Imigranti definitivi - Harta interactiva")

    # Incarca datele de imigranti
    df_imigranti = incarca_date('Imigranti')
    df_imigranti = replace_total_with_romania(df_imigranti)

    # Selecteaza parametrii
    ani = sorted([col for col in df_imigranti.columns if col.startswith('Anul')],
                 key=lambda x: int(x.split()[-1]), reverse=True)
    an = st.selectbox("Alege anul:", ani, index=0)
    doar_centru = st.checkbox("Afiseaza doar regiunea Centru", value=False)

    # Filtreaza datele
    df_filtrat = filtreaza_judete_pentru_harta(df_imigranti, doar_centru)
    df_filtrat = converteste_ani_la_float(df_filtrat, [an])
    df_filtrat['Judete_std'] = df_filtrat['Judete'].apply(standardizeaza_nume_judete)

    # Coordonatele și prescurtările județelor din regiunea Centru
    coordonate_judete = {
        'Alba': (46.0667, 23.5833),
        'Brasov': (45.6500, 25.6000),
        'Covasna': (45.8667, 26.1833),
        'Harghita': (46.3600, 25.8000),
        'Mures': (46.5500, 24.5667),
        'Sibiu': (45.7833, 24.1500)
    }
    
    prescurtari_judete = {
        'Alba': 'AB',
        'Brasov': 'BV', 
        'Covasna': 'CV',
        'Harghita': 'HR',
        'Mures': 'MS',
        'Sibiu': 'SB'
    }

    # Creeaza harta cu Plotly
    if geo_type == 'geojson':
        fig = px.choropleth(
            df_filtrat,
            geojson=geo_data,
            locations='Judete_std',
            color=an,
            hover_name='Judete',
            hover_data={an: ':.0f'},
            featureidkey="properties.name",
            projection="mercator",
            color_continuous_scale="Teal",
            title=f"Imigranti definitivi in anul {an.split()[-1]} - {'Regiunea Centru' if doar_centru else 'Romania'}"
        )

        # Adauga labeluri DOAR pentru regiunea Centru
        if doar_centru:
            for _, row in df_filtrat.iterrows():
                if row['Judete'] in coordonate_judete and row['Judete'] in prescurtari_judete:
                    lat, lon = coordonate_judete[row['Judete']]
                    prescurtare = prescurtari_judete[row['Judete']]
                    
                    fig.add_scattergeo(
                        lat=[lat],
                        lon=[lon],
                        text=[prescurtare],
                        mode='text',
                        textfont=dict(
                            size=14,
                            color="black",
                            family="Arial Black"
                        ),
                        textposition='middle center',
                        showlegend=False,
                        hoverinfo='skip'
                    )

    fig.update_geos(
        fitbounds="locations",
        visible=False,
        bgcolor="rgba(0,0,0,0)"
    )
    fig.update_layout(
        width=1200,
        height=800,
        title=dict(font=dict(size=20)),
        coloraxis_colorbar=dict(title="Numar imigranti"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    st.plotly_chart(fig, use_container_width=True)
    st.markdown("#### Datele afisate pe harta")
    st.dataframe(df_filtrat[['Judete', an]].set_index('Judete'))

def choropleth_rata_somaj(geo_data, geo_type):
    # Creeaza choropleth map pentru rata somajului
    st.subheader("Rata somajului pe judete - Harta interactiva")

    # Incarca datele de somaj
    df_somaj = incarca_date('Somaj')
    df_somaj = replace_total_with_romania(df_somaj)

    # Selecteaza parametrii
    ani = sorted([col for col in df_somaj.columns if col.startswith('Anul')],
                 key=lambda x: int(x.split()[-1]), reverse=True)
    sex = st.selectbox("Alege sexul:", df_somaj['Sexe'].unique())
    an = st.selectbox("Alege anul:", ani, index=0)
    doar_centru = st.checkbox("Afiseaza doar regiunea Centru", value=False)

    # Filtreaza datele
    df_filtrat = filtreaza_judete_pentru_harta(df_somaj, doar_centru)
    df_filtrat = df_filtrat[df_filtrat['Sexe'] == sex]
    df_filtrat = converteste_ani_la_float(df_filtrat, [an])

    # Standardizeaza numele judetelor
    df_filtrat['Judete_std'] = df_filtrat['Judete'].apply(standardizeaza_nume_judete)

    # Coordonatele și prescurtările județelor din regiunea Centru
    coordonate_judete = {
        'Alba': (46.0667, 23.5833),
        'Brasov': (45.6500, 25.6000),
        'Covasna': (45.8667, 26.1833),
        'Harghita': (46.3600, 25.8000),
        'Mures': (46.5500, 24.5667),
        'Sibiu': (45.7833, 24.1500)
    }
    
    prescurtari_judete = {
        'Alba': 'AB',
        'Brasov': 'BV', 
        'Covasna': 'CV',
        'Harghita': 'HR',
        'Mures': 'MS',
        'Sibiu': 'SB'
    }

    # Creeaza harta cu Plotly
    if geo_type == 'geojson':
        fig = px.choropleth(
            df_filtrat,
            geojson=geo_data,
            locations='Judete_std',
            color=an,
            hover_name='Judete',
            hover_data={an: ':.2f'},
            featureidkey="properties.name",
            projection="mercator",
            color_continuous_scale="Reds",
            title=f"Rata somajului ({sex}) in anul {an.split()[-1]} - {'Regiunea Centru' if doar_centru else 'Romania'}"
        )

        # Adauga labeluri DOAR pentru regiunea Centru
        if doar_centru:
            for _, row in df_filtrat.iterrows():
                if row['Judete'] in coordonate_judete and row['Judete'] in prescurtari_judete:
                    lat, lon = coordonate_judete[row['Judete']]
                    prescurtare = prescurtari_judete[row['Judete']]
                    
                    fig.add_scattergeo(
                        lat=[lat],
                        lon=[lon],
                        text=[prescurtare],
                        mode='text',
                        textfont=dict(
                            size=14,
                            color="black",
                            family="Arial Black"
                        ),
                        textposition='middle center',
                        showlegend=False,
                        hoverinfo='skip'
                    )

    fig.update_geos(
        fitbounds="locations",
        visible=False,
        bgcolor="rgba(0,0,0,0)"
    )
    fig.update_layout(
        width=1200,
        height=800,
        title=dict(font=dict(size=20)),
        coloraxis_colorbar=dict(title="Rata somaj (%)"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    st.plotly_chart(fig, use_container_width=True)
    # Afiseaza tabelul cu datele
    st.markdown("#### Datele afisate pe harta")
    st.dataframe(df_filtrat[['Judete', an]].set_index('Judete'))

def choropleth_rata_ocupare(geo_data, geo_type):
    # Creeaza choropleth map pentru rata de ocupare
    st.subheader("Rata de ocupare a resurselor de munca - Harta interactiva")

    # Incarca datele de ocupare
    df_resurse = incarca_date('Resurse')
    df_resurse = replace_total_with_romania(df_resurse)

    # Selecteaza parametrii
    ani = sorted([col for col in df_resurse.columns if col.startswith('Anul')],
                 key=lambda x: int(x.split()[-1]), reverse=True)
    an = st.selectbox("Alege anul:", ani, index=0)
    doar_centru = st.checkbox("Afiseaza doar regiunea Centru", value=False)

    # Filtreaza datele
    df_filtrat = filtreaza_judete_pentru_harta(df_resurse, doar_centru)
    df_filtrat = converteste_ani_la_float(df_filtrat, [an])
    df_filtrat['Judete_std'] = df_filtrat['Judete'].apply(standardizeaza_nume_judete)

    # Coordonatele și prescurtările județelor din regiunea Centru
    coordonate_judete = {
        'Alba': (46.0667, 23.5833),
        'Brasov': (45.6500, 25.6000),
        'Covasna': (45.8667, 26.1833),
        'Harghita': (46.3600, 25.8000),
        'Mures': (46.5500, 24.5667),
        'Sibiu': (45.7833, 24.1500)
    }
    
    prescurtari_judete = {
        'Alba': 'AB',
        'Brasov': 'BV', 
        'Covasna': 'CV',
        'Harghita': 'HR',
        'Mures': 'MS',
        'Sibiu': 'SB'
    }

    # Creeaza harta cu Plotly
    if geo_type == 'geojson':
        fig = px.choropleth(
            df_filtrat,
            geojson=geo_data,
            locations='Judete_std',
            color=an,
            hover_name='Judete',
            hover_data={an: ':.2f'},
            featureidkey="properties.name",
            projection="mercator",
            color_continuous_scale="Blues",
            title=f"Rata de ocupare a resurselor de munca in anul {an.split()[-1]} - {'Regiunea Centru' if doar_centru else 'Romania'}"
        )

        # Adauga labeluri DOAR pentru regiunea Centru
        if doar_centru:
            for _, row in df_filtrat.iterrows():
                if row['Judete'] in coordonate_judete and row['Judete'] in prescurtari_judete:
                    lat, lon = coordonate_judete[row['Judete']]
                    prescurtare = prescurtari_judete[row['Judete']]
                    
                    fig.add_scattergeo(
                        lat=[lat],
                        lon=[lon],
                        text=[prescurtare],
                        mode='text',
                        textfont=dict(
                            size=14,
                            color="black",
                            family="Arial Black"
                        ),
                        textposition='middle center',
                        showlegend=False,
                        hoverinfo='skip'
                    )

    fig.update_geos(
        fitbounds="locations",
        visible=False,
        bgcolor="rgba(0,0,0,0)"
    )
    fig.update_layout(
        width=1200,
        height=800,
        title=dict(font=dict(size=20)),
        coloraxis_colorbar=dict(title="Rata ocupare (%)"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    st.plotly_chart(fig, use_container_width=True)
    st.markdown("#### Datele afisate pe harta")
    st.dataframe(df_filtrat[['Judete', an]].set_index('Judete'))

def choropleth_populatie_activa(geo_data, geo_type):
    # Creeaza choropleth map pentru populatia activa
    st.subheader("Populatia activa - Harta interactiva")

    # Incarca datele de populatie activa
    df_popactiva = incarca_date('PopActiva')
    df_popactiva = replace_total_with_romania(df_popactiva)

    # Selecteaza parametrii
    ani = sorted([col for col in df_popactiva.columns if col.startswith('Anul')],
                 key=lambda x: int(x.split()[-1]), reverse=True)
    sex = st.selectbox("Alege sexul:", df_popactiva['Sexe'].unique())
    an = st.selectbox("Alege anul:", ani, index=0)
    doar_centru = st.checkbox("Afiseaza doar regiunea Centru", value=False)

    # Filtreaza datele
    df_filtrat = filtreaza_judete_pentru_harta(df_popactiva, doar_centru)
    df_filtrat = df_filtrat[df_filtrat['Sexe'] == sex]
    df_filtrat = converteste_ani_la_float(df_filtrat, [an])
    df_filtrat['Judete_std'] = df_filtrat['Judete'].apply(standardizeaza_nume_judete)

    # Coordonatele și prescurtările județelor din regiunea Centru
    coordonate_judete = {
        'Alba': (46.0667, 23.5833),
        'Brasov': (45.6500, 25.6000),
        'Covasna': (45.8667, 26.1833),
        'Harghita': (46.3600, 25.8000),
        'Mures': (46.5500, 24.5667),
        'Sibiu': (45.7833, 24.1500)
    }
    
    prescurtari_judete = {
        'Alba': 'AB',
        'Brasov': 'BV', 
        'Covasna': 'CV',
        'Harghita': 'HR',
        'Mures': 'MS',
        'Sibiu': 'SB'
    }

    # Creeaza harta cu Plotly
    if geo_type == 'geojson':
        fig = px.choropleth(
            df_filtrat,
            geojson=geo_data,
            locations='Judete_std',
            color=an,
            hover_name='Judete',
            hover_data={an: ':.0f'},
            featureidkey="properties.name",
            projection="mercator",
            color_continuous_scale="Greens",
            title=f"Populatia activa ({sex}) in anul {an.split()[-1]} - {'Regiunea Centru' if doar_centru else 'Romania'}"
        )

        # Adauga labeluri DOAR pentru regiunea Centru
        if doar_centru:
            for _, row in df_filtrat.iterrows():
                if row['Judete'] in coordonate_judete and row['Judete'] in prescurtari_judete:
                    lat, lon = coordonate_judete[row['Judete']]
                    prescurtare = prescurtari_judete[row['Judete']]
                    
                    fig.add_scattergeo(
                        lat=[lat],
                        lon=[lon],
                        text=[prescurtare],
                        mode='text',
                        textfont=dict(
                            size=14,
                            color="black",
                            family="Arial Black"
                        ),
                        textposition='middle center',
                        showlegend=False,
                        hoverinfo='skip'
                    )

    fig.update_geos(
        fitbounds="locations",
        visible=False,
        bgcolor="rgba(0,0,0,0)"
    )
    fig.update_layout(
        width=1200,
        height=800,
        title=dict(font=dict(size=20)),
        coloraxis_colorbar=dict(title="Populatie activa (mii persoane)"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    st.plotly_chart(fig, use_container_width=True)
    st.markdown("#### Datele afisate pe harta")
    st.dataframe(df_filtrat[['Judete', an]].set_index('Judete'))

def choropleth_absolventi(geo_data, geo_type):
    # Creeaza choropleth map pentru numarul total de absolventi
    st.subheader("Numarul total de absolventi - Harta interactiva")

    # Incarca datele de absolventi
    df_absolventi = incarca_date('Absolventi')
    df_absolventi = replace_total_with_romania(df_absolventi)

    # Selecteaza parametrii
    ani = sorted([col for col in df_absolventi.columns if col.startswith('Anul')],
                 key=lambda x: int(x.split()[-1]), reverse=True)
    an = st.selectbox("Alege anul:", ani, index=0)
    doar_centru = st.checkbox("Afiseaza doar regiunea Centru", value=False)

    # Filtreaza datele
    df_filtrat = filtreaza_judete_pentru_harta(df_absolventi, doar_centru)
    df_filtrat = converteste_ani_la_float(df_filtrat, [an])
    df_total = df_filtrat.groupby('Judete')[an].sum().reset_index()
    df_total['Judete_std'] = df_total['Judete'].apply(standardizeaza_nume_judete)

    # Coordonatele și prescurtările județelor din regiunea Centru
    coordonate_judete = {
        'Alba': (46.0667, 23.5833),
        'Brasov': (45.6500, 25.6000),
        'Covasna': (45.8667, 26.1833),
        'Harghita': (46.3600, 25.8000),
        'Mures': (46.5500, 24.5667),
        'Sibiu': (45.7833, 24.1500)
    }
    
    prescurtari_judete = {
        'Alba': 'AB',
        'Brasov': 'BV', 
        'Covasna': 'CV',
        'Harghita': 'HR',
        'Mures': 'MS',
        'Sibiu': 'SB'
    }

    # Creeaza harta cu Plotly
    if geo_type == 'geojson':
        fig = px.choropleth(
            df_total,
            geojson=geo_data,
            locations='Judete_std',
            color=an,
            hover_name='Judete',
            hover_data={an: ':.0f'},
            featureidkey="properties.name",
            projection="mercator",
            color_continuous_scale="Purples",
            title=f"Numarul total de absolventi in anul {an.split()[-1]} - {'Regiunea Centru' if doar_centru else 'Romania'}"
        )

        # Adauga labeluri DOAR pentru regiunea Centru
        if doar_centru:
            for _, row in df_total.iterrows():
                if row['Judete'] in coordonate_judete and row['Judete'] in prescurtari_judete:
                    lat, lon = coordonate_judete[row['Judete']]
                    prescurtare = prescurtari_judete[row['Judete']]
                    
                    fig.add_scattergeo(
                        lat=[lat],
                        lon=[lon],
                        text=[prescurtare],
                        mode='text',
                        textfont=dict(
                            size=14,
                            color="black",
                            family="Arial Black"
                        ),
                        textposition='middle center',
                        showlegend=False,
                        hoverinfo='skip'
                    )

    fig.update_geos(
        fitbounds="locations",
        visible=False,
        bgcolor="rgba(0,0,0,0)"
    )
    fig.update_layout(
        width=1200,
        height=800,
        title=dict(font=dict(size=20)),
        coloraxis_colorbar=dict(title="Numar absolventi"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    st.plotly_chart(fig, use_container_width=True)
    st.markdown("#### Datele afisate pe harta")
    st.dataframe(df_total.set_index('Judete')[[an]])

def choropleth_salariati_total(geo_data, geo_type):
    # Creeaza choropleth map pentru numarul total de salariati
    st.subheader("Numarul total de salariati - Harta interactiva")

    # Incarca datele de salariati
    df_salariati = incarca_date('Salariati2')
    df_salariati = replace_total_with_romania(df_salariati)

    # Selecteaza parametrii
    ani = sorted([col for col in df_salariati.columns if col.startswith('Anul')],
                 key=lambda x: int(x.split()[-1]), reverse=True)
    an = st.selectbox("Alege anul:", ani, index=0)
    doar_centru = st.checkbox("Afiseaza doar regiunea Centru", value=False)

    # Calculeaza totalul pe judete
    df_filtrat = filtreaza_judete_pentru_harta(df_salariati, doar_centru)
    df_filtrat = converteste_ani_la_float(df_filtrat, [an])
    df_total = df_filtrat.groupby('Judete')[an].sum().reset_index()
    df_total['Judete_std'] = df_total['Judete'].apply(standardizeaza_nume_judete)

    # Converteste la mii pentru afisare
    df_total[f'{an}_mii'] = df_total[an] / 1000

    # Coordonatele și prescurtările județelor din regiunea Centru
    coordonate_judete = {
        'Alba': (46.0667, 23.5833),
        'Brasov': (45.6500, 25.6000),
        'Covasna': (45.8667, 26.1833),
        'Harghita': (46.3600, 25.8000),
        'Mures': (46.5500, 24.5667),
        'Sibiu': (45.7833, 24.1500)
    }
    
    prescurtari_judete = {
        'Alba': 'AB',
        'Brasov': 'BV', 
        'Covasna': 'CV',
        'Harghita': 'HR',
        'Mures': 'MS',
        'Sibiu': 'SB'
    }

    # Creeaza harta cu Plotly
    if geo_type == 'geojson':
        fig = px.choropleth(
            df_total,
            geojson=geo_data,
            locations='Judete_std',
            color=f'{an}_mii',
            hover_name='Judete',
            hover_data={f'{an}_mii': ':.1f'},
            featureidkey="properties.name",
            projection="mercator",
            color_continuous_scale="Burg",
            title=f"Numarul total de salariati in anul {an.split()[-1]} - {'Regiunea Centru' if doar_centru else 'Romania'}"
        )

        # Adauga labeluri DOAR pentru regiunea Centru
        if doar_centru:
            for _, row in df_total.iterrows():
                if row['Judete'] in coordonate_judete and row['Judete'] in prescurtari_judete:
                    lat, lon = coordonate_judete[row['Judete']]
                    prescurtare = prescurtari_judete[row['Judete']]
                    
                    fig.add_scattergeo(
                        lat=[lat],
                        lon=[lon],
                        text=[prescurtare],
                        mode='text',
                        textfont=dict(
                            size=14,
                            color="black",
                            family="Arial Black"
                        ),
                        textposition='middle center',
                        showlegend=False,
                        hoverinfo='skip'
                    )

    fig.update_geos(
        fitbounds="locations",
        visible=False,
        bgcolor="rgba(0,0,0,0)"
    )
    fig.update_layout(
        width=1200,
        height=800,
        title=dict(font=dict(size=20)),
        coloraxis_colorbar=dict(title="Numar salariati (mii)"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    st.plotly_chart(fig, use_container_width=True)
    st.markdown("#### Datele afisate pe harta")
    df_display = df_total[['Judete', an]].set_index('Judete')
    st.dataframe(df_display)

def choropleth_salariati_activitati(geo_data, geo_type):
    # Creeaza choropleth map pentru salariati pe activitati economice
    st.subheader("Numarul de salariati pe activitati economice - Harta interactiva")

    # Incarca datele de salariati
    df_salariati = incarca_date('Salariati2')
    df_salariati = replace_total_with_romania(df_salariati)

    # Selecteaza parametrii
    ani = sorted([col for col in df_salariati.columns if col.startswith('Anul')],
                 key=lambda x: int(x.split()[-1]), reverse=True)
    an = st.selectbox("Alege anul:", ani, index=0)
    doar_centru = st.checkbox("Afiseaza doar regiunea Centru", value=False)

    activitati = df_salariati['Activitati ale economiei'].unique()
    activitati_prescurtate = [prescurteaza_activitate(a) for a in activitati]
    activitate = st.selectbox("Alege activitatea economica:", activitati_prescurtate)
    activitate_originala = [a for a in activitati if prescurteaza_activitate(a) == activitate][0]

    # Filtreaza datele
    df_filtrat = filtreaza_judete_pentru_harta(df_salariati, doar_centru)
    df_filtrat = df_filtrat[df_filtrat['Activitati ale economiei'] == activitate_originala]
    df_filtrat = converteste_ani_la_float(df_filtrat, [an])
    df_filtrat['Judete_std'] = df_filtrat['Judete'].apply(standardizeaza_nume_judete)

    # Coordonatele și prescurtările județelor din regiunea Centru
    coordonate_judete = {
        'Alba': (46.0667, 23.5833),
        'Brasov': (45.6500, 25.6000),
        'Covasna': (45.8667, 26.1833),
        'Harghita': (46.3600, 25.8000),
        'Mures': (46.5500, 24.5667),
        'Sibiu': (45.7833, 24.1500)
    }
    
    prescurtari_judete = {
        'Alba': 'AB',
        'Brasov': 'BV', 
        'Covasna': 'CV',
        'Harghita': 'HR',
        'Mures': 'MS',
        'Sibiu': 'SB'
    }

    # Creeaza harta cu Plotly
    if geo_type == 'geojson':
        fig = px.choropleth(
            df_filtrat,
            geojson=geo_data,
            locations='Judete_std',
            color=an,
            hover_name='Judete',
            hover_data={an: ':.0f'},
            featureidkey="properties.name",
            projection="mercator",
            color_continuous_scale="Oranges",
            title=f"Salariati in {activitate} ({an.split()[-1]}) - {'Regiunea Centru' if doar_centru else 'Romania'}"
        )

        # Adauga labeluri DOAR pentru regiunea Centru
        if doar_centru:
            for _, row in df_filtrat.iterrows():
                if row['Judete'] in coordonate_judete and row['Judete'] in prescurtari_judete:
                    lat, lon = coordonate_judete[row['Judete']]
                    prescurtare = prescurtari_judete[row['Judete']]
                    
                    fig.add_scattergeo(
                        lat=[lat],
                        lon=[lon],
                        text=[prescurtare],
                        mode='text',
                        textfont=dict(
                            size=14,
                            color="black",
                            family="Arial Black"
                        ),
                        textposition='middle center',
                        showlegend=False,
                        hoverinfo='skip'
                    )

    fig.update_geos(
        fitbounds="locations",
        visible=False,
        bgcolor="rgba(0,0,0,0)"
    )
    fig.update_layout(
        width=1200,
        height=800,
        title=dict(font=dict(size=20)),
        coloraxis_colorbar=dict(title="Numar salariati"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    st.plotly_chart(fig, use_container_width=True)
    st.markdown("#### Datele afisate pe harta")
    st.dataframe(df_filtrat[['Judete', an]].set_index('Judete'))

def analiza_pib_evolutie():
    # Analiza evolutiei PIB-ului regional pe locuitor
    st.header("Evolutia PIB-ului regional pe locuitor")
    st.info("Acest grafic arata evolutia PIB-ului regional pe locuitor in timp pentru fiecare judet din regiunea Centru. "
            "Linia alba punctata reprezinta media nationala.")
    
    df = incarca_date('PIB')
    ani = sorted([col for col in df.columns if col.startswith('Anul')],
                 key=lambda x: int(x.split()[-1]), reverse=True)
    
    df_filtrat = df[(df['Judete'].isin(['Alba', 'Brasov', 'Covasna', 'Harghita', 'Mures', 'Sibiu'])) |
                    (df['Judete'].str.upper() == 'TOTAL')]
    
    grafic_linie_pib(df_filtrat, ani, "Evolutia PIB-ului regional pe locuitor", "PIB pe locuitor (lei)")

def grafic_linie_pib(df, ani, titlu, ylabel):
    # Creaza grafic linie pentru evolutia PIB-ului pe judete
    st.divider()
    ani_num = extrage_ani(ani)
    df = replace_total_with_romania(df)
    df = converteste_ani_la_float(df, ani)
    df_judete = df[df['Judete'] != 'Romania']
    
    fig = go.Figure()
    for idx, row in df_judete.iterrows():
        color = JUD_COLORS.get(row['Judete'], PALETA[idx % len(PALETA)])
        fig.add_trace(go.Scatter(
            x=ani_num,
            y=[row[an] for an in ani],
            mode='lines+markers',
            name=row['Judete'],
            text=[f"{row['Judete']}<br>{an}: {row[an]:.0f} lei" for an in ani],
            hoverinfo='text+y',
            line=dict(width=3, color=color),
            marker=dict(size=10, line=dict(width=1.5, color="#222"), color=color)
        ))
    
    # Adauga linia pentru media nationala (Romania)
    df_total = df[df['Judete'] == 'Romania']
    if not df_total.empty:
        row = df_total.iloc[0]
        fig.add_trace(go.Scatter(
            x=ani_num,
            y=[row[an] for an in ani],
            mode='lines+markers',
            name="Medie Romania",
            text=[f"Medie Romania<br>{an}: {row[an]:.0f} lei" for an in ani],
            hoverinfo='text+y',
            line=dict(width=5, color="#FFFFFF", dash='dot'),
            marker=dict(size=12, color="#FFFFFF", line=dict(width=2, color='black'))
        ))
    
    # Configurare aspect grafic
    fig.update_layout(
        width=1000, height=650,
        font=dict(family="Segoe UI, Arial", size=16),
        title=dict(text=titlu, font=dict(size=26)),
        xaxis_title=dict(text="Anul", font=dict(size=18)),
        yaxis_title=dict(text=ylabel, font=dict(size=18)),
        yaxis=dict(tickfont=dict(size=14)),
        xaxis=dict(tickfont=dict(size=14)),
        legend_title=dict(text="Judet", font=dict(size=16)),
        legend=dict(font=dict(size=14)),
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("#### Tabel cu datele")
    st.dataframe(df.set_index('Judete')[ani])
    st.divider()

def analiza_statistici_descriptive():
    # Analiza cu statistici descriptive pentru diferite indicatori
    st.header("Statistici descriptive pentru indicatorii pietei muncii")
    st.info("Aceasta analiza calculeaza statistici descriptive (media, mediana, dispersia, etc.) "
            "pentru diferiti indicatori ai pietei muncii din regiunea Centru.")
    
    # Selecteaza tipul de indicator
    tip_indicator = st.selectbox(
        "Alege indicatorul pentru analiza:",
        [
            "Rata somajului",
            "PIB regional pe locuitor", 
            "Castigul salarial mediu net",
            "Rata de ocupare a resurselor de munca",
            "Populatia activa",
            "Imigranti definitivi"
        ]
    )
    
    if tip_indicator == "Rata somajului":
        calculeaza_statistici_somaj()
    elif tip_indicator == "PIB regional pe locuitor":
        calculeaza_statistici_pib()
    elif tip_indicator == "Castigul salarial mediu net":
        calculeaza_statistici_salariu()
    elif tip_indicator == "Rata de ocupare a resurselor de munca":
        calculeaza_statistici_ocupare()
    elif tip_indicator == "Populatia activa":
        calculeaza_statistici_populatie()
    elif tip_indicator == "Imigranti definitivi":
        calculeaza_statistici_imigranti()

def verifica_semnificativitatea_statistici(valori, nume_indicator):
    """
    Verifica semnificativitatea statisticilor descriptive
    """
    rezultate = {}
    n = len(valori)
    
    # Test de normalitate
    if n <= 50:
        # Shapiro-Wilk pentru eșantioane mici
        stat_shapiro, p_shapiro = shapiro(valori)
        rezultate['test_normalitate'] = f"Shapiro-Wilk: statistica={stat_shapiro:.4f}, p-value={p_shapiro:.4f}"
        rezultate['normalitate_concluzie'] = "Datele urmează distribuția normală" if p_shapiro > 0.05 else "Datele NU urmează distribuția normală"
    else:
        # Kolmogorov-Smirnov pentru eșantioane mari
        stat_ks, p_ks = kstest(valori, 'norm')
        rezultate['test_normalitate'] = f"Kolmogorov-Smirnov: statistica={stat_ks:.4f}, p-value={p_ks:.4f}"
        rezultate['normalitate_concluzie'] = "Datele urmează distribuția normală" if p_ks > 0.05 else "Datele NU urmează distribuția normală"
    
    # Intervale de încredere pentru medie (95% și 99%)
    media = np.mean(valori)
    eroare_std = stats.sem(valori)  # Standard error of mean
    
    # Interval 95%
    ic_95 = stats.t.interval(0.95, n-1, loc=media, scale=eroare_std)
    rezultate['interval_incredere_95'] = f"IC 95% pentru medie: [{ic_95[0]:.3f}, {ic_95[1]:.3f}]"
    
    # Interval 99%
    ic_99 = stats.t.interval(0.99, n-1, loc=media, scale=eroare_std)
    rezultate['interval_incredere_99'] = f"IC 99% pentru medie: [{ic_99[0]:.3f}, {ic_99[1]:.3f}]"
    
    # Test t pentru media (testăm dacă media diferă semnificativ de 0)
    t_stat, p_t = ttest_1samp(valori, 0)
    rezultate['test_t_media'] = f"Test t pentru medie=0: t={t_stat:.4f}, p-value={p_t:.4f}"
    rezultate['media_semnificativa'] = "Media este semnificativ diferită de 0" if p_t < 0.05 else "Media NU este semnificativ diferită de 0"
    
    # Detectarea valorilor extreme (outliers) - metoda IQR
    Q1 = np.percentile(valori, 25)
    Q3 = np.percentile(valori, 75)
    IQR = Q3 - Q1
    limita_inf = Q1 - 1.5 * IQR
    limita_sup = Q3 + 1.5 * IQR
    
    outliers = valori[(valori < limita_inf) | (valori > limita_sup)]
    rezultate['outliers'] = f"Valori extreme detectate: {len(outliers)} din {n} observații"
    if len(outliers) > 0:
        rezultate['lista_outliers'] = f"Valorile extreme sunt: {outliers.tolist()}"
    
    # Test pentru varianta (test Chi-patrat)
    varianta_observata = np.var(valori, ddof=1)
    chi2_stat = (n-1) * varianta_observata / 1
    p_chi2 = 1 - stats.chi2.cdf(chi2_stat, n-1)
    rezultate['test_varianta'] = f"Test Chi² pentru varianță: χ²={chi2_stat:.4f}, p-value={p_chi2:.4f}"
    
    return rezultate

def calculeaza_statistici_somaj():
    # Calculeaza statistici descriptive pentru rata somajului
    st.subheader("Statistici descriptive - Rata somajului")
    
    df = incarca_date('Somaj')
    df = replace_total_with_romania(df)
    
    # Selecteaza parametrii
    sex = st.selectbox("Alege sexul:", df['Sexe'].unique())
    ani = sorted([col for col in df.columns if col.startswith('Anul')],
                 key=lambda x: int(x.split()[-1]), reverse=True)
    an = st.selectbox("Alege anul:", ani, index=0)
    
    # Filtreaza datele pentru regiunea Centru
    df_centru = df[(df['Sexe'] == sex) & 
                   (df['Judete'].isin(['Alba', 'Brasov', 'Covasna', 'Harghita', 'Mures', 'Sibiu']))]
    df_centru = converteste_ani_la_float(df_centru, [an])
    
    # Calculeaza statisticile
    valori = df_centru[an].dropna()
    
    statistici = {
        'Media': np.mean(valori),
        'Mediana': np.median(valori),
        'Dispersia': np.var(valori, ddof=1),
        'Abaterea standard': np.std(valori, ddof=1),
        'Minimul': np.min(valori),
        'Maximul': np.max(valori),
        'Coeficientul de variatie (%)': (np.std(valori, ddof=1) / np.mean(valori)) * 100,
        'Amplitudinea': np.max(valori) - np.min(valori)
    }
    
    # Afiseaza rezultatele
    st.markdown("#### Statistici descriptive calculate")
    df_stat = pd.DataFrame(list(statistici.items()), columns=['Statistica', 'Valoare'])
    df_stat['Valoare'] = df_stat['Valoare'].round(3)
    st.dataframe(df_stat, use_container_width=True)
    
    # Verificarea semnificativității
    rezultate_teste = verifica_semnificativitatea_statistici(valori, "Rata somajului")
    
    # Secțiunea informativă cu rezultatele verificării
    st.markdown("#### Verificarea semnificativității statisticilor")
    st.info(f"""
    **Rezultatele testelor statistice pentru rata somajului:**
    
    📊 **Test de normalitate:** {rezultate_teste['test_normalitate']}
    ✅ **Concluzie normalitate:** {rezultate_teste['normalitate_concluzie']}
    
    📈 **Intervale de încredere:**
    - {rezultate_teste['interval_incredere_95']}
    - {rezultate_teste['interval_incredere_99']}
    
    🎯 **Test pentru medie:** {rezultate_teste['test_t_media']}
    ✅ **Concluzie medie:** {rezultate_teste['media_semnificativa']}
    
    ⚠️ **Valori extreme:** {rezultate_teste['outliers']}
    {rezultate_teste.get('lista_outliers', '')}
    
    📊 **Test pentru varianță:** {rezultate_teste['test_varianta']}
    
    **Interpretare:**
    - Dacă p-value < 0.05 → rezultatul este semnificativ statistic
    - Intervalele de încredere arată intervalul în care se află adevărata valoare a mediei cu o probabilitate de 95%/99%
    - Valorile extreme pot influența semnificativ rezultatele statisticilor descriptive
    """)
    
    # Afiseaza datele folosite
    st.markdown("#### Datele folosite pentru calcul")
    st.dataframe(df_centru[['Judete', an]].set_index('Judete'))

def calculeaza_statistici_pib():
    # Calculeaza statistici descriptive pentru PIB
    st.subheader("Statistici descriptive - PIB regional pe locuitor")
    
    df = incarca_date('PIB')
    df = replace_total_with_romania(df)
    
    # Selecteaza parametrii
    ani = sorted([col for col in df.columns if col.startswith('Anul')],
                 key=lambda x: int(x.split()[-1]), reverse=True)
    an = st.selectbox("Alege anul:", ani, index=0)
    
    # Filtreaza datele pentru regiunea Centru
    df_centru = df[df['Judete'].isin(['Alba', 'Brasov', 'Covasna', 'Harghita', 'Mures', 'Sibiu'])]
    df_centru = converteste_ani_la_float(df_centru, [an])
    
    # Calculeaza statisticile
    valori = df_centru[an].dropna()
    
    statistici = {
        'Media': np.mean(valori),
        'Mediana': np.median(valori),
        'Dispersia': np.var(valori, ddof=1),
        'Abaterea standard': np.std(valori, ddof=1),
        'Minimul': np.min(valori),
        'Maximul': np.max(valori),
        'Coeficientul de variatie (%)': (np.std(valori, ddof=1) / np.mean(valori)) * 100,
        'Amplitudinea': np.max(valori) - np.min(valori)
    }
    
    # Afiseaza rezultatele
    st.markdown("#### Statistici descriptive calculate")
    df_stat = pd.DataFrame(list(statistici.items()), columns=['Statistica', 'Valoare'])
    df_stat['Valoare'] = df_stat['Valoare'].round(2)
    st.dataframe(df_stat, use_container_width=True)
    
    # Verificarea semnificativității
    rezultate_teste = verifica_semnificativitatea_statistici(valori, "PIB regional pe locuitor")
    
    # Secțiunea informativă cu rezultatele verificării
    st.markdown("#### Verificarea semnificativității statisticilor")
    st.info(f"""
    **Rezultatele testelor statistice pentru PIB regional pe locuitor:**
    
    📊 **Test de normalitate:** {rezultate_teste['test_normalitate']}
    ✅ **Concluzie normalitate:** {rezultate_teste['normalitate_concluzie']}
    
    📈 **Intervale de încredere:**
    - {rezultate_teste['interval_incredere_95']}
    - {rezultate_teste['interval_incredere_99']}
    
    🎯 **Test pentru medie:** {rezultate_teste['test_t_media']}
    ✅ **Concluzie medie:** {rezultate_teste['media_semnificativa']}
    
    ⚠️ **Valori extreme:** {rezultate_teste['outliers']}
    {rezultate_teste.get('lista_outliers', '')}
    
    📊 **Test pentru varianță:** {rezultate_teste['test_varianta']}
    
    **Interpretare:**
    - Dacă p-value < 0.05 → rezultatul este semnificativ statistic
    - Intervalele de încredere arată intervalul în care se află adevărata valoare a mediei cu o probabilitate de 95%/99%
    - Valorile extreme pot influența semnificativ rezultatele statisticilor descriptive
    """)
    
    # Afiseaza datele folosite
    st.markdown("#### Datele folosite pentru calcul")
    st.dataframe(df_centru[['Judete', an]].set_index('Judete'))

def calculeaza_statistici_salariu():
    # Calculeaza statistici descriptive pentru salariul mediu
    st.subheader("Statistici descriptive - Castigul salarial mediu net")
    
    df = incarca_date('Salariu')
    df = replace_total_with_romania(df)
    
    # Selecteaza parametrii
    sex = st.selectbox("Alege sexul:", df['Sexe'].unique())
    ani = sorted([col for col in df.columns if col.startswith('Anul')],
                 key=lambda x: int(x.split()[-1]), reverse=True)
    an = st.selectbox("Alege anul:", ani, index=0)
    
    # Filtreaza datele pentru regiunea Centru
    df_centru = df[(df['Sexe'] == sex) & 
                   (df['Judete'].isin(['Alba', 'Brasov', 'Covasna', 'Harghita', 'Mures', 'Sibiu']))]
    df_centru = converteste_ani_la_float(df_centru, [an])
    
    # Calculeaza statisticile
    valori = df_centru[an].dropna()
    
    statistici = {
        'Media': np.mean(valori),
        'Mediana': np.median(valori),
        'Dispersia': np.var(valori, ddof=1),
        'Abaterea standard': np.std(valori, ddof=1),
        'Minimul': np.min(valori),
        'Maximul': np.max(valori),
        'Coeficientul de variatie (%)': (np.std(valori, ddof=1) / np.mean(valori)) * 100,
        'Amplitudinea': np.max(valori) - np.min(valori)
    }
    
    # Afiseaza rezultatele
    st.markdown("#### Statistici descriptive calculate")
    df_stat = pd.DataFrame(list(statistici.items()), columns=['Statistica', 'Valoare'])
    df_stat['Valoare'] = df_stat['Valoare'].round(2)
    st.dataframe(df_stat, use_container_width=True)
    
    # Verificarea semnificativității
    rezultate_teste = verifica_semnificativitatea_statistici(valori, "Castigul salarial mediu net")
    
    # Secțiunea informativă cu rezultatele verificării
    st.markdown("#### Verificarea semnificativității statisticilor")
    st.info(f"""
    **Rezultatele testelor statistice pentru castigul salarial mediu net:**
    
    📊 **Test de normalitate:** {rezultate_teste['test_normalitate']}
    ✅ **Concluzie normalitate:** {rezultate_teste['normalitate_concluzie']}
    
    📈 **Intervale de încredere:**
    - {rezultate_teste['interval_incredere_95']}
    - {rezultate_teste['interval_incredere_99']}
    
    🎯 **Test pentru medie:** {rezultate_teste['test_t_media']}
    ✅ **Concluzie medie:** {rezultate_teste['media_semnificativa']}
    
    ⚠️ **Valori extreme:** {rezultate_teste['outliers']}
    {rezultate_teste.get('lista_outliers', '')}
    
    📊 **Test pentru varianță:** {rezultate_teste['test_varianta']}
    
    **Interpretare:**
    - Dacă p-value < 0.05 → rezultatul este semnificativ statistic
    - Intervalele de încredere arată intervalul în care se află adevărata valoare a mediei cu o probabilitate de 95%/99%
    - Valorile extreme pot influența semnificativ rezultatele statisticilor descriptive
    """)
    
    # Afiseaza datele folosite
    st.markdown("#### Datele folosite pentru calcul")
    st.dataframe(df_centru[['Judete', an]].set_index('Judete'))

def calculeaza_statistici_ocupare():
    # Calculeaza statistici descriptive pentru rata de ocupare
    st.subheader("Statistici descriptive - Rata de ocupare a resurselor de munca")
    
    df = incarca_date('Resurse')
    df = replace_total_with_romania(df)
    
    # Selecteaza parametrii
    ani = sorted([col for col in df.columns if col.startswith('Anul')],
                 key=lambda x: int(x.split()[-1]), reverse=True)
    an = st.selectbox("Alege anul:", ani, index=0)
    
    # Filtreaza datele pentru regiunea Centru
    df_centru = df[df['Judete'].isin(['Alba', 'Brasov', 'Covasna', 'Harghita', 'Mures', 'Sibiu'])]
    df_centru = converteste_ani_la_float(df_centru, [an])
    
    # Calculeaza statisticile
    valori = df_centru[an].dropna()
    
    statistici = {
        'Media': np.mean(valori),
        'Mediana': np.median(valori),
        'Dispersia': np.var(valori, ddof=1),
        'Abaterea standard': np.std(valori, ddof=1),
        'Minimul': np.min(valori),
        'Maximul': np.max(valori),
        'Coeficientul de variatie (%)': (np.std(valori, ddof=1) / np.mean(valori)) * 100,
        'Amplitudinea': np.max(valori) - np.min(valori)
    }
    
    # Afiseaza rezultatele
    st.markdown("#### Statistici descriptive calculate")
    df_stat = pd.DataFrame(list(statistici.items()), columns=['Statistica', 'Valoare'])
    df_stat['Valoare'] = df_stat['Valoare'].round(3)
    st.dataframe(df_stat, use_container_width=True)
    
    # Verificarea semnificativității
    rezultate_teste = verifica_semnificativitatea_statistici(valori, "Rata de ocupare a resurselor de munca")
    
    # Secțiunea informativă cu rezultatele verificării
    st.markdown("#### Verificarea semnificativității statisticilor")
    st.info(f"""
    **Rezultatele testelor statistice pentru rata de ocupare a resurselor de munca:**
    
    📊 **Test de normalitate:** {rezultate_teste['test_normalitate']}
    ✅ **Concluzie normalitate:** {rezultate_teste['normalitate_concluzie']}
    
    📈 **Intervale de încredere:**
    - {rezultate_teste['interval_incredere_95']}
    - {rezultate_teste['interval_incredere_99']}
    
    🎯 **Test pentru medie:** {rezultate_teste['test_t_media']}
    ✅ **Concluzie medie:** {rezultate_teste['media_semnificativa']}
    
    ⚠️ **Valori extreme:** {rezultate_teste['outliers']}
    {rezultate_teste.get('lista_outliers', '')}
    
    📊 **Test pentru varianță:** {rezultate_teste['test_varianta']}
    
    **Interpretare:**
    - Dacă p-value < 0.05 → rezultatul este semnificativ statistic
    - Intervalele de încredere arată intervalul în care se află adevărata valoare a mediei cu o probabilitate de 95%/99%
    - Valorile extreme pot influența semnificativ rezultatele statisticilor descriptive
    """)
    
    # Afiseaza datele folosite
    st.markdown("#### Datele folosite pentru calcul")
    st.dataframe(df_centru[['Judete', an]].set_index('Judete'))

def calculeaza_statistici_populatie():
    # Calculeaza statistici descriptive pentru populatia activa
    st.subheader("Statistici descriptive - Populatia activa")
    
    df = incarca_date('PopActiva')
    df = replace_total_with_romania(df)
    
    # Selecteaza parametrii
    sex = st.selectbox("Alege sexul:", df['Sexe'].unique())
    ani = sorted([col for col in df.columns if col.startswith('Anul')],
                 key=lambda x: int(x.split()[-1]), reverse=True)
    an = st.selectbox("Alege anul:", ani, index=0)
    
    # Filtreaza datele pentru regiunea Centru
    df_centru = df[(df['Sexe'] == sex) & 
                   (df['Judete'].isin(['Alba', 'Brasov', 'Covasna', 'Harghita', 'Mures', 'Sibiu']))]
    df_centru = converteste_ani_la_float(df_centru, [an])
    
    # Calculeaza statisticile
    valori = df_centru[an].dropna()
    
    statistici = {
        'Media': np.mean(valori),
        'Mediana': np.median(valori),
        'Dispersia': np.var(valori, ddof=1),
        'Abaterea standard': np.std(valori, ddof=1),
        'Minimul': np.min(valori),
        'Maximul': np.max(valori),
        'Coeficientul de variatie (%)': (np.std(valori, ddof=1) / np.mean(valori)) * 100,
        'Amplitudinea': np.max(valori) - np.min(valori)
    }
    
    # Afiseaza rezultatele
    st.markdown("#### Statistici descriptive calculate")
    df_stat = pd.DataFrame(list(statistici.items()), columns=['Statistica', 'Valoare'])
    df_stat['Valoare'] = df_stat['Valoare'].round(3)
    st.dataframe(df_stat, use_container_width=True)
    
    # Verificarea semnificativității
    rezultate_teste = verifica_semnificativitatea_statistici(valori, "Populatia activa")
    
    # Secțiunea informativă cu rezultatele verificării
    st.markdown("#### Verificarea semnificativității statisticilor")
    st.info(f"""
    **Rezultatele testelor statistice pentru populatia activa:**
    
    📊 **Test de normalitate:** {rezultate_teste['test_normalitate']}
    ✅ **Concluzie normalitate:** {rezultate_teste['normalitate_concluzie']}
    
    📈 **Intervale de încredere:**
    - {rezultate_teste['interval_incredere_95']}
    - {rezultate_teste['interval_incredere_99']}
    
    🎯 **Test pentru medie:** {rezultate_teste['test_t_media']}
    ✅ **Concluzie medie:** {rezultate_teste['media_semnificativa']}
    
    ⚠️ **Valori extreme:** {rezultate_teste['outliers']}
    {rezultate_teste.get('lista_outliers', '')}
    
    📊 **Test pentru varianță:** {rezultate_teste['test_varianta']}
    
    **Interpretare:**
    - Dacă p-value < 0.05 → rezultatul este semnificativ statistic
    - Intervalele de încredere arată intervalul în care se află adevărata valoare a mediei cu o probabilitate de 95%/99%
    - Valorile extreme pot influența semnificativ rezultatele statisticilor descriptive
    """)
    
    # Afiseaza datele folosite
    st.markdown("#### Datele folosite pentru calcul")
    st.dataframe(df_centru[['Judete', an]].set_index('Judete'))

def calculeaza_statistici_imigranti():
    # Calculeaza statistici descriptive pentru imigranti
    st.subheader("Statistici descriptive - Imigranti definitivi")
    
    df = incarca_date('Imigranti')
    df = replace_total_with_romania(df)
    
    # Selecteaza parametrii
    ani = sorted([col for col in df.columns if col.startswith('Anul')],
                 key=lambda x: int(x.split()[-1]), reverse=True)
    an = st.selectbox("Alege anul:", ani, index=0)
    
    # Filtreaza datele pentru regiunea Centru
    df_centru = df[df['Judete'].isin(['Alba', 'Brasov', 'Covasna', 'Harghita', 'Mures', 'Sibiu'])]
    df_centru = converteste_ani_la_float(df_centru, [an])
    
    # Calculeaza statisticile
    valori = df_centru[an].dropna()
    
    statistici = {
        'Media': np.mean(valori),
        'Mediana': np.median(valori),
        'Dispersia': np.var(valori, ddof=1),
        'Abaterea standard': np.std(valori, ddof=1),
        'Minimul': np.min(valori),
        'Maximul': np.max(valori),
        'Coeficientul de variatie (%)': (np.std(valori, ddof=1) / np.mean(valori)) * 100,
        'Amplitudinea': np.max(valori) - np.min(valori)
    }
    
    # Afiseaza rezultatele
    st.markdown("#### Statistici descriptive calculate")
    df_stat = pd.DataFrame(list(statistici.items()), columns=['Statistica', 'Valoare'])
    df_stat['Valoare'] = df_stat['Valoare'].round(2)
    st.dataframe(df_stat, use_container_width=True)
    
    # Verificarea semnificativității
    rezultate_teste = verifica_semnificativitatea_statistici(valori, "Imigranti definitivi")
    
    # Secțiunea informativă cu rezultatele verificării
    st.markdown("#### Verificarea semnificativității statisticilor")
    st.info(f"""
    **Rezultatele testelor statistice pentru imigranti definitivi:**
    
    📊 **Test de normalitate:** {rezultate_teste['test_normalitate']}
    ✅ **Concluzie normalitate:** {rezultate_teste['normalitate_concluzie']}
    
    📈 **Intervale de încredere:**
    - {rezultate_teste['interval_incredere_95']}
    - {rezultate_teste['interval_incredere_99']}
    
    🎯 **Test pentru medie:** {rezultate_teste['test_t_media']}
    ✅ **Concluzie medie:** {rezultate_teste['media_semnificativa']}
    
    ⚠️ **Valori extreme:** {rezultate_teste['outliers']}
    {rezultate_teste.get('lista_outliers', '')}
    
    📊 **Test pentru varianță:** {rezultate_teste['test_varianta']}
    
    **Interpretare:**
    - Dacă p-value < 0.05 → rezultatul este semnificativ statistic
    - Intervalele de încredere arată intervalul în care se află adevărata valoare a mediei cu o probabilitate de 95%/99%
    - Valorile extreme pot influența semnificativ rezultatele statisticilor descriptive
    """)
    
    # Afiseaza datele folosite
    st.markdown("#### Datele folosite pentru calcul")
    st.dataframe(df_centru[['Judete', an]].set_index('Judete'))

def grafic_linie_somaj(df, ani, titlu, ylabel):
    # Creaza grafic linie pentru evolutia ratei somajului pe judete
    st.divider()
    ani_num = extrage_ani(ani)
    df = replace_total_with_romania(df)
    df = converteste_ani_la_float(df, ani)
    df_judete = df[df['Judete'] != 'Romania']
    fig = go.Figure()
    for idx, row in df_judete.iterrows():
        color = JUD_COLORS.get(row['Judete'], PALETA[idx % len(PALETA)])
        fig.add_trace(go.Scatter(
            x=ani_num,
            y=[row[an] for an in ani],
            mode='lines+markers',
            name=row['Judete'],
            text=[f"{row['Judete']}<br>{an}: {row[an]:.2f}%" for an in ani],
            hoverinfo='text+y',
            line=dict(width=3, color=color),
            marker=dict(size=10, line=dict(width=1.5, color="#222"), color=color)
        ))
    # Adauga linia pentru media nationala (Romania)
    df_total = df[df['Judete'] == 'Romania']
    if not df_total.empty:
        row = df_total.iloc[0]
        fig.add_trace(go.Scatter(
            x=ani_num,
            y=[row[an] for an in ani],
            mode='lines+markers',
            name="Medie Romania",
            text=[f"Medie Romania<br>{an}: {row[an]:.2f}%" for an in ani],
            hoverinfo='text+y',
            line=dict(width=5, color="#FFFFFF", dash='dot'),
            marker=dict(size=12, color="#FFFFFF", line=dict(width=2, color='black'))
        ))
    # Configurare aspect grafic
    fig.update_layout(
        width=1000, height=650,
        font=dict(family="Segoe UI, Arial", size=16),
        title=dict(text=titlu, font=dict(size=26)),
        xaxis_title=dict(text="Anul", font=dict(size=18)),
        yaxis_title=dict(text=ylabel, font=dict(size=18)),
        yaxis=dict(tickfont=dict(size=14)),
        xaxis=dict(tickfont=dict(size=14)),
        legend_title=dict(text="Judet", font=dict(size=16)),
        legend=dict(font=dict(size=14)),
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("#### Tabel cu datele")
    st.dataframe(df.set_index('Judete')[ani])
    st.divider()

def heatmap_judete_ani_interactiv(df, ani, titlu):
    # Creaza heatmap pentru comparatie rata somaj pe judete si ani
    st.divider()
    ani_num = extrage_ani(ani)
    df = replace_total_with_romania(df)
    df_total = df[df['Judete'] == 'Romania']
    df_centru = df[df['Judete'].isin(['Alba', 'Brasov', 'Covasna', 'Harghita', 'Mures', 'Sibiu'])]
    df_hm = pd.concat([df_centru, df_total], ignore_index=True)
    df_hm = df_hm.set_index('Judete')[ani]
    df_hm.columns = ani_num
    fig = px.imshow(
        df_hm,
        text_auto=True,
        aspect=0.08,
        color_continuous_scale="Blues",
        labels=dict(color="Rata somaj (%)"),
        title=titlu
    )
    fig.update_xaxes(
        side="bottom",
        tickangle=45,
        title=dict(text="Anul", font=dict(size=18)),
        tickfont=dict(size=12),
        dtick=1
    )
    fig.update_yaxes(
        autorange="reversed",
        title=dict(text="Judet", font=dict(size=18)),
        tickfont=dict(size=12)
    )
    fig.update_layout(
        width=1400, height=500,
        font=dict(family="Segoe UI, Arial", size=12),
        title=dict(font=dict(size=22)),
        coloraxis_colorbar=dict(title_font=dict(size=16), tickfont=dict(size=12))
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("#### Tabel cu datele")
    st.dataframe(df_hm)
    st.divider()

def stacked_bar_absolventi_interactiv(df, ani, judet_selectat):
    # Creaza stacked bar pentru structura absolventilor pe niveluri de educatie
    st.divider()
    ani_num = extrage_ani(ani)
    df = replace_total_with_romania(df)
    df = converteste_ani_la_float(df, ani)
    df_judet = df[df['Judete'] == judet_selectat]

    # Pastreaza ordinea nivelurilor de educatie asa cum sunt in tabel
    niveluri = df_judet['Niveluri de educatie'].tolist()

    # Construim DataFrame-ul pentru stacked bar, reindexat dupa ordinea din tabel si completeaza cu 0 unde e necesar
    df_temp = df_judet.set_index('Niveluri de educatie')[ani]
    df_temp = df_temp.reindex(niveluri)
    df_temp = df_temp.fillna(0)
    df_stacked = df_temp.T.reset_index().rename(columns={'index': 'An'})
    df_stacked['An'] = ani_num

    # Paleta de culori pentru niveluri de educatie (ordinea reflecta semnificatia nivelurilor)
    PALETA_EDUCATIE = [
        "#1976D2",
        "#FF9800",
        "#43A047",
        "#8E24AA",
        "#E53935",
        "#ADEED9",
        "#FDD835",
        "#FEC5F6",
        "#C0CA33",
        "#00ACC1",
    ]

    fig = go.Figure()
    legend_labels = []
    # Adaugam cate o serie pentru fiecare nivel, in ordinea din tabel (ultimul din lista este jos in stacked bar)
    for i, nivel in enumerate(niveluri):
        color = PALETA_EDUCATIE[i % len(PALETA_EDUCATIE)]
        fig.add_trace(go.Bar(
            x=df_stacked['An'],
            y=df_stacked[nivel],
            name=nivel,
            text=df_stacked[nivel],
            textfont=dict(size=12),
            marker_color=color,
            marker_line=dict(width=1.5, color="#222"),
            hovertemplate=f"{nivel}: %{{y}}"
        ))
        legend_labels.append((color, nivel))

    fig.update_layout(
        width=1600, height=600,
        font=dict(family="Segoe UI, Arial", size=12),
        barmode='stack',
        title=dict(text=f"Structura absolventilor pe niveluri de educatie ({judet_selectat})", font=dict(size=28)),
        xaxis=dict(title=dict(text="Anul", font=dict(size=16)), tickangle=0, tickfont=dict(size=12)),
        yaxis=dict(title=dict(text="Numar absolventi", font=dict(size=16)), tickfont=dict(size=12)),
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

    # Generam legenda pentru niveluri de educatie
    st.markdown("#### Legenda nivel educatie")
    legend_html = "<div style='display:flex; flex-wrap:wrap; gap:20px;'>"
    for color, label in legend_labels:
        legend_html += (
            "<div style='display:flex; align-items:center; margin-bottom:6px;'>"
            f"<div style='width:18px; height:18px; background:{color}; border:2px solid #222; margin-right:8px;'></div>"
            f"<span style='font-size:15px'>{label}</span></div>"
        )
    legend_html += "</div>"
    st.markdown(legend_html, unsafe_allow_html=True)

    st.markdown("#### Tabel cu datele")
    st.dataframe(df_judet.set_index('Niveluri de educatie')[ani])
    st.divider()

def bar_chart_an_interactiv(df, an, titlu, ylabel):
    # Creaza bar chart pentru comparatia rata somaj in anul selectat
    st.divider()
    an_num = an.split()[-1]
    df = replace_total_with_romania(df)
    df = converteste_ani_la_float(df, [an])
    judete_ord = ["Alba", "Brasov", "Covasna", "Harghita", "Mures", "Sibiu"]
    colors = [JUD_COLORS[j] for j in judete_ord]
    fig = go.Figure()
    for idx, jud in enumerate(judete_ord):
        row = df[df['Judete'] == jud]
        if not row.empty:
            val = row.iloc[0][an]
            fig.add_trace(go.Bar(
                x=[jud],
                y=[val],
                name=jud,
                text=[val],
                marker_color=colors[idx],
                marker_line=dict(width=1.5, color="#222"),
                textfont=dict(size=14)
            ))
    # Adauga bara pentru Romania separat
    row = df[df['Judete'] == 'Romania']
    if not row.empty:
        val = row.iloc[0][an]
        fig.add_trace(go.Bar(
            x=["Romania"],
            y=[val],
            name="Romania",
            text=[val],
            marker_color="#FFFFFF",
            marker_line=dict(width=2, color="#222"),
            textfont=dict(size=14, color="black")
        ))
    fig.update_layout(
        width=1000, height=650,
        font=dict(family="Segoe UI, Arial", size=16),
        yaxis=dict(title=dict(text=ylabel, font=dict(size=18)), tickfont=dict(size=14)),
        xaxis=dict(title=dict(text="Judet", font=dict(size=18)), tickangle=30, tickfont=dict(size=14)),
        title=dict(text=titlu, font=dict(size=26)),
        legend=dict(font=dict(size=14))
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("#### Tabel cu datele")
    st.dataframe(df.set_index('Judete')[[an]])
    st.divider()

def scatter_corelatie_interactiv(df_x, df_y, an, titlu, xlabel, ylabel):
    # Creaza scatter plot pentru corelatia intre rata somaj si rata de ocupare
    st.divider()
    an_num = an.split()[-1]
    df_x = replace_total_with_romania(df_x)
    df_y = replace_total_with_romania(df_y)
    df_x = converteste_ani_la_float(df_x, [an])
    df_y = converteste_ani_la_float(df_y, [an])
    
    # Definește județele din regiunea Centru
    judete_centru = ["Alba", "Brasov", "Covasna", "Harghita", "Mures", "Sibiu"]
    
    # Toate celelalte județe (excluzând regiunea Centru și România)
    judete_alte = [j for j in TOATE_JUDETELE if j not in judete_centru and j != "Romania"]
    
    df_corel = pd.DataFrame({
        'Judet': df_x['Judete'],
        'Rata somaj': df_x[an],
        'Rata ocupare': df_y[an]
    })
    
    fig = go.Figure()
    
    # PRIMUL: Adaugă celelalte județe cu gri și opacitate redusă (să fie în spate)
    for jud in judete_alte:
        row = df_corel[df_corel['Judet'] == jud]
        if not row.empty:
            fig.add_trace(go.Scatter(
                x=row['Rata somaj'],
                y=row['Rata ocupare'],
                mode='markers+text',
                name=jud,
                text=[jud],
                marker=dict(
                    size=12, 
                    color="rgba(128, 128, 128, 0.5)",  # Gri cu opacitate redusă
                    line=dict(width=1, color="rgba(128, 128, 128, 0.7)")
                ),
                textfont=dict(size=10, color="rgba(128, 128, 128, 0.8)"),
                textposition='top center',
                showlegend=False  # Nu afișa în legendă pentru a nu aglomera
            ))
    
    # AL DOILEA: Adaugă județele din regiunea Centru cu culorile specifice (să fie deasupra)
    for jud in judete_centru:
        row = df_corel[df_corel['Judet'] == jud]
        if not row.empty:
            color = JUD_COLORS.get(jud, "#888888")
            fig.add_trace(go.Scatter(
                x=row['Rata somaj'],
                y=row['Rata ocupare'],
                mode='markers+text',
                name=jud,
                text=[jud],
                marker=dict(size=18, color=color, line=dict(width=1.5, color="#222")),
                textfont=dict(size=14, color=color),
                textposition='top center'
            ))
    
    # AL TREILEA: Adaugă România cu culoarea și textul specific (să fie cel mai sus)
    row_romania = df_corel[df_corel['Judet'] == "Romania"]
    if not row_romania.empty:
        fig.add_trace(go.Scatter(
            x=row_romania['Rata somaj'],
            y=row_romania['Rata ocupare'],
            mode='markers+text',
            name="Romania",
            text=["Romania"],
            marker=dict(size=20, color="#FFFFFF", line=dict(width=2, color="#222")),
            textfont=dict(size=14, color="#FFFFFF"),  # Text alb pentru România
            textposition='top center'
        ))
    
    fig.update_layout(
        width=1000, height=650,
        font=dict(family="Segoe UI, Arial", size=16),
        xaxis=dict(title=dict(text=xlabel, font=dict(size=18)), tickfont=dict(size=14)),
        yaxis=dict(title=dict(text=ylabel, font=dict(size=18)), tickfont=dict(size=14)),
        title=dict(text=titlu, font=dict(size=26)),
        legend=dict(font=dict(size=14))
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("#### Tabel cu datele pentru regiunea Centru și România")
    # Afișează doar datele pentru regiunea Centru și România în tabel
    df_display = df_corel[df_corel['Judet'].isin(judete_centru + ["Romania"])]
    st.dataframe(df_display.set_index('Judet'))
    st.divider()

def bar_chart_salariati_activitati(df, ani, an_selectat):
    # Creaza bar chart pentru numarul salariatilor pe activitati economice in anul selectat
    st.divider()
    an_num = an_selectat.split()[-1]
    df = replace_total_with_romania(df)
    df = converteste_ani_la_float(df, [an_selectat])
    judete_ord = ["Alba", "Brasov", "Covasna", "Harghita", "Mures", "Sibiu", "Romania"]
    colors = [JUD_COLORS.get(j, "#888888") for j in judete_ord]
    activitati = df['Activitati ale economiei'].unique()
    activitati_prescurtate = [prescurteaza_activitate(a) for a in activitati]
    # Alege activitatea economica prin dropdown
    activitate = st.selectbox("Alege activitatea economica", activitati_prescurtate)
    activitate_originala = [a for a in activitati if prescurteaza_activitate(a) == activitate][0]
    df_activ = df[df['Activitati ale economiei'] == activitate_originala]
    show_romania = st.checkbox("Afiseaza si Romania", value=False)
    fig = go.Figure()
    for idx, jud in enumerate(judete_ord):
        if jud == "Romania" and not show_romania:
            continue
        row = df_activ[df_activ['Judete'] == jud]
        if not row.empty:
            val = row.iloc[0][an_selectat]
            fig.add_trace(go.Bar(
                x=[jud],
                y=[val],
                name=jud,
                text=[val],
                marker_color=colors[idx],
                marker_line=dict(width=1.5, color="#222"),
                textfont=dict(size=14, color="#222" if jud == "Romania" else "#fff")
            ))
    fig.update_layout(
        width=1000, height=650,
        font=dict(family="Segoe UI, Arial", size=16),
        yaxis=dict(title=dict(text="Numar salariati", font=dict(size=18)), tickfont=dict(size=14)),
        xaxis=dict(title=dict(text="Judet", font=dict(size=18)), tickangle=30, tickfont=dict(size=14)),
        title=dict(text=f"Numar salariati in {an_num} pentru activitatea: {activitate}", font=dict(size=26)),
        legend=dict(font=dict(size=14))
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("#### Tabel cu datele")
    if not show_romania:
        st.dataframe(df_activ[df_activ['Judete'] != "Romania"].set_index('Judete')[[an_selectat]])
    else:
        st.dataframe(df_activ.set_index('Judete')[[an_selectat]])
    st.divider()

def pie_charts_salariati_judete(df, ani, an_selectat):
    # Creaza pie chart-uri pentru structura salariatilor pe activitati economice in fiecare judet
    st.divider()
    an_num = an_selectat.split()[-1]
    df = replace_total_with_romania(df)
    df = converteste_ani_la_float(df, [an_selectat])
    judete = ["Alba", "Brasov", "Covasna", "Harghita", "Mures", "Sibiu"]
    st.subheader(f"Structura salariatilor pe activitati economice in anul {an_num}")

    # Checkbox pentru a afisa detaliile pentru categoriile sub 5%
    show_detail_alte = st.checkbox("Afiseaza detaliu pentru Alte Industrii (categorii < 5%)", value=False)

    # Creeaza coloana cu activitatea prescurtata
    df['Activitate'] = df['Activitati ale economiei'].apply(prescurteaza_activitate)

    for judet in judete:
        df_judet = df[df['Judete'] == judet]
        total_judet = df_judet[an_selectat].sum()
        # Identifica categoriile mici sub 5%
        df_other = df_judet[df_judet[an_selectat] < total_judet * 0.05]
        # Categoriile principale (>=5%)
        df_main = df_judet[df_judet[an_selectat] >= total_judet * 0.05].copy()
        valoare_other = df_other[an_selectat].sum()
        # Adauga categoria "Alte industrii" in df_main daca exista valori in df_other
        if valoare_other > 0:
            df_main = pd.concat([
                df_main,
                pd.DataFrame([{'Activitate': 'Alte industrii', an_selectat: valoare_other}])
            ], ignore_index=True)

        if not show_detail_alte:
            # Afiseaza graficul principal cu "Alte industrii" grupate
            fig = px.pie(
                df_main,
                names='Activitate',
                values=an_selectat,
                title=f"{judet}",
                width=800, height=600,
                color_discrete_sequence=PALETA,
                hole=0.3
            )
            fig.update_traces(
                textinfo='percent+label',
                textposition='inside',
                textfont=dict(size=14, family="Segoe UI", color="white"),
                insidetextfont=dict(size=14, family="Segoe UI", color="white"),
                showlegend=True,
                marker_line=dict(width=2, color='white')
            )
            fig.update_layout(
                title=dict(font=dict(size=20)),
                legend=dict(font=dict(size=12))
            )
            st.plotly_chart(fig, use_container_width=True)
            st.markdown(f"#### Tabel cu datele pentru {judet} - Categorii grupate")
            st.dataframe(df_main.set_index('Activitate')[[an_selectat]])
            st.divider()
        else:
            # Afiseaza graficul detaliat pentru categoriile sub 5%
            if df_other.empty:
                st.write(f"Pentru judetul {judet}, nu exista categorii sub 5%.")
                st.divider()
            else:
                fig_other = px.pie(
                    df_other,
                    names='Activitate',
                    values=an_selectat,
                    title=f"{judet} - Alte industrii detaliat",
                    width=800, height=600,
                    color_discrete_sequence=PALETA,
                    hole=0.3
                )
                fig_other.update_traces(
                    textinfo='percent+label',
                    textposition='inside',
                    textfont=dict(size=14, family="Segoe UI", color="white"),
                    insidetextfont=dict(size=14, family="Segoe UI", color="white"),
                    showlegend=True,
                    marker_line=dict(width=2, color='white')
                )
                fig_other.update_layout(
                    title=dict(font=dict(size=20)),
                    legend=dict(font=dict(size=12))
                )
                st.plotly_chart(fig_other, use_container_width=True)
                st.markdown(f"#### Tabel cu datele pentru {judet} - Alte industrii detaliat")
                st.dataframe(df_other.set_index('Activitate')[[an_selectat]])
                st.divider()

    st.markdown("### Legenda activitati economice")
    # Afiseaza legenda pentru prescurtari activitati
    st.markdown(
        "\n".join([f"- **{prescurtare}**: {activitate}" for activitate, prescurtare in PRESCURTARI_ACTIVITATI.items()])
    )
    st.divider()

def pie_chart_public_privat(df_analiza, an, doar_centru):
    # Creeaza pie chart pentru distributia publica vs privata
    st.subheader("Distributia generala publica vs privata")
    
    # Calculeaza totalurile generale
    total_salariati_publici = df_analiza['Salariati_publici'].sum()
    total_salariati_general = df_analiza['Total_salariati'].sum()
    total_salariati_privati = total_salariati_general - total_salariati_publici
    
    procent_public_general = (total_salariati_publici / total_salariati_general) * 100
    procent_privat_general = (total_salariati_privati / total_salariati_general) * 100
    
    # Creaza DataFrame pentru pie chart
    df_pie = pd.DataFrame({
        'Sector': ['Public', 'Privat'],
        'Numar_salariati': [total_salariati_publici, total_salariati_privati],
        'Procent': [procent_public_general, procent_privat_general]
    })
    
    # Creaza pie chart cu Plotly
    fig = px.pie(
        df_pie,
        names='Sector',
        values='Numar_salariati',
        title=f"Distributia salariatilor public vs privat in anul {an.split()[-1]} - {'Regiunea Centru' if doar_centru else 'Romania'}",
        color_discrete_sequence=['#c72a2a', '#f5c3ba'],
        width=800,
        height=600
    )
    
    fig.update_traces(
        textinfo='label+percent+value',
        textfont=dict(size=16),
        marker_line=dict(width=2, color='white'),
        hovertemplate='<b>%{label}</b><br>' +
                     'Numar salariati: %{value:,.0f}<br>' +
                     'Procent: %{percent}<br>' +
                     '<extra></extra>'
    )
    
    fig.update_layout(
        title=dict(font=dict(size=20)),
        legend=dict(font=dict(size=16)),
        font=dict(family="Segoe UI, Arial", size=14)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Afiseaza comparatie pe judete
    st.markdown("#### Comparatie pe judete")
    df_comparatie = df_analiza[['Judete', 'Procent_public', 'Procent_privat']].copy()
    df_comparatie = df_comparatie.sort_values('Procent_public', ascending=False)
    df_comparatie['Procent_public'] = df_comparatie['Procent_public'].round(1)
    df_comparatie['Procent_privat'] = df_comparatie['Procent_privat'].round(1)
    df_comparatie = df_comparatie.rename(columns={
        'Procent_public': 'Procent public (%)',
        'Procent_privat': 'Procent privat (%)'
    })
    st.dataframe(df_comparatie.set_index('Judete'))

def choropleth_public_privat(df_analiza, geo_data, geo_type, an, doar_centru):
    # Creeaza choropleth map pentru procentul de salariati publici
    st.subheader("Procentul de salariati din sectorul public - Harta interactiva")
    
    # Prima parte: Harta animata pentru toti anii
    st.markdown("#### Evoluția în timp - Animație")
    choropleth_animat_public_privat(geo_data, geo_type, doar_centru)
    st.divider()
    st.markdown("#### Harta detaliată pentru anul selectat")
    
    # Coordonatele ajustate ale centrelor judetelor din regiunea Centru
    coordonate_judete = {
        'Alba': (46.0667, 23.5833),
        'Brasov': (45.6500, 25.6000),
        'Covasna': (45.8667, 26.1833),
        'Harghita': (46.3600, 25.8000),
        'Mures': (46.5500, 24.5667),
        'Sibiu': (45.7833, 24.1500)
    }
    
    # Adauga prescurtari pentru judete
    prescurtari_judete = {
        'Alba': 'AB',
        'Brasov': 'BV', 
        'Covasna': 'CV',
        'Harghita': 'HR',
        'Mures': 'MS',
        'Sibiu': 'SB'
    }
    
    df_analiza['Prescurtare'] = df_analiza['Judete'].map(prescurtari_judete)
    
    # Creeaza harta cu Plotly
    if geo_type == 'geojson':
        fig = px.choropleth(
            df_analiza,
            geojson=geo_data,
            locations='Judete_std',
            color='Procent_public',
            hover_name='Judete',
            hover_data={
                'Procent_public': ':.1f',
                'Salariati_publici': ':,.0f',
                'Total_salariati': ':,.0f'
            },
            featureidkey="properties.name",
            projection="mercator",
            color_continuous_scale="Reds",
            range_color=[10, 25],
            title=f"Procentul de salariati din sectorul public in anul {an.split()[-1]} - {'Regiunea Centru' if doar_centru else 'Romania'}"
        )
        
        # Adauga textul pentru fiecare judet DOAR daca este selectata regiunea Centru
        if doar_centru:
            for _, row in df_analiza.iterrows():
                if row['Judete'] in coordonate_judete and pd.notna(row['Prescurtare']):
                    lat, lon = coordonate_judete[row['Judete']]
                    text_afisare = f"{row['Prescurtare']}<br>{row['Procent_public']:.1f}%"
                    
                    fig.add_scattergeo(
                        lat=[lat],
                        lon=[lon],
                        text=[text_afisare],
                        mode='text',
                        textfont=dict(
                            size=12,
                            color="white",
                            family="Arial Black"
                        ),
                        textposition='middle center',
                        showlegend=False,
                        hoverinfo='skip'
                    )

    fig.update_geos(
        fitbounds="locations",
        visible=False,
        bgcolor="rgba(0,0,0,0)"
    )
    fig.update_layout(
        width=1400,
        height=1000,
        title=dict(font=dict(size=20)),
        coloraxis_colorbar=dict(title="Procent salariati publici (%)"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    st.plotly_chart(fig, use_container_width=True)
    
    # Afiseaza tabelul cu datele
    st.markdown("#### Datele afisate pe harta")
    df_display = df_analiza[['Judete', 'Procent_public', 'Procent_privat', 'Salariati_publici', 'Total_salariati']].copy()
    df_display['Procent_public'] = df_display['Procent_public'].round(1)
    df_display['Procent_privat'] = df_display['Procent_privat'].round(1)
    df_display = df_display.rename(columns={
        'Procent_public': 'Procent public (%)',
        'Procent_privat': 'Procent privat (%)',
        'Salariati_publici': 'Salariati publici',
        'Total_salariati': 'Total salariati'
    })
    st.dataframe(df_display.set_index('Judete'))

def choropleth_animat_public_privat(geo_data, geo_type, doar_centru):
    # Creeaza harta animata pentru evolutia in timp
    
    # Incarca datele de salariati
    df_salariati = incarca_date('Salariati2')
    df_salariati = replace_total_with_romania(df_salariati)
    
    # Selecteaza anii disponibili
    ani = sorted([col for col in df_salariati.columns if col.startswith('Anul')],
                 key=lambda x: int(x.split()[-1]))
    
    # Defineste activitatile publice
    activitati_publice = [
        'O ADMINISTRATIE PUBLICA SI APARARE; ASIGURARI SOCIALE DIN SISTEMUL PUBLIC',
        'P INVATAMANT',
        'Q SANATATE SI ASISTENTA SOCIALA'
    ]
    
    # Prepara datele pentru animatie
    df_animatie_lista = []
    
    for an in ani:
        an_num = an.split()[-1]
        
        # Filtreaza si pregateste datele pentru anul curent
        df_filtrat = filtreaza_judete_pentru_harta(df_salariati, doar_centru)
        df_filtrat = converteste_ani_la_float(df_filtrat, [an])
        
        # Calculeaza totalul de salariati pe judete
        df_total = df_filtrat.groupby('Judete')[an].sum().reset_index()
        df_total = df_total.rename(columns={an: 'Total_salariati'})
        
        # Calculeaza salariati din sectorul public
        df_public = df_filtrat[df_filtrat['Activitati ale economiei'].isin(activitati_publice)]
        df_public_total = df_public.groupby('Judete')[an].sum().reset_index()
        df_public_total = df_public_total.rename(columns={an: 'Salariati_publici'})
        
        # Uneste datele si calculeaza procentul
        df_an = df_total.merge(df_public_total, on='Judete', how='left')
        df_an['Salariati_publici'] = df_an['Salariati_publici'].fillna(0)
        df_an['Procent_public'] = (df_an['Salariati_publici'] / df_an['Total_salariati']) * 100
        df_an['Judete_std'] = df_an['Judete'].apply(standardizeaza_nume_judete)
        df_an['An'] = an_num
        
        df_animatie_lista.append(df_an)
    
    # Combina toate datele intr-un singur DataFrame
    df_animatie = pd.concat(df_animatie_lista, ignore_index=True)
    
    # Creeaza harta animata
    if geo_type == 'geojson':
        fig_animat = px.choropleth(
            df_animatie,
            geojson=geo_data,
            locations='Judete_std',
            color='Procent_public',
            animation_frame='An',
            hover_name='Judete',
            hover_data={
                'Procent_public': ':.1f',
                'Salariati_publici': ':,.0f',
                'Total_salariati': ':,.0f',
                'An': False
            },
            featureidkey="properties.name",
            projection="mercator",
            color_continuous_scale="Reds",
            range_color=[10, 25],
            title=f"Evoluția procentului de salariați din sectorul public în timp - {'Regiunea Centru' if doar_centru else 'Romania'}"
        )
        
        # Configurari pentru animatie
        fig_animat.update_geos(
            fitbounds="locations",
            visible=False,
            bgcolor="rgba(0,0,0,0)"
        )
        
        fig_animat.update_layout(
            width=1400,
            height=900,
            title=dict(font=dict(size=18)),
            coloraxis_colorbar=dict(title="Procent salariati publici (%)"),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        
        # Configurari pentru butoanele de animatie
        fig_animat.layout.updatemenus = [
            dict(
                type="buttons",
                direction="left",
                pad={"r": 10, "t": 87},
                showactive=False,
                x=0.011,
                xanchor="right",
                y=0,
                yanchor="top",
                buttons=[
                    dict(
                        label="▶️ Play",
                        method="animate",
                        args=[None, {"frame": {"duration": 1500, "redraw": True},
                                    "fromcurrent": True, 
                                    "transition": {"duration": 300}}]
                    ),
                    dict(
                        label="⏸️ Pause",
                        method="animate",
                        args=[[None], {"frame": {"duration": 0, "redraw": False},
                                      "mode": "immediate",
                                      "transition": {"duration": 0}}]
                    )
                ]
            )
        ]
        
        # Configurari pentru slider-ul de animatie
        fig_animat.layout.sliders = [dict(
            active=0,
            yanchor="top",
            xanchor="left",
            currentvalue=dict(
                font=dict(size=16), 
                prefix="Anul: ",
                visible=True,
                xanchor="right"
            ),
            transition=dict(duration=300, easing="cubic-in-out"),
            pad=dict(b=10, t=50),
            len=0.9,
            x=0.1,
            y=0,
            steps=[dict(
                args=[[f.name], dict(
                    frame=dict(duration=300, redraw=True),
                    mode="immediate",
                    transition=dict(duration=300)
                )],
                label=f.name,
                method="animate"
            ) for f in fig_animat.frames]
        )]
    
    st.plotly_chart(fig_animat, use_container_width=True)

def analiza_spatiala_public_privat():
    # Analiza spatiala pentru salariati public vs privat
    st.header("Analiza spatiala - Sectorul public vs privat")
    # Incarca datele geografice
    geo_data, geo_type = incarca_date_geografice()
    if geo_data is None:
        st.error("Nu s-au putut incarca datele geografice.")
        return
    # Incarca datele de salariati
    df_salariati = incarca_date('Salariati2')
    df_salariati = replace_total_with_romania(df_salariati)
    # Selecteaza parametrii
    ani = sorted([col for col in df_salariati.columns if col.startswith('Anul')],
                 key=lambda x: int(x.split()[-1]), reverse=True)
    an = st.selectbox("Alege anul:", ani, index=0)
    doar_centru = st.checkbox("Afiseaza doar regiunea Centru", value=True)
    
    # Defineste activitatile publice
    activitati_publice = [
        'O ADMINISTRATIE PUBLICA SI APARARE; ASIGURARI SOCIALE DIN SISTEMUL PUBLIC',
        'P INVATAMANT',
        'Q SANATATE SI ASISTENTA SOCIALA'
    ]
    # Filtreaza si pregateste datele pentru anul curent
    df_filtrat = filtreaza_judete_pentru_harta(df_salariati, doar_centru)
    df_filtrat = converteste_ani_la_float(df_filtrat, [an])
    # Calculeaza totalul de salariati pe judete pentru anul curent
    df_total = df_filtrat.groupby('Judete')[an].sum().reset_index()
    df_total = df_total.rename(columns={an: 'Total_salariati'})
    # Calculeaza salariati din sectorul public pentru anul curent
    df_public = df_filtrat[df_filtrat['Activitati ale economiei'].isin(activitati_publice)]
    df_public_total = df_public.groupby('Judete')[an].sum().reset_index()
    df_public_total = df_public_total.rename(columns={an: 'Salariati_publici'})
    # Uneste datele si calculeaza procentul pentru anul curent
    df_analiza = df_total.merge(df_public_total, on='Judete', how='left')
    df_analiza['Salariati_publici'] = df_analiza['Salariati_publici'].fillna(0)
    df_analiza['Procent_public'] = (df_analiza['Salariati_publici'] / df_analiza['Total_salariati']) * 100
    df_analiza['Procent_privat'] = 100 - df_analiza['Procent_public']
    df_analiza['Judete_std'] = df_analiza['Judete'].apply(standardizeaza_nume_judete)
    # Calculeaza statisticile pentru anul curent
    total_salariati_publici = df_analiza['Salariati_publici'].sum()
    total_salariati_general = df_analiza['Total_salariati'].sum()
    total_salariati_privati = total_salariati_general - total_salariati_publici
    procent_public_general = (total_salariati_publici / total_salariati_general) * 100
    procent_privat_general = (total_salariati_privati / total_salariati_general) * 100
    # Calculeaza cresterea fata de anul precedent
    an_curent = int(an.split()[-1])
    an_precedent_str = f"Anul {an_curent - 1}"
    if an_curent == 2010:
        # Pentru 2010, nu avem date din 2009
        delta_public = "N/A - nu sunt date din 2009"
        delta_privat = "N/A - nu sunt date din 2009"
        delta_total = "N/A - nu sunt date din 2009"
    elif an_precedent_str in df_salariati.columns:
        # Calculeaza pentru anul precedent
        df_filtrat_prec = filtreaza_judete_pentru_harta(df_salariati, doar_centru)
        df_filtrat_prec = converteste_ani_la_float(df_filtrat_prec, [an_precedent_str])
        # Total pentru anul precedent
        df_total_prec = df_filtrat_prec.groupby('Judete')[an_precedent_str].sum().reset_index()
        total_salariati_general_prec = df_total_prec[an_precedent_str].sum()
        # Public pentru anul precedent
        df_public_prec = df_filtrat_prec[df_filtrat_prec['Activitati ale economiei'].isin(activitati_publice)]
        df_public_total_prec = df_public_prec.groupby('Judete')[an_precedent_str].sum().reset_index()
        total_salariati_publici_prec = df_public_total_prec[an_precedent_str].sum()
        # Privat pentru anul precedent
        total_salariati_privati_prec = total_salariati_general_prec - total_salariati_publici_prec
        
        # Calculeaza cresterea procentuala
        if total_salariati_publici_prec > 0:
            crestere_public = ((total_salariati_publici - total_salariati_publici_prec) / total_salariati_publici_prec) * 100
            delta_public = f"{crestere_public:+.1f}%"
        else:
            delta_public = "N/A"
            
        if total_salariati_privati_prec > 0:
            crestere_privat = ((total_salariati_privati - total_salariati_privati_prec) / total_salariati_privati_prec) * 100
            delta_privat = f"{crestere_privat:+.1f}%"
        else:
            delta_privat = "N/A"
            
        if total_salariati_general_prec > 0:
            crestere_total = ((total_salariati_general - total_salariati_general_prec) / total_salariati_general_prec) * 100
            delta_total = f"{crestere_total:+.1f}%"
        else:
            delta_total = "N/A"
    else:
        # Anul precedent nu există în date
        delta_public = "N/A - nu sunt date disponibile"
        delta_privat = "N/A - nu sunt date disponibile"
        delta_total = "N/A - nu sunt date disponibile"
    
    # Afiseaza statistici sumare la inceput
    st.markdown("#### Statistici sumare")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Salariati sector public", 
            f"{total_salariati_publici:,.0f}", 
            delta_public
        )
    with col2:
        st.metric(
            "Salariati sector privat", 
            f"{total_salariati_privati:,.0f}", 
            delta_privat
        )
    with col3:
        st.metric(
            "Total salariati", 
            f"{total_salariati_general:,.0f}", 
            delta_total
        )
    # Explicatie scurta cu verde
    st.markdown(
        """
        <div style="color:#28a745;font-weight:bold;margin:15px 0;">
        Procentul reprezintă creșterea salariaților față de anul precedent.
        </div>
        """,
        unsafe_allow_html=True
    )
    st.divider()
    # Afiseaza harta choropleth
    choropleth_public_privat(df_analiza, geo_data, geo_type, an, doar_centru)
    # Afiseaza pie chart cu distributia generala
    pie_chart_public_privat(df_analiza, an, doar_centru)

def analiza_regresie():
    # Analiza de regresie pentru date de tip panel realizata in R
    st.header("Analiza de regresie pentru date de tip panel")
    st.info(
        "Această analiză de regresie pentru date de tip panel a fost realizată în R, "
        "folosind datele economice și demografice din Regiunea Centru a României. "
        "Datele au fost standardizate folosind funcția scale() din R."
    )
    
    # Explicația despre metodologia folosită
    st.markdown("#### Metodologia analizei")
    st.markdown("""
    **Selecția variabilelor:** Variabilele au fost alese în funcție de matricea de corelație 
    care a fost creată cu ajutorul unui script în R. Matricea de corelație a evidențiat 
    relațiile semnificative între variabilele economice și demografice.
    
    **Compararea modelelor:** Modelele au fost comparate folosind:
    - **Hausman Test** pentru alegerea între Fixed Effects și Random Effects
    - **Compararea R-squared** pentru evaluarea puterii explicative a modelelor
    
    **Standardizarea datelor:** Toate variabilele au fost standardizate folosind funcția `scale()` 
    din R pentru a permite compararea directă a coeficienților.
    """)
    
    # Afișarea matricei de corelație
    st.markdown("#### Matricea de corelație")
    st.markdown("Matricea de corelație utilizată pentru selecția variabilelor:")
    
    try:
        from PIL import Image
        image = Image.open('matrice_corelatie.png')
        st.image(image, caption='Matricea de corelație între variabilele economice și demografice', 
                width=600)
    except:
        st.error("Nu s-a putut încărca imaginea cu matricea de corelație (matrice_corelatie.png)")
    
    st.markdown("---")
    
    # Rezultatele analizei din R
    st.markdown("#### Rezultatele analizei de regresie")
    st.markdown("Rezultatele obținute din analiza efectuată în R:")
    
    # Afișarea rezultatelor formatate
    st.code("""
=== MODELUL 1: FIXED EFFECTS ===
Oneway (individual) effect Within Model

Call:
plm(formula = Salariu ~ Imigranti + Rata_Somaj + Rata_Ocupare + 
    Pop_Activa, data = panel_pdata, model = "within")

Balanced Panel: n = 42, T = 13, N = 546

Residuals:
     Min.   1st Qu.    Median   3rd Qu.      Max. 
-1.548817 -0.394844 -0.084152  0.331147  2.691460 

Coefficients:
              Estimate Std. Error  t-value  Pr(>|t|)    
Imigranti     0.276490   0.046662   5.9253 5.808e-09 ***
Rata_Somaj   -1.112099   0.054922 -20.2485 < 2.2e-16 ***
Rata_Ocupare  0.042407   0.062213   0.6816  0.495783    
Pop_Activa   -1.037893   0.326945  -3.1745  0.001593 ** 
---
Signif. codes:  0 '***' 0.001 '**' 0.01 '*' 0.05 '.' 0.1 ' ' 1

Total Sum of Squares:    467.72
Residual Sum of Squares: 168.26
R-Squared:      0.64026
Adj. R-Squared: 0.60789
F-statistic: 222.475 on 4 and 500 DF, p-value: < 2.22e-16

=== MODELUL 2: RANDOM EFFECTS ===
Oneway (individual) effect Random Effect Model 
   (Swamy-Arora's transformation)

Call:
plm(formula = Salariu ~ Imigranti + Rata_Somaj + Rata_Ocupare + 
    Pop_Activa, data = panel_pdata, model = "random")

Balanced Panel: n = 42, T = 13, N = 546

Effects:
                  var std.dev share
idiosyncratic 0.33651 0.58010 0.937
individual    0.02257 0.15025 0.063
theta: 0.2691

Residuals:
     Min.   1st Qu.    Median   3rd Qu.      Max. 
-1.977198 -0.553702 -0.072856  0.525829  2.463928 

Coefficients:
                Estimate  Std. Error  z-value  Pr(>|z|)    
(Intercept)  -5.1074e-16  4.1809e-02   0.0000  1.000000    
Imigranti     3.1267e-01  4.2487e-02   7.3592  1.85e-13 ***
Rata_Somaj   -7.2608e-01  4.1321e-02 -17.5715 < 2.2e-16 ***
Rata_Ocupare  2.6614e-02  4.8461e-02   0.5492  0.582880    
Pop_Activa   -1.4790e-01  5.4560e-02  -2.7108  0.006711 ** 
---
Signif. codes:  0 '***' 0.001 '**' 0.01 '*' 0.05 '.' 0.1 ' ' 1

Total Sum of Squares:    509
Residual Sum of Squares: 275.8
R-Squared:      0.45816
Adj. R-Squared: 0.45415
Chisq: 457.444 on 4 DF, p-value: < 2.22e-16

============================================================
COMPARAREA MODELELOR
============================================================

1. HAUSMAN TEST (Fixed Effects vs Random Effects):
H0: Random Effects model este preferat
H1: Fixed Effects model este preferat

	Hausman Test

data:  Salariu ~ Imigranti + Rata_Somaj + Rata_Ocupare + Pop_Activa
chisq = 157.27, df = 4, p-value < 2.2e-16
alternative hypothesis: one model is inconsistent

Rezultat: Fixed Effects model este preferat (p < 0.05)

2. COMPARAREA R-SQUARED:
Fixed Effects R-squared: 0.6403 
Random Effects R-squared: 0.4582 
""", language="")
    
    # Interpretarea rezultatelor
    st.markdown("#### Interpretarea rezultatelor")
    st.markdown("""
    **Modelul selectat:** Pe baza Hausman Test (p < 2.2e-16), modelul **Fixed Effects** 
    este preferat față de modelul Random Effects.
    
    **Puterea explicativă:** Modelul Fixed Effects explică **64.03%** din variația 
    salariului (R-squared = 0.6403), comparativ cu **45.82%** pentru modelul Random Effects.
    
    **Variabile semnificative:**
    - **Imigranti** (p = 5.808e-09): Efect pozitiv semnificativ
    - **Rata_Somaj** (p < 2.2e-16): Efect negativ puternic semnificativ  
    - **Pop_Activa** (p = 0.001593): Efect negativ semnificativ
    - **Rata_Ocupare** (p = 0.495783): Nu este semnificativ statistic
    """)  

def pagina_principala():
    # Pagina de landing cu design modern și estetic
    
    # Import font modern
    st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        .main-font {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header principal cu design modern
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 60px 40px; border-radius: 20px; margin-bottom: 50px; text-align: center;
                box-shadow: 0 20px 40px rgba(102, 126, 234, 0.3);" class="main-font">
        <h1 style="color: white; font-size: 3.5em; margin-bottom: 20px; font-weight: 700; 
                   letter-spacing: -2px; text-shadow: 0 4px 8px rgba(0,0,0,0.2);">
            📊 Analiza Pieței Muncii
        </h1>
        <h2 style="color: rgba(255,255,255,0.9); font-size: 1.8em; font-weight: 400; 
                   margin-bottom: 0; letter-spacing: 0.5px;">
            Regiunea Centru - România
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Sectiune descriere aplicatie
    st.markdown("""
    <div style="background: linear-gradient(145deg, #f8fafc, #ffffff); 
                padding: 40px; border-radius: 16px; margin-bottom: 50px; 
                border: 1px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05);" class="main-font">
        <h3 style="color: #1e293b; margin-bottom: 25px; font-weight: 600; font-size: 1.8em;">
            🎯 Despre această aplicație
        </h3>
        <p style="font-size: 1.2em; line-height: 1.8; color: #475569; text-align: justify; 
                  font-weight: 400; margin: 0;">
            Această aplicație oferă un suport vizual în cadrul unei analize a pieței muncii din 
            <strong style="color: #3b82f6;">Regiunea Centru a României </strong>
            (Alba, Brașov, Covasna, Harghita, Mureș și Sibiu). Prin intermediul unor 
            grafice interactive și analize statistice avansate, utilizatorii pot explora evoluția 
            în timp a diferitelor date economice și demografice.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sectiune caracteristici principale - titlu mai vizibil
    st.markdown("""
    <div style="text-align: center; margin: 60px 0 40px 0;" class="main-font">
        <h2 style="background: linear-gradient(135deg, #3b82f6, #1d4ed8); 
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                   background-clip: text; font-size: 2.5em; font-weight: 700; 
                   margin-bottom: 10px; letter-spacing: -1px;">
            ⭐ Caracteristicile principale
        </h2>
        <div style="width: 100px; height: 4px; background: linear-gradient(135deg, #3b82f6, #1d4ed8); 
                    margin: 0 auto; border-radius: 2px;"></div>
    </div>
    """, unsafe_allow_html=True)
    
    # Grid cu caracteristici - design modern
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #3b82f6, #1e40af); 
                    padding: 35px 25px; border-radius: 20px; text-align: center; height: 240px; 
                    display: flex; flex-direction: column; justify-content: center;
                    box-shadow: 0 10px 25px rgba(59, 130, 246, 0.3);
                    transition: transform 0.3s ease;" class="main-font">
            <div style="font-size: 3.5em; margin-bottom: 20px;">📈</div>
            <h4 style="color: white; margin-bottom: 15px; font-weight: 600; font-size: 1.3em;">
                Analize temporale
            </h4>
            <p style="color: rgba(255,255,255,0.9); font-size: 1em; line-height: 1.5; margin: 0;">
                Urmărirea evoluției indicatorilor în timp prin grafice interactive
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #10b981, #047857); 
                    padding: 35px 25px; border-radius: 20px; text-align: center; height: 240px;
                    display: flex; flex-direction: column; justify-content: center;
                    box-shadow: 0 10px 25px rgba(16, 185, 129, 0.3);
                    transition: transform 0.3s ease;" class="main-font">
            <div style="font-size: 3.5em; margin-bottom: 20px;">🗺️</div>
            <h4 style="color: white; margin-bottom: 15px; font-weight: 600; font-size: 1.3em;">
                Analize spațiale
            </h4>
            <p style="color: rgba(255,255,255,0.9); font-size: 1em; line-height: 1.5; margin: 0;">
                Vizualizări pe hartă pentru comparații între județe
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #8b5cf6, #7c3aed); 
                    padding: 35px 25px; border-radius: 20px; text-align: center; height: 240px;
                    display: flex; flex-direction: column; justify-content: center;
                    box-shadow: 0 10px 25px rgba(139, 92, 246, 0.3);
                    transition: transform 0.3s ease;" class="main-font">
            <div style="font-size: 3.5em; margin-bottom: 20px;">🔬</div>
            <h4 style="color: white; margin-bottom: 15px; font-weight: 600; font-size: 1.3em;">
                Statistici avansate
            </h4>
            <p style="color: rgba(255,255,255,0.9); font-size: 1em; line-height: 1.5; margin: 0;">
                Analize de corelație și modele de regresie multiplă
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Sectiune indicatori și tipuri de analiză - carduri complete
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="background: linear-gradient(145deg, #ffffff, #f8fafc); 
                    padding: 35px; border-radius: 20px; height: 420px;
                    border: 1px solid #e2e8f0; box-shadow: 0 8px 25px rgba(0,0,0,0.08);
                    overflow-y: auto;" class="main-font">
            <h4 style="color: #1e293b; margin-bottom: 30px; font-weight: 600; font-size: 1.5em; 
                       display: flex; align-items: center;">
                <span style="margin-right: 10px;">📋</span> Indicatori disponibili
            </h4>
            <div style="space-y: 15px;">
                <div style="margin-bottom: 18px; padding: 12px; background: #f1f5f9; border-radius: 10px;">
                    <span style="color: #3b82f6; font-weight: 600;">💼 Piața muncii:</span>
                    <span style="color: #475569; margin-left: 8px;">Rata șomajului, Rata de ocupare a resurselor de muncă</span>
                </div>
                <div style="margin-bottom: 18px; padding: 12px; background: #f1f5f9; border-radius: 10px;">
                    <span style="color: #10b981; font-weight: 600;">👥 Populația:</span>
                    <span style="color: #475569; margin-left: 8px;">Populația activă, Imigranți definitivi</span>
                </div>
                <div style="margin-bottom: 18px; padding: 12px; background: #f1f5f9; border-radius: 10px;">
                    <span style="color: #8b5cf6; font-weight: 600;">🎓 Educația:</span>
                    <span style="color: #475569; margin-left: 8px;">Numărul absolvenților pe niveluri de educație</span>
                </div>
                <div style="margin-bottom: 18px; padding: 12px; background: #f1f5f9; border-radius: 10px;">
                    <span style="color: #f59e0b; font-weight: 600;">💰 Economia:</span>
                    <span style="color: #475569; margin-left: 8px;">PIB regional pe locuitor, Salariați pe activități economice, Câștigul salarial mediu net</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: linear-gradient(145deg, #ffffff, #f8fafc); 
                    padding: 35px; border-radius: 20px; height: 420px;
                    border: 1px solid #e2e8f0; box-shadow: 0 8px 25px rgba(0,0,0,0.08);
                    overflow-y: auto;" class="main-font">
            <h4 style="color: #1e293b; margin-bottom: 30px; font-weight: 600; font-size: 1.5em; 
                       display: flex; align-items: center;">
                <span style="margin-right: 10px;">🛠️</span> Tipuri de analiză
            </h4>
            <div style="space-y: 15px;">
                <div style="margin-bottom: 18px; padding: 12px; background: #fef3c7; border-radius: 10px;">
                    <span style="color: #92400e; font-weight: 600;">📊 Grafice de evoluție</span>
                    <span style="color: #78350f; margin-left: 8px;">în timp</span>
                </div>
                <div style="margin-bottom: 18px; padding: 12px; background: #dbeafe; border-radius: 10px;">
                    <span style="color: #1e40af; font-weight: 600;">🗺️ Hărți coropletice</span>
                    <span style="color: #1e3a8a; margin-left: 8px;">interactive</span>
                </div>
                <div style="margin-bottom: 18px; padding: 12px; background: #dcfce7; border-radius: 10px;">
                    <span style="color: #15803d; font-weight: 600;">🔥 Hărți termice</span>
                    <span style="color: #14532d; margin-left: 8px;">pentru comparații</span>
                </div>
                <div style="margin-bottom: 18px; padding: 12px; background: #fce7f3; border-radius: 10px;">
                    <span style="color: #be185d; font-weight: 600;">🥧 Grafice circulare</span>
                    <span style="color: #9d174d; margin-left: 8px;">pentru structuri</span>
                </div>
                <div style="margin-bottom: 18px; padding: 12px; background: #ede9fe; border-radius: 10px;">
                    <span style="color: #7c3aed; font-weight: 600;">📈 Diagrame de dispersie</span>
                    <span style="color: #6d28d9; margin-left: 8px;">pentru corelații</span>
                </div>
                <div style="margin-bottom: 0; padding: 12px; background: #f0fdfa; border-radius: 10px;">
                    <span style="color: #0f766e; font-weight: 600;">📋 Statistici descriptive</span>
                    <span style="color: #134e4a; margin-left: 8px;">și teste</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Sectiune sursa datelor - design modern
    st.markdown("""
    <div style="background: linear-gradient(135deg, #ec4899, #be185d); 
                padding: 40px; border-radius: 20px; margin: 50px 0; text-align: center;
                box-shadow: 0 20px 40px rgba(236, 72, 153, 0.3);" class="main-font">
        <h3 style="color: white; margin-bottom: 25px; font-weight: 600; font-size: 1.8em;
                   display: flex; align-items: center; justify-content: center;">
            <span style="margin-right: 15px;">📊</span> Sursa datelor
        </h3>
        <p style="color: white; font-size: 1.4em; margin-bottom: 20px; font-weight: 600;">
            Institutul Național de Statistică (INS)
        </p>
        <p style="color: rgba(255,255,255,0.9); font-size: 1.1em; margin-bottom: 15px; font-weight: 400;">
            Datele sunt preluate prin intermediul platformei
        </p>
        <p style="color: white; font-size: 1.6em; font-weight: 700; margin-bottom: 10px;">
            TEMPO Online
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sectiune perioada de acoperire - design modern
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1f2937, #374151); 
                padding: 40px; border-radius: 20px; margin-top: 40px;
                box-shadow: 0 20px 40px rgba(31, 41, 55, 0.4);" class="main-font">
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 30px; text-align: center;">
            <div style="color: white;">
                <div style="font-size: 3em; margin-bottom: 15px;">📅</div>
                <h4 style="margin-bottom: 10px; font-weight: 600; font-size: 1.3em;">Perioada</h4>
                <p style="font-weight: 500; font-size: 1.2em; color: #9ca3af; margin: 0;">2010 - 2023</p>
            </div>
            <div style="color: white;">
                <div style="font-size: 3em; margin-bottom: 15px;">🌍</div>
                <h4 style="margin-bottom: 10px; font-weight: 600; font-size: 1.3em;">Acoperire</h4>
                <p style="font-weight: 500; font-size: 1.2em; color: #9ca3af; margin: 0;">Regiunea Centru</p>
            </div>
            <div style="color: white;">
                <div style="font-size: 3em; margin-bottom: 15px;">⚡</div>
                <h4 style="margin-bottom: 10px; font-weight: 600; font-size: 1.3em;">Frecvență</h4>
                <p style="font-weight: 500; font-size: 1.2em; color: #9ca3af; margin: 0;">Date anuale</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def analiza_absolventi_evolutie():
    # Analiza evolutiei numarului total de absolventi
    st.header("Evolutia numarului total de absolventi")
    st.info("Acest grafic arata evolutia numarului total de absolventi in timp pentru fiecare judet din regiunea Centru. "
            "Linia alba punctata reprezinta media pe judete din regiunea Centru.")
    
    df = incarca_date('Absolventi')
    ani = sorted([col for col in df.columns if col.startswith('Anul')],
                 key=lambda x: int(x.split()[-1]), reverse=True)
    
    # Filtreaza DOAR judetele din regiunea Centru (fara Romania)
    df_filtrat = df[df['Judete'].isin(['Alba', 'Brasov', 'Covasna', 'Harghita', 'Mures', 'Sibiu'])]
    
    # Converteste la float pentru calculele numerice
    df_filtrat = converteste_ani_la_float(df_filtrat, ani)
    
    # Calculeaza totalul de absolventi pe judete (suma tuturor nivelurilor de educatie)
    df_total = df_filtrat.groupby('Judete')[ani].sum().reset_index()
    
    # Calculeaza media pe judete pentru fiecare an pentru a obtine valoarea pentru Romania
    media_pe_ani = {}
    for an in ani:
        media_pe_ani[an] = df_total[an].mean()
    
    # Creaza o inregistrare pentru Romania cu mediile calculate
    df_romania = pd.DataFrame([{'Judete': 'Romania', **media_pe_ani}])
    
    # Combina datele judetelor cu Romania
    df_final = pd.concat([df_total, df_romania], ignore_index=True)
    
    grafic_linie_absolventi(df_final, ani, "Evolutia numarului total de absolventi", "Numar absolventi")

def grafic_linie_absolventi(df, ani, titlu, ylabel):
    # Creaza grafic linie pentru evolutia numarului de absolventi pe judete
    st.divider()
    ani_num = extrage_ani(ani)
    df = converteste_ani_la_float(df, ani)
    df_judete = df[df['Judete'] != 'Romania']
    
    fig = go.Figure()
    for idx, row in df_judete.iterrows():
        color = JUD_COLORS.get(row['Judete'], PALETA[idx % len(PALETA)])
        fig.add_trace(go.Scatter(
            x=ani_num,
            y=[row[an] for an in ani],
            mode='lines+markers',
            name=row['Judete'],
            text=[f"{row['Judete']}<br>{an}: {row[an]:.0f} absolventi" for an in ani],
            hoverinfo='text+y',
            line=dict(width=3, color=color),
            marker=dict(size=10, line=dict(width=1.5, color="#222"), color=color)
        ))
    
    # Adauga linia pentru media pe judete (Romania)
    df_romania = df[df['Judete'] == 'Romania']
    if not df_romania.empty:
        row = df_romania.iloc[0]
        fig.add_trace(go.Scatter(
            x=ani_num,
            y=[row[an] for an in ani],
            mode='lines+markers',
            name="Medie Romania",
            text=[f"Medie Romania<br>{an}: {row[an]:.0f} absolventi" for an in ani],
            hoverinfo='text+y',
            line=dict(width=5, color="#FFFFFF", dash='dot'),
            marker=dict(size=12, color="#FFFFFF", line=dict(width=2, color='black'))
        ))
    
    # Configurare aspect grafic
    fig.update_layout(
        width=1000, height=650,
        font=dict(family="Segoe UI, Arial", size=16),
        title=dict(text=titlu, font=dict(size=26)),
        xaxis_title=dict(text="Anul", font=dict(size=18)),
        yaxis_title=dict(text=ylabel, font=dict(size=18)),
        yaxis=dict(tickfont=dict(size=14)),
        xaxis=dict(tickfont=dict(size=14)),
        legend_title=dict(text="Judet", font=dict(size=16)),
        legend=dict(font=dict(size=14)),
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("#### Tabel cu datele")
    df_display = df.copy()
    df_display.loc[df_display['Judete'] == 'Romania', 'Judete'] = 'Romania'
    st.dataframe(df_display.set_index('Judete')[ani])
    st.divider()

def main():
    # Titlul aplicatiei Streamlit
    st.set_page_config(
        page_title="Analiza Pieței Muncii - Regiunea Centru",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.sidebar.title("Navigare")
    st.sidebar.markdown("---")
    
    # Meniul de optiuni din sidebar - design profesional fără emoji
    optiune = st.sidebar.radio(
        "Alege secțiunea:",
        (
            "Pagina principală",
            "Evoluție rată șomaj",
            "Evoluție PIB",
            "Evoluție absolvenți", 
            "Hartă termică șomaj",
            "Comparație rată șomaj",
            "Salariați pe activități (bare)",
            "Salariați pe activități (grafice circulare)",
            "Corelație șomaj-ocupare",
            "Structura absolvenți",
            "Statistici descriptive",
            "Analiză spațială",
            "Sectorul public vs privat",
            "Analiză de regresie"
        ),
        index=0
    )
    
    if optiune == "Pagina principală":
        pagina_principala()
        
    elif optiune == "Evoluție rată șomaj":
        st.header("Evolutia ratei somajului in regiunea Centru (grafic cu linii)")
        st.info("Acest grafic arata evolutia ratei somajului in timp pentru fiecare judet din regiunea Centru. "
                "Linia alba punctata reprezinta media nationala.")
        df = incarca_date('Somaj')
        ani = sorted([col for col in df.columns if col.startswith('Anul')],
                     key=lambda x: int(x.split()[-1]), reverse=True)
        sex = st.selectbox("Sex", df['Sexe'].unique())
        df_filtrat = df[(df['Sexe'] == sex) & ((df['Judete'].isin(['Alba', 'Brasov', 'Covasna',
                                                                    'Harghita', 'Mures', 'Sibiu'])) |
                                                (df['Judete'].str.upper() == 'TOTAL'))]
        grafic_linie_somaj(df_filtrat, ani, "Evolutia ratei somajului", "Rata somaj (%)")

    elif optiune == "Evoluție PIB":
        analiza_pib_evolutie()

    elif optiune == "Evoluție absolvenți":
        analiza_absolventi_evolutie()

    elif optiune == "Hartă termică șomaj":
        st.header("Comparatie rata somajului pe judete si ani (harta termica)")
        st.info("Harta termica permite compararea rapida a ratei somajului intre judete si ani.")
        df = incarca_date('Somaj')
        ani = sorted([col for col in df.columns if col.startswith('Anul')],
                     key=lambda x: int(x.split()[-1]), reverse=True)
        sex = st.selectbox("Sex", df['Sexe'].unique())
        df = df[(df['Sexe'] == sex) & ((df['Judete'].isin(['Alba', 'Brasov', 'Covasna',
                                                           'Harghita', 'Mures', 'Sibiu'])) |
                                        (df['Judete'].str.upper() == 'TOTAL'))]
        heatmap_judete_ani_interactiv(df, ani, "Harta termica rata somajului pe judete si ani")

    elif optiune == "Comparație rată șomaj":
        st.header("Top judete dupa rata somajului (grafic cu bare)")
        st.info("Acest grafic arata comparatia ratei somajului intre judete pentru anul selectat.")
        df = incarca_date('Somaj')
        ani = sorted([col for col in df.columns if col.startswith('Anul')],
                     key=lambda x: int(x.split()[-1]), reverse=True)
        sex = st.selectbox("Sex", df['Sexe'].unique())
        an = st.selectbox("An", ani, index=0)
        df = df[(df['Sexe'] == sex) & ((df['Judete'].isin(['Alba', 'Brasov', 'Covasna',
                                                           'Harghita', 'Mures', 'Sibiu'])) |
                                        (df['Judete'].str.upper() == 'TOTAL'))]
        bar_chart_an_interactiv(df, an, f"Rata somajului pe judete in {an.split()[-1]}", "Rata somaj (%)")

    elif optiune == "Salariați pe activități (bare)":
        st.header("Numar salariati pe activitati economice si judete (grafic cu bare)")
        st.info("Acest grafic arata distributia salariatilor pe activitati economice pentru fiecare judet.")
        df = incarca_date('Salariati2')
        ani = sorted([col for col in df.columns if col.startswith('Anul')],
                     key=lambda x: int(x.split()[-1]), reverse=True)
        an = st.selectbox("An", ani, index=0)
        df = df[(df['Judete'].isin(['Alba', 'Brasov', 'Covasna', 'Harghita', 'Mures', 'Sibiu'])) |
                (df['Judete'].str.upper() == 'TOTAL')]
        bar_chart_salariati_activitati(df, ani, an)

    elif optiune == "Salariați pe activități (grafice circulare)":
        st.header("Structura salariatilor pe activitati economice (grafice circulare pe judete)")
        st.info("Fiecare grafic circular arata structura salariatilor pe activitati economice pentru un judet.")
        df = incarca_date('Salariati2')
        ani = sorted([col for col in df.columns if col.startswith('Anul')],
                     key=lambda x: int(x.split()[-1]), reverse=True)
        an = st.selectbox("An", ani, index=0)
        df = df[(df['Judete'].isin(['Alba', 'Brasov', 'Covasna', 'Harghita', 'Mures', 'Sibiu'])) |
                (df['Judete'].str.upper() == 'TOTAL')]
        pie_charts_salariati_judete(df, ani, an)

    elif optiune == "Corelație șomaj-ocupare":
        st.header("Corelatie intre rata somajului si rata de ocupare a resurselor de munca")
        st.info("Aceasta diagrama de dispersie arata relatia dintre rata somajului si rata de ocupare a resurselor de munca. "
            "Județele din regiunea Centru sunt evidențiate cu culori distinctive, celelalte județe sunt afișate în gri.")
        df_somaj = incarca_date('Somaj')
        df_resurse = incarca_date('Resurse')
        ani = sorted([col for col in df_somaj.columns if col.startswith('Anul')],
                 key=lambda x: int(x.split()[-1]), reverse=True)
        sex = st.selectbox("Sex", df_somaj['Sexe'].unique())
    
        # Include toate județele, nu doar regiunea Centru
        df_somaj = df_somaj[(df_somaj['Sexe'] == sex)]
        df_resurse = replace_total_with_romania(df_resurse)
    
        an = st.selectbox("An", ani, index=0)
        scatter_corelatie_interactiv(
        df_somaj, df_resurse, an,
        f"Corelație rata somaj - rata de ocupare ({an.split()[-1]})",
        "Rata somaj (%)", "Rata de ocupare (%)"
    )

    elif optiune == "Structura absolvenți":
        st.header("Structura absolventilor pe niveluri de educatie (diagrama cu bare stivuite)")
        st.info("Aceasta diagrama cu bare stivuite arata structura absolventilor pe niveluri de educatie pentru judetul selectat.")
        df = filtreaza_regiunea_centru_si_romania(incarca_date('Absolventi'))
        ani = sorted([col for col in df.columns if col.startswith('Anul')],
                     key=lambda x: int(x.split()[-1]), reverse=True)
        judet = st.selectbox("Alege judetul", df['Judete'].unique())
        stacked_bar_absolventi_interactiv(df, ani, judet)

    elif optiune == "Statistici descriptive":
        analiza_statistici_descriptive()

    elif optiune == "Analiză spațială":
        analiza_spatiala_choropleth()

    elif optiune == "Sectorul public vs privat":
        analiza_spatiala_public_privat()

    elif optiune == "Analiză de regresie":
        analiza_regresie()

if __name__ == "__main__":
    main()