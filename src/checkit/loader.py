import logging
from sqlalchemy import create_engine, text

# L'URL magique de ton conteneur Docker
# utilisateur:airflow | mot_de_passe:airflow | serveur:postgres | base:airflow
DB_URL = "postgresql+psycopg2://etl_user:mdp_ecriture@postgres-data:5432/checkit_db"
engine = create_engine(DB_URL)

def init_db():
    """Crée la table 'articles' si elle n'existe pas encore dans Postgres"""
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS articles (
                url TEXT PRIMARY KEY,
                title TEXT,
                content TEXT,
                source_type TEXT,
                extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        logging.info("Table 'articles' initialisée.")

def load_to_db(articles_data):
    """Insère les articles et gère les doublons silencieusement"""
    if not articles_data:
        logging.info("Aucun article à charger.")
        return

    init_db() # On s'assure que la table existe avant d'écrire

    with engine.begin() as conn:
        inserted_count = 0
        for article in articles_data:
            query = text("""
                INSERT INTO articles (url, title, content, source_type)
                VALUES (:url, :title, :content, :source)
                ON CONFLICT (url) DO NOTHING;
            """)
            result = conn.execute(query, {
                "url": article['article_url'],
                "title": article['title'],
                "content": article['content'],
                "source": article['source_type']
            })
            inserted_count += result.rowcount # Compte les lignes réellement ajoutées
            
    logging.info(f"{inserted_count} NOUVEAUX articles insérés sur {len(articles_data)} fournis.")

def get_known_urls():
    """Récupère la liste des URLs déjà présentes dans la table articles."""
    init_db()  # On s'assure que la table existe
    with engine.connect() as conn:
        # On ne récupère que la colonne des URLs pour aller très vite
        result = conn.execute(text("SELECT url FROM articles"))
        return {row[0] for row in result} # On renvoie un Set pour une recherche instantanée


def save_metrics(api_count, rss_count, valid_count, execution_time):
    """Enregistre les KPI de la session dans la table etl_metrics."""
    try:
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO etl_metrics 
                    (articles_bruts_api, articles_bruts_rss, articles_valides, temps_execution_secondes)
                    VALUES (:api, :rss, :valides, :temps)
                """),
                {"api": api_count, "rss": rss_count, "valides": valid_count, "temps": execution_time}
            )
        logging.info("Métriques de performance sauvegardées avec succès.")
    except Exception as e:
        logging.error(f"Erreur lors de la sauvegarde des métriques : {e}")