import pandas as pd

print("Iniciant el processament del fitxer Morphalou3.1_CSV.csv...")

# Carrega el CSV a partir de la fila 17 (índex 16)
print("Carregant el fitxer CSV...")
df = pd.read_csv("Morphalou3.1_CSV.csv", sep=";", header=16, dtype=str)

# Neteja els noms de les columnes
print("Netejant els noms de les columnes...")
df.columns = df.columns.str.strip()

# Extreu les columnes necessàries
print("Extraient columnes necessàries...")
df_work = df.iloc[:, [0, 2, 9, 12]].copy()
df_work.columns = ['lemme', 'categorie', 'GRAPHIE', 'mode']

# Propaga les dades per tenir-les completes
print("Propagant dades per completar valors...")
df_work[['lemme', 'categorie', 'mode']] = df_work[['lemme', 'categorie', 'mode']].ffill()

# Neteja textos i valors buits
print("Netejant textos i valors buits...")
df_work['categorie'] = df_work['categorie'].fillna("").astype(str).str.strip().str.lower().replace({'-': ''})
df_work['mode'] = df_work['mode'].fillna("").astype(str).str.strip().str.lower().replace({'-': ''})
df_work['lemme'] = df_work['lemme'].fillna("").astype(str).str.strip()

# Filtra les files amb formes derivades
print("Filtrant files amb formes derivades...")
df_flex = df_work[df_work['GRAPHIE'].notna()].copy()

# Funció per generar variants apostrofades
def afegeix_apostrofs(forma, cat, mode, lemme):
    formes = set()

    # Conversió segura
    forma = str(forma).strip() if pd.notna(forma) else ""
    cat = str(cat).strip().lower().replace('-', '') if pd.notna(cat) else ""
    mode = str(mode).strip().lower().replace('-', '') if pd.notna(mode) else ""
    lemme = str(lemme).strip().lower() if pd.notna(lemme) else ""

    if not forma or forma[0].lower() not in "aeiouhàáèéêëïîôœùü":
        return formes

    # l' i qu' davant de totes les paraules
    formes.update({f"l'{forma}", f"qu'{forma}"})

    # d' a totes excepte verbs que no són infinitiu ni participi
    if not cat.startswith('ver') or (cat.startswith('ver') and mode in ('infinitive', 'participle')):
        formes.add(f"d'{forma}")

    # n', j', m', s', t' a tots els verbs
    if cat.startswith('ver'):
        for prefix in ['n', 'j', 'm', 's', 't']:
            formes.add(f"{prefix}'{forma}")

    # c' només amb être
    if cat.startswith('ver') and lemme == 'être':
        formes.add(f"c'{forma}")

    return formes

# Genera flexions i variants
print("Generant flexions i variants apostrofades...")

# Flexions originals
print("Processant flexions originals...")
deriv = df_flex[['lemme', 'GRAPHIE', 'categorie', 'mode']].copy()
deriv['GRAPHIE'] = deriv['GRAPHIE'].fillna("").astype(str).str.strip()

# Variants apostrofades de derivats
print("Generant variants apostrofades dels derivats...")
deriv['variants'] = deriv.apply(lambda r: afegeix_apostrofs(r['GRAPHIE'], r['categorie'], r['mode'], r['lemme']), axis=1)
variants_deriv = deriv.explode('variants')[['lemme', 'variants']].rename(columns={'variants': 'GRAPHIE'})
variants_deriv['GRAPHIE'] = variants_deriv['GRAPHIE'].fillna("").astype(str).str.strip()

# Variants apostrofades dels lemes
print("Generant variants apostrofades dels lemes...")
lemes_unique = df_work[['lemme', 'categorie', 'mode']].drop_duplicates(subset='lemme')
lemes_unique['root_variants'] = lemes_unique.apply(lambda r: afegeix_apostrofs(r['lemme'], r['categorie'], r['mode'], r['lemme']), axis=1)
variants_root = lemes_unique.explode('root_variants')[['lemme', 'root_variants']].rename(columns={'root_variants': 'GRAPHIE'})
variants_root['GRAPHIE'] = variants_root['GRAPHIE'].fillna("").astype(str).str.strip()

# Combina totes les formes
print("Combinant totes les formes...")
totes = pd.concat([
    deriv[['lemme', 'GRAPHIE']],
    variants_deriv[['lemme', 'GRAPHIE']],
    variants_root[['lemme', 'GRAPHIE']]
])

# Elimina duplicats i formes iguals al lema
print("Eliminant duplicats i formes iguals al lema...")
totes = totes[(totes['GRAPHIE'] != totes['lemme']) & (totes['GRAPHIE'] != "")].drop_duplicates()
totes['GRAPHIE'] = totes['GRAPHIE'].astype(str).str.strip()

# Agrupa per lema
print("Agrupant per lema...")
gruppat = totes.groupby('lemme')['GRAPHIE'].apply(lambda x: sorted(x)).reset_index()

# Expandeix a columnes
print("Expandint formes a columnes...")
formes_expandides = pd.DataFrame(gruppat['GRAPHIE'].tolist())
resultat_final = pd.concat([gruppat['lemme'], formes_expandides], axis=1)

# Desa resultat
target = "derivades.csv"
print(f"Guardant resultats a '{target}'...")
resultat_final.to_csv(target, index=False)
print(f"Procés completat! Guardat '{target}' amb {resultat_final.shape[0]} lemes i fins a {formes_expandides.shape[1]} derivades")
