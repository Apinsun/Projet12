import logging
from sqlalchemy import create_engine, text

# L'URL magique de ton conteneur Docker
# utilisateur:airflow | mot_de_passe:airflow | serveur:postgres | base:airflow
DB_URL = "postgresql+psycopg2://airflow:airflow@postgres:5432/airflow"
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
