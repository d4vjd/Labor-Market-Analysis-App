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

@st.cache_data
def incarca_date(nume_tabel):
    conexiune = sqlite3.connect('data.sqlite')
    df = pd.read_sql_query(f"SELECT * FROM {nume_tabel}", conexiune)
    conexiune.close()
    return df

def filtreaza_regiunea_centru_si_romania(df):
    judete_centru = ['Alba', 'Brasov', 'Covasna', 'Harghita', 'Mures', 'Sibiu', 'Romania']
    return df[df['Judete'].isin(judete_centru)]

def extrage_ani(lista_ani):
    return [col.split()[-1] for col in lista_ani]

def converteste_ani_la_float(df, ani):
    for an in ani:
        df[an] = pd.to_numeric(df[an], errors='coerce')
    return df

JUD_COLORS = {
    "Alba": "#1976D2",
    "Brasov": "#FF9800",
    "Covasna": "#388E3C",
    "Harghita": "#7B1FA2",
    "Mures": "#D32F2F",
    "Sibiu": "#00B8D4",
    "Romania": "#FFFFFF"
}
PALETA = [JUD_COLORS[j] for j in ["Alba", "Brasov", "Covasna", "Harghita", "Mures", "Sibiu"]]

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

def prescurteaza_activitate(activitate):
    activitate_norm = activitate.strip().upper()
    for cheie in PRESCURTARI_ACTIVITATI:
        if activitate_norm.startswith(cheie):
            return PRESCURTARI_ACTIVITATI[cheie]
    return activitate[:30] + "..."

def replace_total_with_romania(df):
    df = df.copy()
    df['Judete'] = df['Judete'].replace({'TOTAL': 'Romania', 'Total': 'Romania', 'MEDIA ROMÂNIA': 'Romania', 'Media România': 'Romania'})
    return df

def grafic_linie_somaj(df, ani, titlu, ylabel, nr_fig):
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
    df_total = df[df['Judete'] == 'Romania']
    if not df_total.empty:
        row = df_total.iloc[0]
        fig.add_trace(go.Scatter(
            x=ani_num,
            y=[row[an] for an in ani],
            mode='lines+markers',
            name="România",
            text=[f"România<br>{an}: {row[an]:.2f}%" for an in ani],
            hoverinfo='text+y',
            line=dict(width=5, color="#FFFFFF", dash='dot'),
            marker=dict(size=12, color="#FFFFFF", line=dict(width=2, color='black'))
        ))
    fig.update_layout(
        width=1000, height=650,
        font=dict(family="Segoe UI, Arial", size=16),
        title=dict(text=f"Figura {nr_fig}. {titlu}", font=dict(size=26)),
        xaxis_title=dict(text="Anul", font=dict(size=18)),
        yaxis_title=dict(text=ylabel, font=dict(size=18)),
        yaxis=dict(tickfont=dict(size=14)),
        xaxis=dict(tickfont=dict(size=14)),
        legend_title=dict(text="Județ", font=dict(size=16)),
        legend=dict(font=dict(size=14)),
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(f"#### Tabel cu datele pentru figura {nr_fig}")
    st.dataframe(df.set_index('Judete')[ani])
    st.divider()

def heatmap_judete_ani_interactiv(df, ani, titlu, nr_fig):
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
        labels=dict(color="Rată șomaj (%)"),
        title=f"Figura {nr_fig}. {titlu}"
    )
    fig.update_xaxes(side="bottom", tickangle=45, title=dict(text="Anul", font=dict(size=18)), tickfont=dict(size=12), dtick=1)
    fig.update_yaxes(autorange="reversed", title=dict(text="Județ", font=dict(size=18)), tickfont=dict(size=12))
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
    st.divider()
    ani_num = extrage_ani(ani)
    df = replace_total_with_romania(df)
    df = converteste_ani_la_float(df, ani)
    df_judet = df[df['Judete'] == judet_selectat]

    # Obține ordinea nivelurilor de educație așa cum apar în tabel
    niveluri = df_judet['Niveluri de educatie'].tolist()

    # Construiește DataFrame-ul pentru stacked bar, reindexat după ordinea din tabel și fill NaN cu 0
    df_temp = df_judet.set_index('Niveluri de educatie')[ani]
    df_temp = df_temp.reindex(niveluri)
    df_temp = df_temp.fillna(0)
    df_stacked = df_temp.T.reset_index().rename(columns={'index': 'An'})
    df_stacked['An'] = ani_num

    # Paleta distinctă pentru niveluri de educație (maxim 10 categorii, poate extinde)
    PALETA_EDUCATIE = [
        "#1976D2",  # albastru
        "#FF9800",  # portocaliu
        "#43A047",  # verde
        "#8E24AA",  # mov
        "#E53935",  # roșu
        "#00ACC1",  # turcoaz
        "#FDD835",  # galben
        "#F06292",  # roz
    ]

    fig = go.Figure()
    legend_labels = []
    # Iterează în ordinea nivelurilor din tabel: primul element din listă va fi bottom-ul grafice
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
        title=dict(text=f"Figura {nr_fig}. Structura absolvenților pe niveluri de educație ({judet_selectat})", font=dict(size=28)),
        xaxis=dict(title=dict(text="Anul", font=dict(size=16)), tickangle=0, tickfont=dict(size=12)),
        yaxis=dict(title=dict(text="Număr absolvenți", font=dict(size=16)), tickfont=dict(size=12)),
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

    # Afișează legenda cu ordine și culori
    st.markdown("#### Legendă nivel educație")
    legend_html = "<div style='display:flex; flex-wrap:wrap; gap:20px;'>"
    for color, label in legend_labels:
        legend_html += f"<div style='display:flex; align-items:center; margin-bottom:6px;'><div style='width:18px; height:18px; background:{color}; border:2px solid #222; margin-right:8px;'></div><span style='font-size:15px'>{label}</span></div>"
    legend_html += "</div>"
    st.markdown(legend_html, unsafe_allow_html=True)

    st.markdown(f"#### Tabel cu datele pentru figura {nr_fig}")
    st.dataframe(df_judet.set_index('Niveluri de educatie')[ani])
    st.divider()

