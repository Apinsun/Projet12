# Plan de Monitoring - Pipeline ETL CheckIt.AI

## 1. Objectif du document

Ce document définit la stratégie de surveillance du pipeline d'extraction de données multimodales (textes et images) pour CheckIt.AI. Il vise à garantir la fiabilité, la sécurité et la qualité continue des données alimentant nos modèles d'analyse.

## 2. Indicateurs de Performance (KPIs) Suivis

Un tableau de bord interactif (Streamlit) est mis à disposition des équipes techniques et métiers pour suivre en temps réel la santé du pipeline. Les KPIs surveillés sont :

* 
**Volume (Coût/Ressources) :** Nombre total d'articles bruts extraits via l'API NewsData et le flux RSS.


* 
**Précision (Qualité) :** Pourcentage d'articles conservés après le nettoyage (exclusion des articles sans image ou avec un texte trop court).


* 
**Rapidité (Performance) :** Temps d'exécution total du pipeline d'extraction et de chargement, exprimé en secondes.



## 3. Stratégie de Surveillance

La surveillance s'articule autour de deux axes :

* **Surveillance Automatisée (Airflow) :** Les logs d'exécution sont centralisés dans l'interface UI d'Apache Airflow. Chaque tâche (`extract`, `transform`, `load`) dispose de son propre journal pour isoler rapidement l'origine d'une panne.


* 
**Vérification Humaine (Dashboard) :** Une vérification visuelle du tableau de bord Streamlit doit être effectuée par l'Ingénieur Data au moins **une fois par semaine** pour repérer d'éventuelles dérives (ex: baisse soudaine de la précision due à un changement de structure d'un site source).



## 4. Gestion des Alertes et des Erreurs

Des seuils d'alerte théoriques sont définis pour déclencher une intervention technique:

* **Alerte Qualité (Précision < 50%) :** Si plus de la moitié des articles sont rejetés lors de la transformation, une révision des règles de parsing (BeautifulSoup/JSON) est requise.
* **Alerte Performance (Temps > 60s) :** Un temps d'exécution anormalement long peut indiquer un problème réseau, un blocage d'API (Rate Limit) ou une base de données surchargée.
* 
**Mécanisme de Retry :** En cas d'échec d'une tâche (erreur réseau 500, timeout), Airflow est configuré pour effectuer automatiquement 1 tentative supplémentaire (`retry=1`) après un délai de 2 minutes avant de marquer le DAG en échec définitif.



## 5. Sécurité de la Base de Données

Pour garantir l'intégrité du monitoring et des données en production :

* Le pipeline d'ingestion (Airflow) utilise un rôle restreint (`etl_user`) disposant uniquement des droits de lecture, d'écriture et de mise à jour (`SELECT`, `INSERT`, `UPDATE`).
* Le tableau de bord (Streamlit) utilise un rôle de lecture seule (`dashboard_user` avec uniquement `SELECT`) pour éviter toute altération accidentelle ou malveillante des métriques et des articles.
