from unittest.mock import patch
from checkit.scraper import scrape_multimodal_article

# On intercepte la fonction requests.get utilisée dans ton script
@patch('checkit.scraper.requests.get')
def test_scrape_multimodal_article(mock_get):
    """
    Vérifie que la fonction extrait correctement le titre, l'image et le texte
    à partir d'une structure HTML donnée, sans nécessiter de connexion internet.
    """
    
    # 1. GIVEN : On fabrique une fausse réponse HTTP
    class MockResponse:
        def __init__(self):
            # C'est exactement le code HTML que notre BeautifulSoup attend
            self.text = """
            <html>
                <head><meta property="og:image" content="http://fake-image.jpg"></head>
                <body>
                    <h1>Titre de Test</h1>
                    <p>Voici un paragraphe suffisamment long pour passer notre filtre 
                    qui exige au moins 100 caractères. On ajoute un peu de texte pour 
                    atteindre la limite requise. Blablabla blablabla blablabla.</p>
                </body>
            </html>
            """
        def raise_for_status(self):
            pass # On simule que tout s'est bien passé (Code 200)
            
    mock_get.return_value = MockResponse()
    
    # 2. WHEN : On lance notre fonction
    result = scrape_multimodal_article("http://fake-url.com")
    
    # 3. THEN : On vérifie que la data est bien extraite
    assert result is not None
    assert result['title'] == "Titre de Test"
    assert result['image_url'] == "http://fake-image.jpg"
    assert "Voici un paragraphe" in result['content']
