import requests
from bs4 import BeautifulSoup
import time
from html import escape

SORTIDA_HTML = "diccionari_complet.html"
LOG_ERRORS = "errors.log"
TEMP_LOG = "errors_tmp.log"
BASE_URL = "https://www.diccionari.cat/cerca/diccionari-frances-catala?search_api_fulltext_cust=&search_api_fulltext_cust_1=&field_faceta_cerca_1=5057&page="
SLEEP_TIME = 0.5
RETRY_LIMIT = 5

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/117.0'
}

# Llegeix pàgines amb errors
try:
    with open(LOG_ERRORS, "r", encoding="utf-8") as f:
        pagines_error = [int(line.strip()) for line in f if line.strip().isdigit()]
except FileNotFoundError:
    print("✅ No hi ha errors pendents.")
    exit()

pagines_restants = []

for i in pagines_error:
    print(f"🔁 Reintentant pàgina {i}")
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

    if retry_count >= RETRY_LIMIT:
        print(f"🚨 Encara no s'ha pogut descarregar la pàgina {i}.")
        pagines_restants.append(i)

# Actualitza errors.log amb les pàgines que encara fallen
with open(LOG_ERRORS, "w", encoding="utf-8") as f:
    for page in pagines_restants:
        f.write(f"{page}\n")

print("✅ S'ha acabat el reintent. Pàgines pendents:", pagines_restants if pagines_restants else "cap 🎉")

