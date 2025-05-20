import os
import csv
from bs4 import BeautifulSoup, Tag, NavigableString

# Elimina múltiples <br/> seguits arreu del document
def elimina_br_multiples(soup):
    br_tags = soup.find_all("br")
    i = 0
    while i < len(br_tags) - 1:
        current = br_tags[i]
        next_br = br_tags[i + 1]

        # Elimina el <br/> actual si està seguit per un altre <br/>
        if next_br and current.find_next_sibling() == next_br:
            current.decompose()
            br_tags = soup.find_all("br")  # Actualitza la llista després d’eliminar
            i = 0  # Torna a començar per evitar errors d’índex
        else:
            i += 1

# Elimina <h2> buits i <br/> finals innecessaris
def neteja_html(soup):
    # Elimina <h2> buits
    for h2 in soup.find_all("h2"):
        if not h2.text.strip() and not h2.find():
            h2.decompose()

    # Elimina <br/> finals en blocs
    for tag in soup.find_all(['div', 'li', 'ol']):
        while tag.contents and isinstance(tag.contents[-1], Tag) and tag.contents[-1].name == 'br':
            tag.contents[-1].decompose()

    # Elimina <br/><br/> seguits
    elimina_br_multiples(soup)

# Funció per processar un fitxer HTML i actualitzar-lo
def processa_html(html_path, arrels_flexions):
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    neteja_html(soup)

    # Cerca les entrades amb <idx:orth>
    for idx_orth in soup.find_all("idx:orth"):
        paraula = idx_orth.text.strip()

        if paraula in arrels_flexions:
            # Elimina tots els blocs <idx:infl> dins de <idx:orth>
            for infl in idx_orth.find_all("idx:infl"):
                infl.decompose()

            # Crea un nou bloc <idx:infl>
            idx_infl = soup.new_tag("idx:infl")
            idx_orth.append(idx_infl)

            # Afegeix les flexions, excloent la mateixa paraula i duplicats
            flexions = list(set(arrels_flexions[paraula]) - {paraula})
            for flexio in flexions:
                idx_iform = soup.new_tag("idx:iform", value=flexio)
                idx_infl.append(idx_iform)

    # Sobreescriu el fitxer HTML actualitzat
    with open(html_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(str(soup))

# Llegeix el fitxer CSV de derivades
csv_file = "derivades.csv"
arrels_flexions = {}
with open(csv_file, newline="", encoding="utf-8") as f:
    reader = csv.reader(f)
    for row in reader:
        paraula_arrel = row[0].strip()
        flexions = [col.strip() for col in row[1:] if col.strip()]
        arrels_flexions[paraula_arrel] = flexions

# Carpeta amb els fitxers HTML
html_folder = "parts_diccionari"

# Processa els fitxers HTML que comencen per "part_" i acaben en ".html"
for filename in sorted(os.listdir(html_folder)):
    if filename.startswith("part_") and filename.endswith(".html"):
        html_path = os.path.join(html_folder, filename)
        print(f"Processant: {html_path}")
        processa_html(html_path, arrels_flexions)

print("Processament complet!")

