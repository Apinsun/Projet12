import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import os

# Configuration de la page
st.set_page_config(page_title="CheckIt.AI - Monitoring ETL", layout="wide")
st.title("📊 Dashboard de Monitoring ETL - CheckIt.AI")

# --- CONNEXION SÉCURISÉE (Lecture seule) ---
# Si tu lances Streamlit en local sur ta machine (hors Docker),
# on pointe vers localhost et le port exposé (5433)
DB_URL = os.getenv("DASHBOARD_DB_URL", "postgresql+psycopg2://dashboard_user:mdp_lecture@localhost:5433/checkit_db")

@st.cache_data(ttl=60) # Met en cache 60s pour ne pas surcharger la base
def load_data():
    engine = create_engine(DB_URL)
    query = "SELECT * FROM etl_metrics ORDER BY execution_date DESC"
    df = pd.read_sql(query, engine)
    return df

try:
    df = load_data()
    
    if df.empty:
        st.warning("Aucune donnée de métrique trouvée dans la base.")
    else:
        # Récupération de la dernière ligne (l'exécution la plus récente)
        latest = df.iloc[0]
        total_bruts = latest['articles_bruts_api'] + latest['articles_bruts_rss']
        
        # Calcul de la précision (pourcentage d'articles conservés après nettoyage)
        precision = (latest['articles_valides'] / total_bruts * 100) if total_bruts > 0 else 0

        st.subheader(f"Dernière exécution : {latest['execution_date'].strftime('%Y-%m-%d %H:%M:%S')}")

        # --- AFFICHAGE DES KPI PRINCIPAUX ---
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Volume Traité (Brut)", value=total_bruts)
        with col2:
            st.metric(label="Précision (Données valides)", value=f"{precision:.1f} %")
        with col3:
            st.metric(label="Temps d'exécution", value=f"{latest['temps_execution_secondes']} s")

        st.divider()

        # --- GRAPHIQUES D'ÉVOLUTION ---
        st.subheader("📈 Historique des performances")
        
        # On ajoute une colonne pour le total brut
        df['total_bruts'] = df['articles_bruts_api'] + df['articles_bruts_rss']
        
        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            st.markdown("**Temps d'exécution au fil du temps (secondes)**")
            st.line_chart(df, x='execution_date', y='temps_execution_secondes')

        with col_chart2:
            st.markdown("**Volume : Articles Bruts vs Valides**")
            st.line_chart(df, x='execution_date', y=['total_bruts', 'articles_valides'])

except Exception as e:
    st.error(f"Erreur de connexion à la base de données : {e}")
