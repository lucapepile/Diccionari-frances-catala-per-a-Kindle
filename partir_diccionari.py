import os
import re
import shutil
import unicodedata

def netejar_divs_repetits(text):
    """Elimina els divs repetits o desbalancejats amb una estratègia més agressiva"""
    # Primer, eliminem els tancaments de div sobrants
    text = re.sub(r'</div>\s*(?=(</div>|<br/>|</idx:entry>))', '', text)
    
    # Netegem els divs buits
    text = re.sub(r'<div[^>]*>\s*</div>', '', text)
    
    # Trobem tots els divs oberts i els paregem amb els tancaments
    divs_oberts = [m.start() for m in re.finditer(r'<div\b[^>]*>', text)]
    divs_tancats = [m.start() for m in re.finditer(r'</div>', text)]
    
    # Si hi ha més divs oberts que tancats, afegim els que falten al final del contingut
    if len(divs_oberts) > len(divs_tancats):
        text += '</div>' * (len(divs_oberts) - len(divs_tancats))
    # Si hi ha més tancaments, eliminem els sobrants (començant pels últims)
    elif len(divs_tancats) > len(divs_oberts):
        for i in range(len(divs_tancats) - 1, len(divs_oberts) - 1, -1):
            text = text[:divs_tancats[i]] + text[divs_tancats[i]+6:]
    
    # Eliminem múltiples <h2></h2> consecutius
    text = re.sub(r'<h2>\s*</h2>', '', text)
    
    # Eliminem múltiples <br/> abans del copyright
    text = re.sub(r'<br/>\s*<br/>\s*(<br/>\s*)*© Carles Castellanos', '<br/>© Carles Castellanos', text)
    # També cobrim el cas on els <br/> apareixen entre dos </div> i el copyright
    text = re.sub(r'</div>\s*<br/>\s*(<br/>\s*)*© Carles Castellanos', '</div>\n© Carles Castellanos', text)
    
    # Netegem espais innecessaris
    text = re.sub(r'\n\s*\n', '\n', text)
    
    return text.strip()

def processar_entrada(linia_titol, homograf=None):
    patrons = [
        re.compile(r'<title type="display">(.*?)</title>'),
        re.compile(r'&lt;title type=&quot;display&quot;&gt;(.*?)&lt;/title&gt;')
    ]
    for patro in patrons:
        coincidencia = patro.search(linia_titol)
        if coincidencia:
            break
    if not coincidencia:
        return None
    linia = coincidencia.group(1)
    linia = re.sub(r'<hi rend="plain">\s*\[\s*ou?\s*', ' [', linia, flags=re.IGNORECASE)
    linia = re.sub(r'</hi>\s*\]\s*', ']', linia)
    linia = re.sub(r'<hi rend="plain">', '', linia)
    linia = re.sub(r'</hi>', '', linia)
    linia = re.sub(r'&lt;hi rend=&quot;plain&quot;&gt;\s*\[\s*ou?\s*', ' [', linia, flags=re.IGNORECASE)
    linia = re.sub(r'&lt;/hi&gt;\s*\]\s*', ']', linia)
    linia = re.sub(r'&lt;hi rend=&quot;plain&quot;&gt;', '', linia)
    linia = re.sub(r'&lt;/hi&gt;', '', linia)
    linia = ' '.join(linia.split())
    return linia

def extreure_paraula_per_ordenar(entrada):
    titol_match = re.search(r'<title type="display">(.*?)</title>', entrada)
    if not titol_match:
        titol_match = re.search(r'&lt;title type=&quot;display&quot;&gt;(.*?)&lt;/title&gt;', entrada)
        if not titol_match:
            return ""
    paraula = processar_entrada(titol_match.group(0))
    if paraula is None:
        return ""
    
    # Neteja inicial de la paraula
    paraula = re.sub(r'\s*\[.*?\]', '', paraula)
    paraula = re.sub(r'^\([^)]+[\'\s]\)', '', paraula)
    paraula = re.sub(r'\(.*?\)', '', paraula)
    
    # Normalització especial per a caràcters especials
    paraula = paraula.replace('œ', 'oe').replace('Œ', 'Oe')  # œ → oe
    paraula = paraula.replace('æ', 'ae').replace('Æ', 'Ae')  # æ → ae
    
    # Normalització Unicode i eliminació de diacrítics
    paraula = unicodedata.normalize('NFD', paraula)
    paraula = ''.join(c for c in paraula if unicodedata.category(c) != 'Mn')
    
    # Convertim a minúscules i netegem
    paraula = paraula.lower().strip()
    
    # Tractament especial per l'apòstrof i guions
    paraula = paraula.replace("'", "").replace("-", "")
    
    return paraula

