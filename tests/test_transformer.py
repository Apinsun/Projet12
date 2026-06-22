from checkit.transformer import clean_text, run_transformation_pipeline

def test_clean_text():
    """
    Vérifie que la fonction de nettoyage supprime le HTML, 
    écrase les sauts de ligne et normalise les espaces.
    """
    # 1. GIVEN : Un texte très sale avec du HTML, des sauts de ligne (\n) et des tabulations (\t)
    texte_sale = "<h1>Titre</h1> \n <p>Ceci est un    texte\t avec <b>beaucoup</b>   d'espaces.</p>"
    
    # 2. WHEN : On nettoie le texte
    texte_propre = clean_text(texte_sale, article_ref="Test Unitaire")
    
    # 3. THEN : On s'attend à une phrase parfaite
    attendu = "Titre Ceci est un texte avec beaucoup d'espaces."
    assert texte_propre == attendu
    
    # On vérifie aussi le comportement face au vide
    assert clean_text(None) == ""
    assert clean_text("   ") == ""

def test_run_transformation_pipeline():
    """
    Vérifie que le pipeline global filtre les articles trop courts
    et ajoute bien la métadonnée 'content_length'.
    """
    # 1. GIVEN : Un faux dataset avec un article valide et un article trop court
    raw_data_mock = [
        {
            "article_url": "http://site.com/valide",
            "title": "Article Parfait",
            "content": "Voici un paragraphe suffisamment long pour passer sans aucun problème le fameux filtre des cinquante caractères.",
            "image_url": "http://site.com/image.jpg",
            "source_type": "api_newsdata",
            "extracted_at": "2026-06-18T10:00:00"
        },
        {
            "article_url": "http://site.com/trop-court",
            "title": "Article Bref",
            "content": "Texte de moins de 50 char.", # Ne survivra pas
            "image_url": "http://site.com/image.jpg",
            "source_type": "api_newsdata",
            "extracted_at": "2026-06-18T10:00:00"
        }
    ]

    # 2. WHEN : On fait passer les données dans le pipeline
    processed_data = run_transformation_pipeline(raw_data_mock)

    # 3. THEN : Vérifications
    assert len(processed_data) == 1
    
    article_survivant = processed_data[0]
    assert article_survivant["article_url"] == "http://site.com/valide"
    
    # Vérification que la feature de Machine Learning a bien été générée
    assert "content_length" in article_survivant
    assert article_survivant["content_length"] == len(article_survivant["content"])