def bar_chart_an_interactiv(df, an, titlu, ylabel, nr_fig):
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
    # România
    row = df[df['Judete'] == 'Romania']
    if not row.empty:
        val = row.iloc[0][an]
        fig.add_trace(go.Bar(
            x=["România"],
            y=[val],
            name="România",
            text=[val],
            marker_color="#FFFFFF",
            marker_line=dict(width=2, color="#222"),
            textfont=dict(size=14, color="black")
        ))
    fig.update_layout(
        width=1000, height=650,
        font=dict(family="Segoe UI, Arial", size=16),
        yaxis=dict(title=dict(text=ylabel, font=dict(size=18)), tickfont=dict(size=14)),
        xaxis=dict(title=dict(text="Județ", font=dict(size=18)), tickangle=30, tickfont=dict(size=14)),
        title=dict(text=f"Figura {nr_fig}. {titlu}", font=dict(size=26)),
        legend=dict(font=dict(size=14))
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(f"#### Tabel cu datele pentru figura {nr_fig}")
    st.dataframe(df.set_index('Judete')[[an]])
    st.divider()

def scatter_corelatie_interactiv(df_x, df_y, an, titlu, xlabel, ylabel, nr_fig):
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
    st.divider()
    an_num = an_selectat.split()[-1]
    df = replace_total_with_romania(df)
    df = converteste_ani_la_float(df, [an_selectat])
    judete_ord = ["Alba", "Brasov", "Covasna", "Harghita", "Mures", "Sibiu", "Romania"]
    colors = [JUD_COLORS.get(j, "#888888") for j in judete_ord]
    activitati = df['Activitati ale economiei'].unique()
    activitati_prescurtate = [prescurteaza_activitate(a) for a in activitati]
    activitate = st.selectbox("Alege activitatea economică", activitati_prescurtate)
    activitate_originala = [a for a in activitati if prescurteaza_activitate(a) == activitate][0]
    df_activ = df[df['Activitati ale economiei'] == activitate_originala]
    show_romania = st.checkbox("Afișează și România", value=False)
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
        yaxis=dict(title=dict(text="Număr salariați", font=dict(size=18)), tickfont=dict(size=14)),
        xaxis=dict(title=dict(text="Județ", font=dict(size=18)), tickangle=30, tickfont=dict(size=14)),
        title=dict(text=f"Figura {nr_fig}. Număr salariați în {an_num} pentru activitatea: {activitate}", font=dict(size=26)),
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
    st.divider()
    an_num = an_selectat.split()[-1]
    df = replace_total_with_romania(df)
    df = converteste_ani_la_float(df, [an_selectat])
    judete = ["Alba", "Brasov", "Covasna", "Harghita", "Mures", "Sibiu"]
    st.subheader(f"Figura {nr_fig}. Structura salariaților pe activități economice în anul {an_num}")

    # Buton pentru afișarea detaliilor ale altor industrii (categorii sub 5%)
    show_detail_alte = st.checkbox("Afișează detaliu pentru Alte Industrii (categorii < 5%)", value=False)

    # Creează coloana cu activitatea prescurtată
    df['Activitate'] = df['Activitati ale economiei'].apply(prescurteaza_activitate)

    for judet in judete:
        df_judet = df[df['Judete'] == judet]
        total_judet = df_judet[an_selectat].sum()
        # Identifică categorii mici sub 5%
        df_other = df_judet[df_judet[an_selectat] < total_judet * 0.05]
        # Categorii principale (>=5%)
        df_main = df_judet[df_judet[an_selectat] >= total_judet * 0.05].copy()
        valoare_other = df_other[an_selectat].sum()
        # Adaugă categoria "Alte industrii" în df_main
        if valoare_other > 0:
            df_main = pd.concat([
                df_main,
                pd.DataFrame([{'Activitate': 'Alte industrii', an_selectat: valoare_other}])
            ], ignore_index=True)

        if not show_detail_alte:
            # Afișează grafic principal cu "Alte industrii" grupate
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
            # Afișează grafic detaliat pentru categoriile sub 5%
            if df_other.empty:
                st.write(f"Pentru județul {judet}, nu există categorii sub 5%.")
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

    st.markdown("### Legenda activități economice")
    st.markdown(
        "\n".join([f"- **{prescurtare}**: {activitate}" for activitate, prescurtare in PRESCURTARI_ACTIVITATI.items()])
    )
    st.divider()

def analiza_regresie_multipla():
    st.header("Regresie multiplă: rata șomajului ~ absolvenți + populație activă")
    st.info(
        "Această analiză construiește un model de regresie multiplă pentru rata șomajului, "
        "folosind ca variabile independente numărul total de absolvenți și populația activă, "
        "pentru fiecare județ din regiunea Centru și pentru România."
    )

    # Încarcă datele relevante
    df_somaj = incarca_date('Somaj')
    df_absolventi = incarca_date('Absolventi')
    df_popactiva = incarca_date('PopActiva')

    # Înlocuiește TOTAL cu Romania
    df_somaj = replace_total_with_romania(df_somaj)
    df_absolventi = replace_total_with_romania(df_absolventi)
    df_popactiva = replace_total_with_romania(df_popactiva)

    # Selectează anii comuni
    ani_somaj = [col for col in df_somaj.columns if col.startswith('Anul')]
    ani_absolventi = [col for col in df_absolventi.columns if col.startswith('Anul')]
    ani_popactiva = [col for col in df_popactiva.columns if col.startswith('Anul')]
    ani_comuni = sorted(list(set(ani_somaj) & set(ani_absolventi) & set(ani_popactiva)), key=lambda x: int(x.split()[-1]), reverse=True)

    # Selectează sexul și anul
    sex = st.selectbox("Alege sexul", df_somaj['Sexe'].unique())
    an = st.selectbox("Alege anul", ani_comuni, index=0)

    # Filtrează doar județele din regiunea Centru și România
    judete_centru_romania = ['Alba', 'Brasov', 'Covasna', 'Harghita', 'Mures', 'Sibiu', 'Romania']

    # Prelucrează datele pentru fiecare sursă
    df_somaj = df_somaj[(df_somaj['Sexe'] == sex) & (df_somaj['Judete'].isin(judete_centru_romania))]
    df_somaj = converteste_ani_la_float(df_somaj, [an])
    df_somaj = df_somaj[['Judete', an]].rename(columns={an: 'Rata_somaj'}).reset_index(drop=True)

    df_absolventi = df_absolventi[df_absolventi['Judete'].isin(judete_centru_romania)]
    df_absolventi = converteste_ani_la_float(df_absolventi, [an])
    # Suma pe toate nivelurile de educație pentru fiecare județ
    df_absolventi_total = df_absolventi.groupby('Judete')[an].sum().reset_index().rename(columns={an: 'Absolventi_totali'})

    df_popactiva = df_popactiva[(df_popactiva['Sexe'] == sex) & (df_popactiva['Judete'].isin(judete_centru_romania))]
    df_popactiva = converteste_ani_la_float(df_popactiva, [an])
    df_popactiva[an] = df_popactiva[an] * 1000  # conversie din mii persoane în persoane
    df_popactiva = df_popactiva[['Judete', an]].rename(columns={an: 'Populatie_activa'})

    # Unește datele într-un singur DataFrame
    df_regresie = df_somaj.merge(df_absolventi_total, on='Judete').merge(df_popactiva, on='Judete')

    st.markdown("#### Tabel cu datele folosite la regresie")
    st.dataframe(df_regresie)

    # Pregătește datele pentru regresie
    X = df_regresie[['Absolventi_totali', 'Populatie_activa']]
    y = df_regresie['Rata_somaj']

    # Standardizează variabilele independente
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Adaugă constantă pentru intercept
    X_scaled_const = sm.add_constant(X_scaled)

    # Modelul de regresie
    model = sm.OLS(y, X_scaled_const).fit()

    st.markdown("#### Rezultatele modelului de regresie multiplă")
    st.text(model.summary())

    # Formula matematică centrată, în afara panoului informativ
    st.latex(r'''
Rata\_somaj = \beta_0 + \beta_1 \cdot Absolventi\_totali^{(standardizat)} + \beta_2 \cdot Populatie\_activa^{(standardizat)} + \varepsilon
''')

    # Panou informativ cu explicații
    st.markdown(
        """
        <div style="background-color:#223b54;padding:18px;border-radius:8px;color:white;">
        <b>Explicații pentru termeni:</b>
        <ul>
        <li><b>Rata_somaj</b> – variabila dependentă</li>
        <li><b>Absolventi_totali</b> – numărul total de absolvenți</li>
        <li><b>Populatie_activa</b> – populația activă</li>
        <li><b>β₀</b> – interceptul modelului</li>
        <li><b>β₁, β₂</b> – coeficienții de regresie (măsoară influența fiecărei variabile independente asupra ratei șomajului)</li>
        <li><b>ε</b> – eroarea/residuu (diferența dintre valoarea observată și cea prezisă de model)</li>
        </ul>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Verificare ipoteze regresie
    st.markdown("#### Verificarea ipotezelor regresiei liniare multiple")

    # 1. Normalitatea reziduurilor (Q-Q plot)
    st.markdown("**Normalitatea reziduurilor (Q-Q plot):**")
    fig_qq = plt.figure()
    sm.qqplot(model.resid, line='s', ax=plt.gca())
    plt.title('Q-Q Plot al reziduurilor')
    st.pyplot(fig_qq)

    # 2. Homoscedasticitate (plot reziduuri vs valori prezise)
    st.markdown("**Homoscedasticitatea reziduurilor:**")
    fig_resid = plt.figure()
    plt.scatter(model.fittedvalues, model.resid, color='blue')
    plt.axhline(y=0, color='red', linestyle='--')
    plt.xlabel('Valori prezise')
    plt.ylabel('Reziduuri')
    plt.title('Reziduuri vs Valori prezise')
    st.pyplot(fig_resid)

    # 3. Multicoliniaritate (VIF)
    st.markdown("**Multicoliniaritatea variabilelor independente (VIF):**")
    vif_data = pd.DataFrame()
    vif_data['Variabila'] = ['Absolventi_totali', 'Populatie_activa']
    vif_data['VIF'] = [variance_inflation_factor(X_scaled, i) for i in range(X_scaled.shape[1])]
    st.dataframe(vif_data)

    # 4. Semnificativitatea modelului (p-value, R^2)
    st.markdown("**Semnificativitatea modelului:**")
    st.write(f"R^2: {model.rsquared:.3f}")
    st.write(f"p-value model: {model.f_pvalue:.4f}")
    st.write("Coeficienți și semnificație (p-value):")
    coef_df = pd.DataFrame({
        'Coeficient': model.params,
        'p-value': model.pvalues
    })
    coef_df.index = ['Intercept', 'Absolventi_totali (standardizat)', 'Populatie_activa (standardizat)']
    st.dataframe(coef_df)

    # Explicații pentru profesori (fundal albastru)
    st.markdown(
        """
        <div style="background-color:#223b54;padding:18px;border-radius:8px;color:white;">
        <b>Explicații privind verificarea ipotezelor:</b><br>
        <ul>
        <li><b>Normalitatea reziduurilor</b> este verificată folosind Q-Q plot (Quantile-Quantile plot). Acest grafic compară distribuția reziduurilor modelului cu o distribuție normală teoretică. Dacă punctele se aliniază pe linia diagonală, reziduurile pot fi considerate normale.</li>
        <li><b>Homoscedasticitatea reziduurilor</b> este verificată printr-un grafic scatter între valorile prezise de model și reziduuri. Dacă reziduurile sunt distribuite aleator în jurul axei 0, fără un pattern clar, atunci ipoteza de homoscedasticitate este îndeplinită.</li>
        </ul>
        </div>
        """,
        unsafe_allow_html=True
    )

def main():
    st.title("Analiză a pieței muncii - Regiunea Centru")
    st.divider()
    st.sidebar.title("Meniu analize")
    optiune = st.sidebar.radio(
        "Alege analiza:",
        (
            "Evoluție rată șomaj (linie)",
            "Comparație rată șomaj (heatmap)",
            "Top județe după rată șomaj (bar chart)",
            "Salariați pe activități economice (bar chart)",
            "Structura salariaților pe activități (pie chart pe județe)",
            "Corelație rată șomaj - ocupare (scatter)",
            "Structura absolvenți pe niveluri (stacked bar)",
            "Regresie multiplă"
        )
    )

    nr_fig = 1

    if optiune == "Evoluție rată șomaj (linie)":
        st.header("Evoluția ratei șomajului în regiunea Centru (linie)")
        st.info("Acest grafic arată evoluția ratei șomajului în timp pentru fiecare județ din regiunea Centru. Linia albă punctată reprezintă media națională.")
        df = incarca_date('Somaj')
        ani = sorted([col for col in df.columns if col.startswith('Anul')], key=lambda x: int(x.split()[-1]), reverse=True)
        sex = st.selectbox("Sex", df['Sexe'].unique())
        df_filtrat = df[(df['Sexe'] == sex) & ((df['Judete'].isin(['Alba', 'Brasov', 'Covasna', 'Harghita', 'Mures', 'Sibiu'])) | (df['Judete'].str.upper() == 'TOTAL'))]
        grafic_linie_somaj(df_filtrat, ani, "Evoluția ratei șomajului", "Rată șomaj (%)", nr_fig)

    elif optiune == "Comparație rată șomaj (heatmap)":
        nr_fig += 1
        st.header("Comparație rata șomajului pe județe și ani (heatmap)")
        st.info("Heatmap-ul permite compararea rapidă a ratei șomajului între județe și ani.")
        df = incarca_date('Somaj')
        ani = sorted([col for col in df.columns if col.startswith('Anul')], key=lambda x: int(x.split()[-1]), reverse=True)
        sex = st.selectbox("Sex", df['Sexe'].unique())
        df = df[(df['Sexe'] == sex) & ((df['Judete'].isin(['Alba', 'Brasov', 'Covasna', 'Harghita', 'Mures', 'Sibiu'])) | (df['Judete'].str.upper() == 'TOTAL'))]
        heatmap_judete_ani_interactiv(df, ani, "Heatmap rata șomajului pe județe și ani", nr_fig)

    elif optiune == "Top județe după rată șomaj (bar chart)":
        nr_fig += 2
        st.header("Top județe după rata șomajului (bar chart)")
        st.info("Acest grafic arată comparația ratei șomajului între județe pentru anul selectat.")
        df = incarca_date('Somaj')
        ani = sorted([col for col in df.columns if col.startswith('Anul')], key=lambda x: int(x.split()[-1]), reverse=True)
        sex = st.selectbox("Sex", df['Sexe'].unique())
        an = st.selectbox("An", ani, index=0)
        df = df[(df['Sexe'] == sex) & ((df['Judete'].isin(['Alba', 'Brasov', 'Covasna', 'Harghita', 'Mures', 'Sibiu'])) | (df['Judete'].str.upper() == 'TOTAL'))]
        bar_chart_an_interactiv(df, an, f"Rata șomajului pe județe în {an.split()[-1]}", "Rată șomaj (%)", nr_fig)

    elif optiune == "Salariați pe activități economice (bar chart)":
        nr_fig += 3
        st.header("Număr salariați pe activități economice și județe (bar chart)")
        st.info("Acest grafic arată distribuția salariaților pe activități economice pentru fiecare județ.")
        df = incarca_date('Salariati2')
        ani = sorted([col for col in df.columns if col.startswith('Anul')], key=lambda x: int(x.split()[-1]), reverse=True)
        an = st.selectbox("An", ani, index=0)
        df = df[(df['Judete'].isin(['Alba', 'Brasov', 'Covasna', 'Harghita', 'Mures', 'Sibiu'])) | (df['Judete'].str.upper() == 'TOTAL')]
        bar_chart_salariati_activitati(df, ani, an, nr_fig)

    elif optiune == "Structura salariaților pe activități (pie chart pe județe)":
        nr_fig += 4
        st.header("Structura salariaților pe activități economice (pie chart pe județe)")
        st.info("Fiecare pie chart arată structura salariaților pe activități economice pentru un județ.")
        df = incarca_date('Salariati2')
        ani = sorted([col for col in df.columns if col.startswith('Anul')], key=lambda x: int(x.split()[-1]), reverse=True)
        an = st.selectbox("An", ani, index=0)
        df = df[(df['Judete'].isin(['Alba', 'Brasov', 'Covasna', 'Harghita', 'Mures', 'Sibiu'])) | (df['Judete'].str.upper() == 'TOTAL')]
        pie_charts_salariati_judete(df, ani, an, nr_fig)

    elif optiune == "Corelație rată șomaj - ocupare (scatter)":
        nr_fig += 5
        st.header("Corelație între rata șomajului și rata de ocupare a resurselor de muncă (scatter)")
        st.info("Acest scatter plot arată relația dintre rata șomajului și rata de ocupare a resurselor de muncă.")
        df_somaj = incarca_date('Somaj')
        df_resurse = incarca_date('Resurse')
        ani = sorted([col for col in df_somaj.columns if col.startswith('Anul')], key=lambda x: int(x.split()[-1]), reverse=True)
        sex = st.selectbox("Sex", df_somaj['Sexe'].unique())
        df_somaj = df_somaj[(df_somaj['Sexe'] == sex) & ((df_somaj['Judete'].isin(['Alba', 'Brasov', 'Covasna', 'Harghita', 'Mures', 'Sibiu'])) | (df_somaj['Judete'].str.upper() == 'TOTAL'))]
        df_resurse = df_resurse[(df_resurse['Judete'].isin(['Alba', 'Brasov', 'Covasna', 'Harghita', 'Mures', 'Sibiu'])) | (df_resurse['Judete'].str.upper() == 'TOTAL')]
        an = st.selectbox("An", ani, index=0)
        scatter_corelatie_interactiv(
            df_somaj, df_resurse, an,
            f"Corelație rată șomaj - rată de ocupare ({an.split()[-1]})",
            "Rată șomaj (%)", "Rată de ocupare (%)", nr_fig
        )

    elif optiune == "Structura absolvenți pe niveluri (stacked bar)":
        nr_fig += 6
        st.header("Structura absolvenților pe niveluri de educație (stacked bar)")
        st.info("Acest stacked bar chart arată structura absolvenților pe niveluri de educație pentru județul selectat.")
        df = filtreaza_regiunea_centru_si_romania(incarca_date('Absolventi'))
        ani = sorted([col for col in df.columns if col.startswith('Anul')], key=lambda x: int(x.split()[-1]), reverse=True)
        judet = st.selectbox("Alege județul", df['Judete'].unique())
        stacked_bar_absolventi_interactiv(df, ani, judet, nr_fig)

    elif optiune == "Regresie multiplă":
        analiza_regresie_multipla()

if __name__ == "__main__":
    main()
