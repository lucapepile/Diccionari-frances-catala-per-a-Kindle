import requests
from bs4 import BeautifulSoup
import time
from html import escape
import os

# Configuració
SORTIDA_HTML = "diccionari_complet.html"
LOG_ERRORS = "errors.log"
NUM_PAGINES = 4837
BASE_URL = "https://www.diccionari.cat/cerca/diccionari-frances-catala?search_api_fulltext_cust=&search_api_fulltext_cust_1=&field_faceta_cerca_1=5057&page="
SLEEP_TIME = 0.5
RETRY_LIMIT = 5

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/117.0'
}

# Crear capçalera del fitxer HTML si no existeix
if not os.path.exists(SORTIDA_HTML):
    with open(SORTIDA_HTML, "w", encoding="utf-8") as f:
        f.write("""<!DOCTYPE html>
<html lang="ca">
<head>
    <meta charset="utf-8">
    <title>Diccionari francès-català</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            margin: 2em;
            line-height: 1.6;
        }
        h1 {
            color: #1a1a1a;
        }
        h2 {
            color: #2c3e50;
            border-bottom: 2px solid #ccc;
            padding-bottom: 0.2em;
            margin-top: 2em;
        }
        .node__content {
            background-color: #ffffff;
            padding: 1em;
            margin-bottom: 1em;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        hr {
            border: none;
            border-top: 1px solid #ddd;
            margin: 3em 0;
        }
        .dom {
            color: #888;
            font-variant: small-caps;
        }
        .hint, .register {
            color: #888;
            font-style: italic;
        }
        .grammar {
            color: #8B4513;
            font-style: italic;
        }
    </style>
</head>
<body>
<h1>Entrades del diccionari francès-català</h1>
""")

# Paginació
for i in range(0, NUM_PAGINES):
    print(f"🔍 Processant pàgina {i}/{NUM_PAGINES}")
    url = BASE_URL + str(i)

    retry_count = 0
    while retry_count < RETRY_LIMIT:
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            articles = soup.find_all("article", class_="node--type-diccionari-fr-ca")

            with open(SORTIDA_HTML, "a", encoding="utf-8") as f:
                for article in articles:
                    h2 = article.find("h2", class_="node__title")
                    if not h2:
                        continue

                    title_tag = h2.find("title")
                    paraula = title_tag.get_text(strip=True) if title_tag else h2.get_text(strip=True)

                    if not paraula:
                        continue

                    definicio = article.find("div", class_="node__content clearfix")
                    if not definicio:
                        continue

                    f.write(f"<h2>{escape(paraula)}</h2>\n")
                    f.write(str(definicio) + "\n")
                    f.write("<hr>\n")

            time.sleep(SLEEP_TIME)
            break  # Èxit

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, requests.exceptions.RequestException) as e:
            retry_count += 1
            print(f"⚠️ Error de connexió a la pàgina {i}. Reintentant... ({retry_count}/{RETRY_LIMIT})")
            time.sleep(5)

        except Exception as e:
            print(f"❌ Error inesperat a la pàgina {i}: {e}")
            break

    # Si ha fallat tots els intents
    if retry_count >= RETRY_LIMIT:
        print(f"🚨 Error persistent a la pàgina {i}. S'ha afegit al log d'errors.")
        with open(LOG_ERRORS, "a", encoding="utf-8") as logf:
            logf.write(f"{i}\n")

# Tanca el fitxer HTML
with open(SORTIDA_HTML, "a", encoding="utf-8") as f:
    f.write("</body>\n</html>")

print("🎉 Diccionari_complet guardat a:", SORTIDA_HTML)
print("📄 Errors registrats a:", LOG_ERRORS)

