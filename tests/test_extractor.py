from checkit.extractor import filter_multimodal_data

def test_filter_multimodal_data():
    """
    Vérifie que la fonction de nettoyage ne conserve que les articles
    possédant à la fois du texte (content ou description) ET une image.
    """
    # 1. GIVEN : On prépare un faux jeu de données avec 3 cas de figure
    raw_data_mock = [
        {
            "title": "Article Parfait", 
            "description": "Ceci est un texte valide.", 
            "image_url": "http://site.com/image.jpg"
        },
        {
            "title": "Article Sans Image", 
            "description": "Texte très intéressant mais pas d'image.", 
            "image_url": None
        },
        {
            "title": "Article Sans Texte", 
            "content": None, 
            "description": None, 
            "image_url": "http://site.com/image.jpg"
        }
    ]

    # 2. WHEN : On fait passer nos fausses données dans le filtre
    clean_data = filter_multimodal_data(raw_data_mock)

    # 3. THEN : On vérifie les affirmations (assertions)
    # Sur les 3 articles, un seul doit survivre
    assert len(clean_data) == 1
    
    # On s'assure que c'est bien le bon article qui a été gardé
    assert clean_data[0]["title"] == "Article Parfait"
    assert clean_data[0]["image_url"] is not None
    assert clean_data[0]["description"] is not None