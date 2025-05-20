import re
import csv
import os

def extreure_paraula_titol(linia_titol):
    """Extreu la paraula principal d'una línia de títol"""
    patro = re.compile(r'<h2>&lt;title type=&quot;display&quot;&gt;(.*?)&lt;/title&gt;</h2>')
    coincidencia = patro.search(linia_titol)
    
    if not coincidencia:
        return None
    
    linia = coincidencia.group(1)
    
    # Processem variants entre claudàtors i netegem etiquetes HTML
    linia = re.sub(r'&lt;hi rend=&quot;plain&quot;&gt;\s*\[\s*ou?\s*', ' [', linia, flags=re.IGNORECASE)
    linia = re.sub(r'&lt;/hi&gt;\s*\]\s*', ']', linia)
    linia = re.sub(r'&lt;hi rend=&quot;plain&quot;&gt;', '', linia)
    linia = re.sub(r'&lt;/hi&gt;', '', linia)
    
    # Si hi ha variants entre claudàtors, només agafem la paraula principal
    paraula_principal = linia.split('[')[0].strip()
    
    # Netegem espais addicionals
    paraula_principal = ' '.join(paraula_principal.split())
    return paraula_principal

def obtenir_entrades_diccionari(fitxer_html):
    """Obté totes les entrades del diccionari des de l'HTML"""
    print(f"Llegint entrades del fitxer {fitxer_html}...")
    
    entrades = []
    
    try:
        # Llegim tot el contingut
        with open(fitxer_html, 'r', encoding='utf-8') as fitxer:
            contingut = fitxer.read()
        
        # Extraiem la primera part (abans del primer <hr>)
        primera_part = re.split(r'<hr>', contingut, 1)[0]
        
        # Busquem si hi ha un títol a la primera part
        titols_primera_part = re.findall(r'<h2>&lt;title type=&quot;display&quot;&gt;(.*?)&lt;/title&gt;</h2>', primera_part)
        if titols_primera_part:
            for titol in titols_primera_part:
                linia_titol = f'<h2>&lt;title type=&quot;display&quot;&gt;{titol}&lt;/title&gt;</h2>'
                paraula = extreure_paraula_titol(linia_titol)
                if paraula:
                    entrades.append(paraula)
        
        # Extraiem la resta d'entrades (després dels <hr>)
        parts = re.split(r'<hr>\s*', contingut)[1:]
        
        for part in parts:
            linies = part.split('\n')
            titols = [linia.strip() for linia in linies if re.search(r'<h2>&lt;title type=&quot;display&quot;&gt;', linia)]
            
            if titols:
                paraula = extreure_paraula_titol(titols[0])
                if paraula:
                    entrades.append(paraula)
        
        print(f"S'han trobat {len(entrades)} entrades al diccionari.")
        return entrades
    
    except Exception as e:
        print(f"Error llegint el fitxer HTML: {str(e)}")
        return []

def obtenir_paraules_csv(fitxer_csv):
    """Obté les paraules de la primera columna del fitxer CSV"""
    print(f"Llegint paraules del fitxer {fitxer_csv}...")
    
    paraules = set()
    
    try:
        with open(fitxer_csv, 'r', encoding='utf-8') as fitxer:
            lector_csv = csv.reader(fitxer)
            for fila in lector_csv:
                if fila and len(fila) > 0:
                    paraula = fila[0].strip()
                    if paraula:
                        paraules.add(paraula)
        
        print(f"S'han trobat {len(paraules)} paraules al fitxer CSV.")
        return paraules
    
    except Exception as e:
        print(f"Error llegint el fitxer CSV: {str(e)}")
        return set()

def verificar_entrades(fitxer_html, fitxer_csv, fitxer_sortida):
    """Verifica si totes les entrades del diccionari són al fitxer CSV"""
    entrades_diccionari = obtenir_entrades_diccionari(fitxer_html)
    paraules_csv = obtenir_paraules_csv(fitxer_csv)
    
    # Trobem les entrades que no són al CSV
    entrades_no_trobades = []
    
    for entrada in entrades_diccionari:
        if entrada not in paraules_csv:
            entrades_no_trobades.append(entrada)
    
    # Escrivim les entrades no trobades al fitxer de sortida
    if entrades_no_trobades:
        try:
            with open(fitxer_sortida, 'w', encoding='utf-8') as fitxer:
                fitxer.write("Entrades del diccionari no trobades al fitxer CSV:\n\n")
                for entrada in entrades_no_trobades:
                    fitxer.write(f"{entrada}\n")
            
            print(f"S'han trobat {len(entrades_no_trobades)} entrades que no són al CSV.")
            print(f"S'han desat les entrades no trobades al fitxer {fitxer_sortida}.")
        
        except Exception as e:
            print(f"Error escrivint al fitxer de sortida: {str(e)}")
    
    else:
        print("Totes les entrades del diccionari són al fitxer CSV.")

# Exemple d'ús
if __name__ == "__main__":
    fitxer_html = 'diccionari_complet.html'
    fitxer_csv = 'derivades.csv'
    fitxer_sortida = 'entrades_no_trobades.txt'
    
    verificar_entrades(fitxer_html, fitxer_csv, fitxer_sortida)
