import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go

@st.cache_data
def incarca_date(nume_tabel):
    conexiune = sqlite3.connect('data.sqlite')
    df = pd.read_sql_query(f"SELECT * FROM {nume_tabel}", conexiune)
    conexiune.close()
    return df

def filtreaza_regiunea_centru(df):
    judete_centru = ['Alba', 'Brasov', 'Covasna', 'Harghita', 'Mures', 'Sibiu']
    return df[df['Judete'].isin(judete_centru)]

def extrage_ani(lista_ani):
    return [col.split()[-1] for col in lista_ani]

def converteste_ani_la_float(df, ani):
    for an in ani:
        df[an] = pd.to_numeric(df[an], errors='coerce')
    return df

# Culori consistente pentru județe și România
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
    "C INDUSTRIA PRELUCRATOARE": "Industria prelucrătoare",
    "G COMERT CU RIDICATA SI CU AMANUNTUL; REPARAREA AUTOVEHICULELOR SI MOTOCICLETELOR": "Comerț și reparații auto",
    "Q SANATATE SI ASISTENTA SOCIALA": "Sănătate și asistență socială",
    "P INVATAMANT": "Învățământ",
    "F CONSTRUCTII": "Construcții",
    "H TRANSPORT SI DEPOZITARE": "Transport și depozitare",
    "O ADMINISTRATIE PUBLICA SI APARARE; ASIGURARI SOCIALE DIN SISTEMUL PUBLIC": "Administrație publică și apărare",
    "A AGRICULTURA, SILVICULTURA SI PESCUIT": "Agricultură și silvicultură",
    "I HOTELURI SI RESTAURANTE": "Hoteluri și restaurante",
    "E DISTRIBUTIA APEI; SALUBRITATE, GESTIONAREA DESEURILOR, ACTIVITATI DE DECONTAMINARE": "Distribuția apei și salubritate",
    "M ACTIVITATI PROFESIONALE, STIINTIFICE SI TEHNICE": "Activități profesionale și tehnice",
    "N ACTIVITATI DE SERVICII ADMINISTRATIVE SI ACTIVITATI DE SERVICII SUPORT": "Servicii administrative și suport",
    "K INTERMEDIERI FINANCIARE SI ASIGURARI": "Finanțe și asigurări",
    "B INDUSTRIA EXTRACTIVA": "Industria extractivă",
    "D PRODUCTIA SI FURNIZAREA DE ENERGIE ELECTRICA SI TERMICA, GAZE, APA CALDA SI AER COND": "Energie și utilități",
    "J INFORMATII SI COMUNICATII": "IT și comunicații",
    "L TRANZACTII IMOBILIARE": "Tranzacții imobiliare",
    "R ACTIVITATI DE SPECTACOLE, CULTURALE SI RECREATIVE": "Spectacole și recreere",
    "S ALTE ACTIVITATI DE SERVICII": "Alte servicii",
    "U ACTIVITATI ALE ORGANIZATIILOR SI ORGANISMELOR EXTRATERESTRE": "Organizații internaționale",
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
    fig = go.Figure()
    legend_labels = []
    df_stacked = df_judet.set_index('Niveluri de educatie')[ani].T
    df_stacked = df_stacked.reset_index().rename(columns={'index': 'An'})
    df_stacked['An'] = ani_num
    for i, col in enumerate(df_stacked.columns[1:]):
        fig.add_trace(go.Bar(
            x=df_stacked['An'],
            y=df_stacked[col],
            name=col,
            text=df_stacked[col],
            textfont=dict(size=12),
            marker_color=PALETA[i % len(PALETA)],
            marker_line=dict(width=1.5, color="#222"),
            hovertemplate=f"{col}: "+"%{{y}}"
        ))
        legend_labels.append((PALETA[i % len(PALETA)], col))
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

    show_lines = st.checkbox("Afișează liniile pentru porțiunile mici din pie chart", value=False)

    df['Activitate scurtă'] = df['Activitati ale economiei'].apply(prescurteaza_activitate)

    for judet in judete:
        df_judet = df[df['Judete'] == judet]
        values = df_judet[an_selectat]
        pulls = [0.08 if show_lines and v < values.sum() * 0.07 else 0 for v in values]
        fig = px.pie(
            df_judet,
            names='Activitate scurtă',
            values=an_selectat,
            title=f"{judet}",
            width=800, height=600,
            color_discrete_sequence=PALETA,
            hole=0.3
        )
        fig.update_traces(
            textinfo='percent+label',
            textfont=dict(size=14, family="Segoe UI", color="white"),
            insidetextfont=dict(size=14, family="Segoe UI", color="white"),
            pull=pulls,
            showlegend=True,
            marker_line=dict(width=2, color='white')
        )
        if not show_lines:
            fig.update_traces(textposition='inside')
        else:
            fig.update_traces(textposition='auto')
        fig.update_layout(
            title=dict(font=dict(size=20)),
            legend=dict(font=dict(size=12))
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(f"#### Tabel cu datele pentru {judet} ({nr_fig})")
        st.dataframe(df_judet.set_index('Activitate scurtă')[[an_selectat]])
        st.divider()

    st.markdown("### Legenda activități economice")
    st.markdown(
        "\n".join([f"- **{prescurtare}**: {activitate}" for activitate, prescurtare in PRESCURTARI_ACTIVITATI.items()])
    )
    st.divider()

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
            "Structura absolvenți pe niveluri (stacked bar)"
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
        st.header("Corelație între rata șomajului și rata de ocupare (scatter)")
        st.info("Acest scatter plot arată relația dintre rata șomajului și rata de ocupare a forței de muncă.")
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
        df = filtreaza_regiunea_centru(incarca_date('Absolventi'))
        ani = sorted([col for col in df.columns if col.startswith('Anul')], key=lambda x: int(x.split()[-1]), reverse=True)
        judet = st.selectbox("Alege județul", df['Judete'].unique())
        stacked_bar_absolventi_interactiv(df, ani, judet, nr_fig)

if __name__ == "__main__":
    main()