def dividir_diccionari_complet(arxiu_entrada, carpeta_sortida, num_parts=300):
    os.makedirs(carpeta_sortida, exist_ok=True)
    styles_origen = os.path.join(os.path.dirname(arxiu_entrada), 'styles.css')
    styles_desti = os.path.join(carpeta_sortida, 'styles.css')
    if os.path.exists(styles_origen):
        shutil.copy2(styles_origen, styles_desti)
        print(f"Fitxer styles.css copiat a la carpeta de destí.")
    else:
        print(f"No s'ha trobat el fitxer styles.css a la carpeta d'origen.")
    
    with open(arxiu_entrada, 'r', encoding='utf-8') as fitxer:
        contingut = fitxer.read()
    contingut = re.split(r'<hr>\s*', contingut, maxsplit=1)
    if len(contingut) == 2:
        contingut = '<hr>\n' + contingut[1] # Reafegim el primer <hr> per mantenir coherència
        entrades_text = re.split(r'<hr>\s*', contingut)
    entrades = []
    for entrada_text in entrades_text:
        entrada_text = entrada_text.strip()
        if not entrada_text:
            continue
        if re.search(r'<title type="display">', entrada_text) or re.search(r'&lt;title type=&quot;display&quot;&gt;', entrada_text):
            paraula_ordenar = extreure_paraula_per_ordenar(entrada_text)
            entrades.append((paraula_ordenar, entrada_text))
    # Ordenem les entrades considerant les regles específiques del català
    entrades_ordenades = sorted(entrades, key=lambda x: (
        # Primer ordenem per la paraula normalitzada
        x[0],
        # Després per homògraf si hi ha empat
        int(re.search(r'<lbl type="homograph">(\d+)</lbl>', x[1]).group(1)) 
        if re.search(r'<lbl type="homograph">(\d+)</lbl>', x[1]) else 0
    ))
    
    entrades = [entrada for _, entrada in entrades_ordenades]  # Corregit aquí
    num_entrades = len(entrades)
    if num_entrades == 0:
        print("No s'han trobat entrades al fitxer.")
        return
    mida_part = max(1, num_entrades // num_parts)
    print(f"Total d'entrades: {num_entrades} - Entrades per part: {mida_part}")
    # Capçalera HTML amb el títol del diccionari ja inclòs
    capcalera_html = (
        '<!DOCTYPE html>\n<html xmlns:math="http://exslt.org/math" xmlns:svg="http://www.w3.org/2000/svg" '
        'xmlns:tl="https://kindlegen.s3.amazonaws.com/AmazonKindlePublishingGuidelines.pdf" '
        'xmlns:saxon="http://saxon.sf.net/" xmlns:xs="http://www.w3.org/2001/XMLSchema" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xmlns:cx="https://kindlegen.s3.amazonaws.com/AmazonKindlePublishingGuidelines.pdf" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:mbp="https://kindlegen.s3.amazonaws.com/AmazonKindlePublishingGuidelines.pdf" '
        'xmlns:mmc="https://kindlegen.s3.amazonaws.com/AmazonKindlePublishingGuidelines.pdf" '
        'xmlns:idx="https://kindlegen.s3.amazonaws.com/AmazonKindlePublishingGuidelines.pdf">'
        '<head>'
        '<meta http-equiv="Content-Type" content="text/html; charset=utf-8">'
        '<link href="styles.css" type="text/css" rel="stylesheet" />'
        '<title>Diccionari francès-català</title>'
        '</head>'
        '<body>'
        '<mbp:frameset>')
    # Títol del diccionari (només per la primera part)
    titol_diccionari = '<h1>Diccionari francès-català</h1>\n'
    tancament_html = '  </mbp:frameset>\n  </body>\n</html>'
    for part in range(min(num_parts, num_entrades)):
        inici = part * mida_part
        fi = (part + 1) * mida_part if part < num_parts - 1 else num_entrades
        nom_fitxer = os.path.join(carpeta_sortida, f'part_{part+1:03d}.html')
        with open(nom_fitxer, 'w', encoding='utf-8') as f_sortida:
            f_sortida.write(capcalera_html)
            
            # Afegim el títol només a la primera part (part_001.html) i ABANS de les entrades
            if part == 0:
                f_sortida.write(titol_diccionari)
            for i in range(inici, fi):
                entrada = entrades[i].strip()
                titol_match = re.search(r'<title type="display">(.*?)</title>', entrada)
                if not titol_match:
                    titol_match = re.search(r'&lt;title type=&quot;display&quot;&gt;(.*?)&lt;/title&gt;', entrada)
                    if not titol_match:
                        continue
                homograf_match = re.search(r'<lbl type="homograph">(\d+)</lbl>', entrada)
                if not homograf_match:
                    homograf_match = re.search(r'&lt;lbl type=&quot;homograph&quot;&gt;(\d+)&lt;/lbl&gt;', entrada)
                homograf = homograf_match.group(1) if homograf_match else None
                paraula = processar_entrada(titol_match.group(0))
                if paraula is None:
                    continue
                entrada_neta = re.sub(r'<idx:entry[^>]*>|</idx:entry>', '', entrada)
                contingut_text = re.sub(
                    r'<title type="display">.*?</title>(<lbl type="homograph">\d+</lbl>)?',
                    '',
                    entrada_neta,
                    flags=re.DOTALL
                )
                contingut_text = re.sub(
                    r'&lt;title type=&quot;display&quot;&gt;.*?&lt;/title&gt;(&lt;lbl type=&quot;homograph&quot;&gt;\d+&lt;/lbl&gt;)?',
                    '',
                    contingut_text,
                    flags=re.DOTALL
                )
                contingut_text = netejar_divs_repetits(contingut_text.strip())
                f_sortida.write('<hr>\n<idx:entry name="default" scriptable="yes" spell="yes">\n')
                f_sortida.write(f'<h2><idx:orth>{paraula}</idx:orth>{f"<sup>{homograf}</sup>" if homograf else ""}</h2>\n')
                f_sortida.write(contingut_text + '\n</idx:entry>\n')
            f_sortida.write(tancament_html)
    print(f"Divisió completada! S'han creat {min(num_parts, num_entrades)} parts a la carpeta '{carpeta_sortida}'.")

if __name__ == "__main__":
    import sys
    nom_arxiu = 'diccionari_complet.html'
    if len(sys.argv) > 1:
        nom_arxiu = sys.argv[1]
    dividir_diccionari_complet(nom_arxiu, 'parts_diccionari')
