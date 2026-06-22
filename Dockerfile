# On part de l'image officielle que tu utilisais déjà
FROM apache/airflow:2.10.0

# On s'assure d'être avec le bon utilisateur
USER airflow

# 1. On installe Poetry dans le conteneur
RUN pip install --upgrade pip
RUN pip install poetry

# 2. On copie tes fichiers de configuration Poetry depuis ton PC vers le conteneur
COPY pyproject.toml poetry.lock ./

# 3. On configure Poetry pour qu'il ne crée pas de sous-environnement virtuel 
# (car le conteneur Docker EST déjà un environnement isolé)
RUN poetry config virtualenvs.create false

# 4. On installe tes dépendances (beautifulsoup4, python-dotenv, etc.)
RUN poetry install --only main --no-root --no-interaction
