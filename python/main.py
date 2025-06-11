import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
import json
import folium
from streamlit_folium import st_folium

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

    fig.update_geos(
        fitbounds="locations",
        visible=False,
        bgcolor="rgba(0,0,0,0)"  # Background transparent
    )
    fig.update_layout(
        width=1200,  # Am mărit lățimea hărții
        height=800,  # Am mărit înălțimea hărții
        title=dict(font=dict(size=20)),
        coloraxis_colorbar=dict(title="Rata somaj (%)"),
        paper_bgcolor="rgba(0,0,0,0)",  # Background transparent pentru paper
        plot_bgcolor="rgba(0,0,0,0)"    # Background transparent pentru plot
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

    fig.update_geos(
        fitbounds="locations",
        visible=False,
        bgcolor="rgba(0,0,0,0)"
    )
    fig.update_layout(
        width=1200,  # Mărim lățimea hărții
        height=800,  # Mărim înălțimea hărții
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

    fig.update_geos(
        fitbounds="locations",
        visible=False,
        bgcolor="rgba(0,0,0,0)"
    )
    fig.update_layout(
        width=1200,  # Mărim lățimea hărții
        height=800,  # Mărim înălțimea hărții
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

    fig.update_geos(
        fitbounds="locations",
        visible=False,
        bgcolor="rgba(0,0,0,0)"
    )
    fig.update_layout(
        width=1200,  # Mărim lățimea hărții
        height=800,  # Mărim înălțimea hărții
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

    fig.update_geos(
        fitbounds="locations",
        visible=False,
        bgcolor="rgba(0,0,0,0)"
    )
    fig.update_layout(
        width=1200,  # Mărim lățimea hărții
        height=800,  # Mărim înălțimea hărții
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

    fig.update_geos(
        fitbounds="locations",
        visible=False,
        bgcolor="rgba(0,0,0,0)"
    )
    fig.update_layout(
        width=1200,  # Mărim lățimea hărții
        height=800,  # Mărim înălțimea hărții
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
    
    grafic_linie_pib(df_filtrat, ani, "Evolutia PIB-ului regional pe locuitor", "PIB pe locuitor (lei)", 1)

def grafic_linie_pib(df, ani, titlu, ylabel, nr_fig):
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
            name="Romania",
            text=[f"Romania<br>{an}: {row[an]:.0f} lei" for an in ani],
            hoverinfo='text+y',
            line=dict(width=5, color="#FFFFFF", dash='dot'),
            marker=dict(size=12, color="#FFFFFF", line=dict(width=2, color='black'))
        ))
    
    # Configurare aspect grafic
    fig.update_layout(
        width=1000, height=650,
        font=dict(family="Segoe UI, Arial", size=16),
        title=dict(text=f"Figura {nr_fig}. {titlu}", font=dict(size=26)),
        xaxis_title=dict(text="Anul", font=dict(size=18)),
        yaxis_title=dict(text=ylabel, font=dict(size=18)),
        yaxis=dict(tickfont=dict(size=14)),
        xaxis=dict(tickfont=dict(size=14)),
        legend_title=dict(text="Judet", font=dict(size=16)),
        legend=dict(font=dict(size=14)),
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(f"#### Tabel cu datele pentru figura {nr_fig}")
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
    
    # Afiseaza datele folosite
    st.markdown("#### Datele folosite pentru calcul")
    st.dataframe(df_centru[['Judete', an]].set_index('Judete'))

def grafic_linie_somaj(df, ani, titlu, ylabel, nr_fig):
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
            name="Romania",
            text=[f"Romania<br>{an}: {row[an]:.2f}%" for an in ani],
            hoverinfo='text+y',
            line=dict(width=5, color="#FFFFFF", dash='dot'),
            marker=dict(size=12, color="#FFFFFF", line=dict(width=2, color='black'))
        ))
    # Configurare aspect grafic
    fig.update_layout(
        width=1000, height=650,
        font=dict(family="Segoe UI, Arial", size=16),
        title=dict(text=f"Figura {nr_fig}. {titlu}", font=dict(size=26)),
        xaxis_title=dict(text="Anul", font=dict(size=18)),
        yaxis_title=dict(text=ylabel, font=dict(size=18)),
        yaxis=dict(tickfont=dict(size=14)),
        xaxis=dict(tickfont=dict(size=14)),
        legend_title=dict(text="Judet", font=dict(size=16)),
        legend=dict(font=dict(size=14)),
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(f"#### Tabel cu datele pentru figura {nr_fig}")
    st.dataframe(df.set_index('Judete')[ani])
    st.divider()

def heatmap_judete_ani_interactiv(df, ani, titlu, nr_fig):
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
        title=f"Figura {nr_fig}. {titlu}"
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
    st.markdown(f"#### Tabel cu datele pentru figura {nr_fig}")
    st.dataframe(df_hm)
    st.divider()

def stacked_bar_absolventi_interactiv(df, ani, judet_selectat, nr_fig):
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
        "#FEC5F6",  # Invatamant universitar - doctorat si postdoctorat (cel mai sus)
        "#FF9800",  # Invatamant universitar - licenta
        "#43A047",  # Invatamant postliceal
        "#8E24AA",  # Invatamant liceal (tehnologic)
        "#E53935",  # Invatamant profesional
        "#00ACC1",  # Invatamant profesional si tehnic (alte filiere)
        "#FDD835",  # Invatamant gimnazial
        "#6D4C41",  # Invatamant primar
        "#C0CA33",  # Alte categorii (daca apar)
        "#F06292",  # Alte categorii (daca apar)
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
        title=dict(text=f"Figura {nr_fig}. Structura absolventilor pe niveluri de educatie ({judet_selectat})", font=dict(size=28)),
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

    st.markdown(f"#### Tabel cu datele pentru figura {nr_fig}")
    st.dataframe(df_judet.set_index('Niveluri de educatie')[ani])
    st.divider()

def bar_chart_an_interactiv(df, an, titlu, ylabel, nr_fig):
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
        title=dict(text=f"Figura {nr_fig}. {titlu}", font=dict(size=26)),
        legend=dict(font=dict(size=14))
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(f"#### Tabel cu datele pentru figura {nr_fig}")
    st.dataframe(df.set_index('Judete')[[an]])
    st.divider()

def scatter_corelatie_interactiv(df_x, df_y, an, titlu, xlabel, ylabel, nr_fig):
    # Creaza scatter plot pentru corelatia intre rata somaj si rata de ocupare
    st.divider()
    an_num = an.split()[-1]
    df_x = replace_total_with_romania(df_x)
    df_y = replace_total_with_romania(df_y)
    df_x = converteste_ani_la_float(df_x, [an])
    df_y = converteste_ani_la_float(df_y, [an])
    judete_ord = ["Alba", "Brasov", "Covasna", "Harghita", "Mures", "Sibiu", "Romania"]
    colors = [JUD_COLORS.get(j, "#888888") for j in judete_ord]
    df_corel = pd.DataFrame({
        'Judet': df_x['Judete'],
        'Rata somaj': df_x[an],
        'Rata ocupare': df_y[an]
    })
    fig = go.Figure()
    for idx, jud in enumerate(judete_ord):
        row = df_corel[df_corel['Judet'] == jud]
        if not row.empty:
            color = colors[idx]
            fig.add_trace(go.Scatter(
                x=row['Rata somaj'],
                y=row['Rata ocupare'],
                mode='markers+text',
                name=jud,
                text=[jud],
                marker=dict(size=18, color=color, line=dict(width=1.5, color="#222")),
                textfont=dict(size=14, color=color if jud != "Romania" else "#222"),
                textposition='top center'
            ))
    fig.update_layout(
        width=1000, height=650,
        font=dict(family="Segoe UI, Arial", size=16),
        xaxis=dict(title=dict(text=xlabel, font=dict(size=18)), tickfont=dict(size=14)),
        yaxis=dict(title=dict(text=ylabel, font=dict(size=18)), tickfont=dict(size=14)),
        title=dict(text=f"Figura {nr_fig}. {titlu}", font=dict(size=26)),
        legend=dict(font=dict(size=14))
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(f"#### Tabel cu datele pentru figura {nr_fig}")
    st.dataframe(df_corel.set_index('Judet'))
    st.divider()

def bar_chart_salariati_activitati(df, ani, an_selectat, nr_fig):
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
        title=dict(text=f"Figura {nr_fig}. Numar salariati in {an_num} pentru activitatea: {activitate}", font=dict(size=26)),
        legend=dict(font=dict(size=14))
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(f"#### Tabel cu datele pentru figura {nr_fig}")
    if not show_romania:
        st.dataframe(df_activ[df_activ['Judete'] != "Romania"].set_index('Judete')[[an_selectat]])
    else:
        st.dataframe(df_activ.set_index('Judete')[[an_selectat]])
    st.divider()

def pie_charts_salariati_judete(df, ani, an_selectat, nr_fig):
    # Creaza pie chart-uri pentru structura salariatilor pe activitati economice in fiecare judet
    st.divider()
    an_num = an_selectat.split()[-1]
    df = replace_total_with_romania(df)
    df = converteste_ani_la_float(df, [an_selectat])
    judete = ["Alba", "Brasov", "Covasna", "Harghita", "Mures", "Sibiu"]
    st.subheader(f"Figura {nr_fig}. Structura salariatilor pe activitati economice in anul {an_num}")

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
            st.markdown(f"#### Tabel cu datele pentru {judet} ({nr_fig}) - Categorii grupate")
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
                st.markdown(f"#### Tabel cu datele pentru {judet} ({nr_fig}) - Alte industrii detaliat")
                st.dataframe(df_other.set_index('Activitate')[[an_selectat]])
                st.divider()

    st.markdown("### Legenda activitati economice")
    # Afiseaza legenda pentru prescurtari activitati
    st.markdown(
        "\n".join([f"- **{prescurtare}**: {activitate}" for activitate, prescurtare in PRESCURTARI_ACTIVITATI.items()])
    )
    st.divider()

def analiza_regresie_multipla():
    # Sectiune care realizeaza regresia multipla: rata somaj ~ absolventi + populatie activa
    st.header("Regresie multipla: rata somajului ~ absolventi + populatie activa")
    st.info(
        "Aceasta analiza construieste un model de regresie multipla pentru rata somajului, "
        "folosind ca variabile independente numarul total de absolventi si populatia activa, "
        "pentru fiecare judet din regiunea Centru si pentru Romania."
    )

    # Incarca datele din tabelele relevante
    df_somaj = incarca_date('Somaj')
    df_absolventi = incarca_date('Absolventi')
    df_popactiva = incarca_date('PopActiva')

    # Inlocuieste valorile TOTAL cu Romania pentru consistenta
    df_somaj = replace_total_with_romania(df_somaj)
    df_absolventi = replace_total_with_romania(df_absolventi)
    df_popactiva = replace_total_with_romania(df_popactiva)

    # Selecteaza anii disponibili in toate tabelele
    ani_somaj = [col for col in df_somaj.columns if col.startswith('Anul')]
    ani_absolventi = [col for col in df_absolventi.columns if col.startswith('Anul')]
    ani_popactiva = [col for col in df_popactiva.columns if col.startswith('Anul')]
    ani_comuni = sorted(
        list(set(ani_somaj) & set(ani_absolventi) & set(ani_popactiva)),
        key=lambda x: int(x.split()[-1]),
        reverse=True
    )

    # Selecteaza sexul si anul pentru analiza
    sex = st.selectbox("Alege sexul", df_somaj['Sexe'].unique())
    an = st.selectbox("Alege anul", ani_comuni, index=0)

    # Filtreaza doar judetele din regiunea Centru si Romania
    judete_centru_romania = ['Alba', 'Brasov', 'Covasna', 'Harghita', 'Mures', 'Sibiu', 'Romania']

    # Prelucreaza datele pentru somaj
    df_somaj = df_somaj[(df_somaj['Sexe'] == sex) & (df_somaj['Judete'].isin(judete_centru_romania))]
    df_somaj = converteste_ani_la_float(df_somaj, [an])
    df_somaj = df_somaj[['Judete', an]].rename(columns={an: 'Rata_somaj'}).reset_index(drop=True)

    # Prelucreaza datele pentru absolventi
    df_absolventi = df_absolventi[df_absolventi['Judete'].isin(judete_centru_romania)]
    df_absolventi = converteste_ani_la_float(df_absolventi, [an])
    df_absolventi_total = df_absolventi.groupby('Judete')[an].sum().reset_index().rename(columns={an: 'Absolventi_totali'})

    # Prelucreaza datele pentru populatie activa
    df_popactiva = df_popactiva[(df_popactiva['Sexe'] == sex) & (df_popactiva['Judete'].isin(judete_centru_romania))]
    df_popactiva = converteste_ani_la_float(df_popactiva, [an])
    df_popactiva[an] = df_popactiva[an] * 1000  # conversie mii persoane -> persoane
    df_popactiva = df_popactiva[['Judete', an]].rename(columns={an: 'Populatie_activa'})

    # Uneste datele intr-un singur DataFrame pentru regresie
    df_regresie = df_somaj.merge(df_absolventi_total, on='Judete').merge(df_popactiva, on='Judete')

    st.markdown("#### Tabel cu datele folosite la regresie")
    st.dataframe(df_regresie)

    # Pregateste variabilele pentru modelul de regresie
    X = df_regresie[['Absolventi_totali', 'Populatie_activa']]
    y = df_regresie['Rata_somaj']

    # Standardizeaza variabilele independente
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Adauga constanta pentru intercept
    X_scaled_const = sm.add_constant(X_scaled)

    # Calculeaza modelul de regresie OLS
    model = sm.OLS(y, X_scaled_const).fit()

    st.markdown("#### Rezultatele modelului de regresie multipla")
    # Afiseaza iesirea modelului folosind font monospace pentru aliniere corecta
    st.code(model.summary().as_text(), language="")

    # Afiseaza formula matematica a modelului
    st.latex(r'''
Rata\_somaj = \beta_0 + \beta_1 \cdot Absolventi\_totali^{(standardizat)} + \beta_2 \cdot Populatie\_activa^{(standardizat)} + \varepsilon
''')

    # Panou informativ cu explicatii despre termeni
    st.markdown(
        """
        <div style="background-color:#223b54;padding:18px;border-radius:8px;color:white;">
        <b>Explicatii pentru termeni:</b>
        <ul>
        <li><b>Rata_somaj</b> – variabila dependenta</li>
        <li><b>Absolventi_totali</b> – numarul total de absolventi</li>
        <li><b>Populatie_activa</b> – populatia activa</li>
        <li><b>β₀</b> – interceptul modelului</li>
        <li><b>β₁, β₂</b> – coeficientii de regresie (masoara influenta variabilelor independente 
              asupra ratei somajului)</li>
        <li><b>ε</b> – eroarea/residuu (diferenta dintre valoarea observata si cea prezisa de model)</li>
        </ul>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Verificare ipoteze regresie
    st.markdown("#### Verificarea ipotezelor regresiei liniare multiple")

    # 1. Normalitatea reziduurilor prin Q-Q plot
    st.markdown("**Normalitatea reziduurilor (Q-Q plot):**")
    fig_qq = plt.figure()
    sm.qqplot(model.resid, line='s', ax=plt.gca())
    plt.title('Q-Q Plot al reziduurilor')
    st.pyplot(fig_qq)

    # 2. Homoscedasticitatea reziduurilor prin scatter plot reziduuri vs valori prezise
    st.markdown("**Homoscedasticitatea reziduurilor:**")
    fig_resid = plt.figure()
    plt.scatter(model.fittedvalues, model.resid, color='blue')
    plt.axhline(y=0, color='red', linestyle='--')
    plt.xlabel('Valori prezise')
    plt.ylabel('Reziduuri')
    plt.title('Reziduuri vs Valori prezise')
    st.pyplot(fig_resid)

    # 3. Multicoliniaritatea variabilelor independente prin calcul VIF
    st.markdown("**Multicoliniaritatea variabilelor independente (VIF):**")
    vif_data = pd.DataFrame()
    vif_data['Variabila'] = ['Absolventi_totali', 'Populatie_activa']
    vif_data['VIF'] = [variance_inflation_factor(X_scaled, i) for i in range(X_scaled.shape[1])]
    st.dataframe(vif_data)

    # 4. Semnificativitatea modelului (R^2, p-value)
    st.markdown("**Semnificativitatea modelului:**")
    st.write(f"R^2: {model.rsquared:.3f}")
    st.write(f"p-value model: {model.f_pvalue:.4f}")
    st.write("Coeficienti si semnificatie (p-value):")
    coef_df = pd.DataFrame({
        'Coeficient': model.params,
        'p-value': model.pvalues
    })
    coef_df.index = ['Intercept', 'Absolventi_totali (standardizat)', 'Populatie_activa (standardizat)']
    st.dataframe(coef_df)

    # Explicatii suplimentare pentru profesori (fundal albastru)
    st.markdown(
        """
        <div style="background-color:#223b54;padding:18px;border-radius:8px;color:white;">
        <b>Explicatii privind verificarea ipotezelor:</b><br>
        <ul>
        <li><b>Normalitatea reziduurilor</b> se verifica cu Q-Q plot. Daca punctele se aliniez pe linia diagonala, 
            reziduurile pot fi considerate normale.</li>
        <li><b>Homoscedasticitatea reziduurilor</b> se verifica prin scatter plot reziduuri vs valori prezise. 
            Daca reziduurile sunt distribuite aleator in jurul axei 0, ipoteza este indeplinita.</li>
        </ul>
        </div>
        """,
        unsafe_allow_html=True
    )

def main():
    # Titlul aplicatiei Streamlit
    st.title("Analiza a pietei muncii - Regiunea Centru")
    st.divider()
    st.sidebar.title("Meniu analize")
    # Meniul de optiuni din sidebar 
    st.sidebar.markdown("## Meniu analize")
    st.sidebar.markdown("---")
    optiune = st.sidebar.radio(
        "📊 Alege analiza:",
        (
            "Evolutie rata somaj (grafic cu linii)",
            "Evolutie PIB (grafic cu linii)",
            "Comparatie rata somaj (harta termica)",
            "Judete dupa rata somaj (grafic cu bare)",
            "Salariati pe activitati economice (grafic cu bare)",
            "Salariati pe activitati economice (grafice circulare)",
            "Corelatie rata somaj - ocupare (diagrama de dispersie)",
            "Structura absolventi pe niveluri (diagrama cu bare stivuite)",
            "Statistici descriptive",
            "Analiza spatiala",
            "Regresie multipla"
        ),
        index=1  # Pozitie implicita
    )

    nr_fig = 1  # Numarul figurii - incrementat pentru fiecare analiza

    if optiune == "Evolutie rata somaj (grafic cu linii)":
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
        grafic_linie_somaj(df_filtrat, ani, "Evolutia ratei somajului", "Rata somaj (%)", nr_fig)

    elif optiune == "Evolutie PIB (grafic cu linii)":
        analiza_pib_evolutie()

    elif optiune == "Comparatie rata somaj (harta termica)":
        nr_fig += 1
        st.header("Comparatie rata somajului pe judete si ani (harta termica)")
        st.info("Harta termica permite compararea rapida a ratei somajului intre judete si ani.")
        df = incarca_date('Somaj')
        ani = sorted([col for col in df.columns if col.startswith('Anul')],
                     key=lambda x: int(x.split()[-1]), reverse=True)
        sex = st.selectbox("Sex", df['Sexe'].unique())
        df = df[(df['Sexe'] == sex) & ((df['Judete'].isin(['Alba', 'Brasov', 'Covasna',
                                                           'Harghita', 'Mures', 'Sibiu'])) |
                                        (df['Judete'].str.upper() == 'TOTAL'))]
        heatmap_judete_ani_interactiv(df, ani, "Harta termica rata somajului pe judete si ani", nr_fig)

    elif optiune == "Judete dupa rata somaj (grafic cu bare)":
        nr_fig += 2
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
        bar_chart_an_interactiv(df, an, f"Rata somajului pe judete in {an.split()[-1]}", "Rata somaj (%)", nr_fig)

    elif optiune == "Salariati pe activitati economice (grafic cu bare)":
        nr_fig += 3
        st.header("Numar salariati pe activitati economice si judete (grafic cu bare)")
        st.info("Acest grafic arata distributia salariatilor pe activitati economice pentru fiecare judet.")
        df = incarca_date('Salariati2')
        ani = sorted([col for col in df.columns if col.startswith('Anul')],
                     key=lambda x: int(x.split()[-1]), reverse=True)
        an = st.selectbox("An", ani, index=0)
        df = df[(df['Judete'].isin(['Alba', 'Brasov', 'Covasna', 'Harghita', 'Mures', 'Sibiu'])) |
                (df['Judete'].str.upper() == 'TOTAL')]
        bar_chart_salariati_activitati(df, ani, an, nr_fig)

    elif optiune == "Salariati pe activitati economice (grafice circulare)":
        nr_fig += 4
        st.header("Structura salariatilor pe activitati economice (grafice circulare pe judete)")
        st.info("Fiecare grafic circular arata structura salariatilor pe activitati economice pentru un judet.")
        df = incarca_date('Salariati2')
        ani = sorted([col for col in df.columns if col.startswith('Anul')],
                     key=lambda x: int(x.split()[-1]), reverse=True)
        an = st.selectbox("An", ani, index=0)
        df = df[(df['Judete'].isin(['Alba', 'Brasov', 'Covasna', 'Harghita', 'Mures', 'Sibiu'])) |
                (df['Judete'].str.upper() == 'TOTAL')]
        pie_charts_salariati_judete(df, ani, an, nr_fig)

    elif optiune == "Corelatie rata somaj - ocupare (diagrama de dispersie)":
        nr_fig += 5
        st.header("Corelatie intre rata somajului si rata de ocupare a resurselor de munca (diagrama de dispersie)")
        st.info("Aceasta diagrama de dispersie arata relatia dintre rata somajului si rata de ocupare a resurselor de munca.")
        df_somaj = incarca_date('Somaj')
        df_resurse = incarca_date('Resurse')
        ani = sorted([col for col in df_somaj.columns if col.startswith('Anul')],
                     key=lambda x: int(x.split()[-1]), reverse=True)
        sex = st.selectbox("Sex", df_somaj['Sexe'].unique())
        df_somaj = df_somaj[(df_somaj['Sexe'] == sex) & ((df_somaj['Judete'].isin(['Alba', 'Brasov', 'Covasna',
                                                                                     'Harghita', 'Mures', 'Sibiu'])) |
                                                           (df_somaj['Judete'].str.upper() == 'TOTAL'))]
        df_resurse = df_resurse[(df_resurse['Judete'].isin(['Alba', 'Brasov', 'Covasna', 'Harghita', 'Mures', 'Sibiu'])) |
                                (df_resurse['Judete'].str.upper() == 'TOTAL')]
        an = st.selectbox("An", ani, index=0)
        scatter_corelatie_interactiv(
            df_somaj, df_resurse, an,
            f"Corelatie rata somaj - rata de ocupare ({an.split()[-1]})",
            "Rata somaj (%)", "Rata de ocupare (%)", nr_fig
        )

    elif optiune == "Structura absolventi pe niveluri (diagrama cu bare stivuite)":
        nr_fig += 6
        st.header("Structura absolventilor pe niveluri de educatie (diagrama cu bare stivuite)")
        st.info("Aceasta diagrama cu bare stivuite arata structura absolventilor pe niveluri de educatie pentru judetul selectat.")
        df = filtreaza_regiunea_centru_si_romania(incarca_date('Absolventi'))
        ani = sorted([col for col in df.columns if col.startswith('Anul')],
                     key=lambda x: int(x.split()[-1]), reverse=True)
        judet = st.selectbox("Alege judetul", df['Judete'].unique())
        stacked_bar_absolventi_interactiv(df, ani, judet, nr_fig)

    elif optiune == "Statistici descriptive":
        analiza_statistici_descriptive()

    elif optiune == "Analiza spatiala":
        analiza_spatiala_choropleth()

    elif optiune == "Regresie multipla":
        analiza_regresie_multipla()

if __name__ == "__main__":
    main()