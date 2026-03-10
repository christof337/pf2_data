import re
import os
import time
from lxml import etree

def clean_text(text):
    """Nettoie les sauts de ligne et espaces superflus dans les descriptions."""
    return re.sub(r'\s+', ' ', text).strip()

def parse_monster_md(content):
    """Analyse le Markdown pour extraire les données complexes du monstre."""
    monster_data = {}
    start_time = time.time()
    
    print("[PARSING] Début de l'analyse du Markdown...")
    
    # 1. Nettoyage du flux principal (on ignore les en-têtes de page et le lore)
    step_start = time.time()
    print("[PARSING] 1. Extraction du flux principal...")
    main_section = content.split("# FLUX PRINCIPAL (STATS/BASE)")[1]
    print(f"[PARSING]    ✓ Flux principal extrait ({len(main_section)} caractères) - {time.time() - step_start:.3f}s")
    
       # 2. Nom, Niveau et Traits
    step_start = time.time()
    print("[PARSING] 2. Extraction du nom, niveau et traits...")
    header_match = re.search(r'([A-ZÀ-Ÿ][A-ZÀ-Ÿa-zà-ÿ\s\-]*?)\s{2,}(CRÉATURE)\s+(\d+)\s*\n\s*([A-ZÀ-Ÿ\s]+?)(?=\n)', main_section)
    
    if header_match:
        monster_data['name'] = header_match.group(1).strip()
        monster_data['type'] = header_match.group(2).strip()
        monster_data['level'] = header_match.group(3).strip()
        traits_raw = header_match.group(4).strip()
        
        # Divise les traits en mots séparés et ne garde que ceux qui sont en MAJUSCULES
        traits_list = traits_raw.split()
        monster_data['size'] = traits_list[0] if traits_list else "Inconnue"
        monster_data['traits'] = [t for t in traits_list[1:] if t.isupper()]
        
        # Ampute main_section jusqu'à la fin du match (juste avant la nouvelle ligne)
        main_section = main_section[header_match.end():]
        
        print(f"[PARSING]    ✓ Nom: {monster_data['name']}, Niveau: {monster_data['level']}, Traits: {monster_data['traits']} - {time.time() - step_start:.3f}s")
    else:
        print("[PARSING]    ✗ Aucune correspondance trouvée pour le nom/niveau/traits")

       # 3. Perception et Sens
    step_start = time.time()
    print("[PARSING] 3. Extraction de la perception et des sens...")
    # Cherche jusqu'à une nouvelle ligne commençant par une majuscule (avant nettoyage)
    percept_match = re.search(r'Perception\s+\+(\d+)\s*;\s*(.*?)(?=\n\s*[A-ZÀ-Ÿ][a-zà-ÿ]+)', main_section, re.DOTALL)
    if percept_match:
        monster_data['perception_bonus'] = "+" + percept_match.group(1)
        senses_raw = percept_match.group(2).strip()
        
        print(f"[PARSING]    DEBUG perception brute = {repr(senses_raw[:200])}")
        
        # Nettoie les sauts de ligne et espaces excessifs APRÈS le match
        senses_raw = re.sub(r'\s+', ' ', senses_raw)
        
        print(f"[PARSING]    DEBUG perception nettoyée = {repr(senses_raw[:200])}")
        
        monster_data['senses'] = []
        
        # Divise par les virgules pour obtenir les sens individuels
        senses_list = [s.strip() for s in senses_raw.split(',')]
        
        for s in senses_list:
            if not s:
                continue
            
            # Pattern pour capturer: nom (précision) portée
            # Exemples: "odorat (imprécis) 18 m", "vision dans le noir"
            s_match = re.match(r'([a-zA-Zà-ÿ\s]+?)(?:\s*\((.*?)\))?(?:\s*(\d+\s*m))?(?:\s\((.*?)\))?$', s)
            if s_match:
                name = s_match.group(1).strip()
                precision = s_match.group(2) if s_match.group(2) else None
                range_val = s_match.group(3) if s_match.group(3) else None
                source = s_match.group(4) if s_match.group(4) else None
                
                monster_data['senses'].append({
                    'name': name,
                    'precision': precision,
                    'range': range_val,
                    'source': source
                })
                
                print(f"[PARSING]    DEBUG sens trouvé: {name} (precision={precision}, range={range_val}, source={source})")
        
        # Ampute main_section
        main_section = main_section[percept_match.end():]
        
        print(f"[PARSING]    ✓ Perception: {monster_data['perception_bonus']}, Sens: {len(monster_data['senses'])} détectés - {time.time() - step_start:.3f}s")
    else:
        print("[PARSING]    ✗ Aucune correspondance trouvée pour la perception")

    # 4. Langues
    step_start = time.time()
    print("[PARSING] 4. Extraction des langues...")
    # On capture tout jusqu'à la section "Compétences" pour être sûr de ne rien rater
    lang_match = re.search(r'Langues\s+(.*?)(?=\n\s*Compétences)', main_section, re.DOTALL)
    if lang_match:
        full_lang_text = lang_match.group(1).strip()
        
        # On sépare par le point-virgule
        parts = full_lang_text.split(';')
        
        # Langues classiques (partie avant le ;)
        monster_data['languages'] = [l.strip() for l in parts[0].split(',') if l.strip()]
        
        # Partie spéciale (partie après le ;)
        monster_data['lang_special'] = parts[1].strip() if len(parts) > 1 else None
        
        # Ampute main_section
        main_section = main_section[lang_match.end():]
        print(f"[PARSING]    ✓ Langues: {monster_data['languages']}, Spécial: {monster_data['lang_special']}")
    else:
        monster_data['languages'] = []
        monster_data['lang_special'] = None
    
    # 5. Extraction des Compétences (Skills)
    step_start = time.time()
    print("[PARSING] 5. Extraction des compétences...")
    # On cherche "Compétences" jusqu'au prochain bloc (souvent les attributs For, Dex...)
    skills_match = re.search(r'Compétences\s+(.*?)(?=\n\s*(?:For|Dex|Con|Int|Sag|Cha)\s+[\+\-]\d+)', main_section, re.S)
    monster_data['skills'] = []
    if skills_match:
        skills_raw = clean_text(skills_match.group(1))
        # Split par virgule pour isoler chaque compétence
        for s in skills_raw.split(','):
            # Capture le nom et le bonus (ex: Athlétisme +22)
            s_match = re.search(r'(.*?)\s+([\+\-]\d+)', s.strip())
            if s_match:
                monster_data['skills'].append({
                    'name': s_match.group(1).strip(),
                    'bonus': s_match.group(2).strip() # On garde le + pour le style ou on cast en int
                })
        main_section = main_section[skills_match.end():]
        print(f"[PARSING]    ✓ {len(monster_data['skills'])} compétences trouvées.")

    # 6. Extraction des Attributs (Attributes)
    step_start = time.time()
    print("[PARSING] 6. Extraction des attributs...")
    # Mapping FR -> Clés XML demandées
    attr_map = {'For': 'STR', 'Dex': 'DEX', 'Con': 'CON', 'Int': 'INT', 'Sag': 'WIS', 'Cha': 'CHA'}
    monster_data['attributes'] = {}
    
    # On cherche toutes les paires Type +Valeur
    attr_pairs = re.findall(r'(For|Dex|Con|Int|Sag|Cha)\s+([\+\-]\s*\d+)', main_section)
    for key, val in attr_pairs:
        # Nettoyage de la valeur (ex: "+ 6" -> "+6")
        clean_val = val.replace(" ", "")
        monster_data['attributes'][attr_map[key]] = clean_val
    
    print(f"[PARSING]    ✓ Attributs : {monster_data['attributes']}")

    # 5. Statistiques de base (Attributs, CA, PV, Saves)
    # step_start = time.time()
    # print("[PARSING] 5. Extraction des statistiques de base...")
    # attr_pattern = r'(For|Dex|Con|Int|Sag|Cha)\s+([\+\-]\s*\d+)'
    # attrs = re.findall(attr_pattern, main_section)
    # monster_data['attributes'] = {k.upper(): v.replace(" ", "") for k, v in attrs}
    
    ac_search = re.search(r'CA\s+(\d+)', main_section)
    monster_data['ac'] = ac_search.group(1) if ac_search else "0"
    
    hp_search = re.search(r'PV\s+(\d+)', main_section)
    monster_data['hp'] = hp_search.group(1) if hp_search else "0"
    
    saves = re.search(r'Réf\s+([\+\-]\d+),\s*Vig\s+([\+\-]\d+),\s*Vol\s([\+\-]\d+)', main_section)
    if saves:
        monster_data['saves'] = {'REF': saves.group(1), 'FOR': saves.group(2), 'VOL': saves.group(3)}
        spec_save = re.search(r'Vol[\+\-]\d+;\s*(.*?)(?:\n|PV)', main_section)
        if spec_save: 
            monster_data['save_special'] = spec_save.group(1).strip()
        
        # Ampute main_section jusqu'après les saves
        saves_end = re.search(r'Vol[\+\-]\d+[^P]*PV', main_section)
        if saves_end:
            main_section = main_section[saves_end.end():]
    
    print(f"[PARSING]    ✓ CA: {monster_data['ac']}, PV: {monster_data['hp']}, Attributs: {list(monster_data['attributes'].keys())} - {time.time() - step_start:.3f}s")

    # 7.5 Extraction des Vitesses (Speeds)
    step_start = time.time()
    print("[PARSING] 7.5 Extraction des vitesses...")
    # On cherche "Vitesses" jusqu'à la ligne des attaques ou une nouvelle section
    speeds_match = re.search(r'Vitesses\s+(.*?)(?=\n\s*[A-ZÀ-Ÿ]|Corps à corps|À distance)', main_section)
    monster_data['speeds'] = {'list': [], 'special': None}
    
    if speeds_match:
        speeds_raw = clean_text(speeds_match.group(1))
        
        # 1. Séparation du spécial (après le point-virgule)
        parts = speeds_raw.split(';')
        if len(parts) > 1:
            monster_data['speeds']['special'] = parts[1].strip()
            
        # 2. Traitement des vitesses individuelles (avant le point-virgule)
        speeds_list = parts[0].split(',')
        
        # Dictionnaire de traduction vers les types VO autorisés par le XSD
        type_mapping = {
            'vol': 'fly',
            'escalade': 'climb',
            'nage': 'swim',
            'creusement': 'burrow'
        }
        
        for s in speeds_list:
            s = s.strip()
            speed_type = None
            speed_val = s
            
            # Cherche si la vitesse commence par un mot clé connu
            for fr_word, en_word in type_mapping.items():
                if s.lower().startswith(fr_word):
                    speed_type = en_word
                    # On enlève le mot clé pour ne garder que la valeur de la vitesse (ex: "45 m")
                    speed_val = s[len(fr_word):].strip()
                    break
                    
            monster_data['speeds']['list'].append({
                'value': speed_val,
                'type': speed_type
            })
            
        # Ampute main_section pour faire avancer le curseur
        main_section = main_section[speeds_match.end():]
        print(f"[PARSING]    ✓ {len(monster_data['speeds']['list'])} vitesse(s) trouvée(s) - {time.time() - step_start:.3f}s")
    else:
        print(f"[PARSING]    ✗ Aucune vitesse trouvée - {time.time() - step_start:.3f}s")

    # 6. Frappes (Strikes)
    step_start = time.time()
    print("[PARSING] 6. Extraction des frappes...")
    strikes = []
    strike_matches = list(re.finditer(r'Corps à corps\s+(.*?)\s+(\+\d+)\s+\((.*?)\),\s+Dégâts\s+(.*?)(?=Corps à corps|Sorts|Vitesse|Capacités|$)', main_section, re.DOTALL))
    strike_count = 0
    
    for m in strike_matches:
        strike_count += 1
        name = re.sub(r'^1\s+', '', m.group(1).strip())
        bonus = m.group(2).strip()
        traits = [t.strip() for t in m.group(3).split(',')]
        dmg_raw = m.group(4).strip()
        
        dmgs = []
        parts = re.split(r'\s+plus\s+', dmg_raw)
        for p in parts:
            d_match = re.search(r'(\d+d\d+[\+\-]?\d*)\s+(.*)', p, re.DOTALL)
            if d_match:
                damage_type = re.sub(r"^d'", '', d_match.group(2).strip())
                dmgs.append({'amount': d_match.group(1), 'type': damage_type})
        
        strikes.append({'name': name, 'bonus': bonus, 'traits': traits, 'damages': dmgs})
    
    # Ampute main_section après la dernière frappe
    if strike_matches:
        main_section = main_section[strike_matches[-1].end():]
    
    monster_data['strikes'] = strikes
    print(f"[PARSING]    ✓ {strike_count} frappe(s) extraite(s) - {time.time() - step_start:.3f}s")

    # 7. Capacités d'interaction
    step_start = time.time()
    print("[PARSING] 7. Extraction des capacités d'interaction...")
    interaction = []
    aura_match = re.search(r'([A-ZÀ-Ÿa-zà-ÿ\s]+)\s*\((aura.*?)\)\s*(\d+\s*m)\.\s*(.*?)(?=\n[A-Z][a-z]|\nVitesse)', main_section, re.S)
    if aura_match:
        interaction.append({
            'name': aura_match.group(1).strip(),
            'traits': [t.strip() for t in aura_match.group(2).split(',')],
            'desc': clean_text(aura_match.group(3) + ". " + aura_match.group(4))
        })
        
        # Ampute main_section
        main_section = main_section[aura_match.end():]
        
        print(f"[PARSING]    ✓ {len(interaction)} capacité(s) d'interaction trouvée(s) - {time.time() - step_start:.3f}s")
    else:
        print(f"[PARSING]    ✗ Aucune capacité d'interaction trouvée - {time.time() - step_start:.3f}s")
    monster_data['interaction'] = interaction

    # 8. Réactions
    step_start = time.time()
    print("[PARSING] 8. Extraction des réactions...")
    reactive = []
    react_match = re.search(r'([A-ZÀ-Ÿ][a-zà-ÿ\s\']+)\s+Déclencheur\.\s*(.*?)\s*Effet\.\s*(.*?)(?=\n[A-Z]|Vitesse|Capacités)', main_section, re.S)
    if react_match:
        reactive.append({
            'name': react_match.group(1).strip(),
            'trigger': clean_text(react_match.group(2)),
            'effect': clean_text(react_match.group(3)),
            'type': 'reaction'
        })
        
        # Ampute main_section
        main_section = main_section[react_match.end():]
        
        print(f"[PARSING]    ✓ {len(reactive)} réaction(s) trouvée(s) - {time.time() - step_start:.3f}s")
    else:
        print(f"[PARSING]    ✗ Aucune réaction trouvée - {time.time() - step_start:.3f}s")
    monster_data['reactive'] = reactive

    # 9. Sorts
    step_start = time.time()
    print("[PARSING] 9. Extraction des sorts...")
    spells = None
    
    # Cherche d'abord l'en-tête des sorts
    spell_header = re.search(r'Sorts\s+(innés|divins|primordiaux|arcaniques)\s+(.*?)\s+DD\s+(\d+)(?:,\s+attaque\s+([\+\-]\d+))?', main_section, re.DOTALL)
    
    if spell_header:
        s_data = {
            'source': 'innate' if 'inné' in spell_header.group(1) else ('spontaneous' if 'spontané' in spell_header.group(1) else 'prepared'), 
            'tradition': spell_header.group(1), 
            'DD': spell_header.group(3), 
            'attack': spell_header.group(4), 
            'ranks': []
        }
        
        # Récupère le texte à partir de l'en-tête jusqu'à la VRAIE fin de la section sorts
        spells_start = spell_header.start()
        
        # IMPORTANT: cherche jusqu'au premier mot en majuscule en début de ligne (nouvelle section)
        # Format: "\n          NOM DE SECTION" avec au moins 2 majuscules
        next_section = re.search(r'\n\s{0,20}[A-Z]+(?:\s+[A-Z])?', main_section[spells_start:])
        
        if next_section:
            spells_text = main_section[spells_start:spells_start + next_section.start()]
        else:
            spells_text = main_section[spells_start:]
        
        # Nettoie les espaces et sauts de ligne excessifs
        spells_text = re.sub(r'\s+', ' ', spells_text)
        
        # Divise d'abord par les points-virgules
        spell_entries = [s.strip() for s in spells_text.split(';') if s.strip()]
        
        for entry in spell_entries:
            # Saute l'en-tête "Sorts innés divins DD ..."
            if 'DD' in entry or 'Sorts' in entry:
                continue
            
            entry = entry.strip()
            
            # Cas 1: Constant (5e) langage universel
            const_match = re.match(r'Constant\s*\(\s*(\d)e\s*\)\s*(.*?)(?:\s*$|$)', entry)
            if const_match:
                rank = const_match.group(1)
                spell_name = const_match.group(2).strip()
                s_data['ranks'].append({
                    'rank': rank,
                    'spells': [spell_name],
                    'constant': True,
                    'cantrips': False,
                    'special': None
                })
                continue
            
            # Cas 2: Ne <nom> (à volonté) ou Ne <nom> (constant) ou simplement Ne <nom>
            rank_match = re.match(r'(\d)e\s+(.*?)(?:\s*$|$)', entry)
            if rank_match:
                rank = rank_match.group(1)
                spell_info = rank_match.group(2)
                
                # Cherche les annotations spéciales
                special = None
                if '(à volonté)' in spell_info:
                    special = 'à volonté'
                    spell_name = spell_info.replace('(à volonté)', '').strip()
                elif '(constant)' in spell_info.lower():
                    special = 'constant'
                    spell_name = re.sub(r'\(constant\)', '', spell_info, flags=re.IGNORECASE).strip()
                else:
                    spell_name = spell_info.strip()
                
                s_data['ranks'].append({
                    'rank': rank,
                    'spells': [spell_name],
                    'constant': False,
                    'cantrips': False,
                    'special': special
                })
                continue
        
        if s_data['ranks']:
            spells = s_data
            print(f"[PARSING]    ✓ {len(s_data['ranks'])} sort(s) extrait(s) - {time.time() - step_start:.3f}s")
        else:
            print(f"[PARSING]    ✗ Aucun sort trouvé - {time.time() - step_start:.3f}s")
    else:
        print(f"[PARSING]    ✗ En-tête des sorts non trouvé - {time.time() - step_start:.3f}s")
    
    monster_data['spells'] = spells

    total_time = time.time() - start_time
    print(f"[PARSING] ✓ Analyse complète en {total_time:.3f}s\n")
    
    return monster_data



def generate_monster_xml(data, output_path):
    """Transforme le dictionnaire de données data en un fichier XML généré dans output_path"""
    start_time = time.time()
    print("[XML] Début de la génération du fichier XML...")
    
    # Définition de l'URI pour xsi
    XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"

    # Création du nœud racine avec le mappage de l'espace de nom 'xsi'
    root = etree.Element("monsters", nsmap={'xsi': XSI_NS})

    # Ajout de l'attribut noNamespaceSchemaLocation
    # Note : on utilise la notation Clark {URI} pour cibler l'attribut dans l'espace xsi
    root.set(f"{{{XSI_NS}}}noNamespaceSchemaLocation", "../../xslt/monster.xsd")

    # Création de la racine
    step_start = time.time()
    print("[XML] 1. Création de la structure XML de base...")
    monster = etree.SubElement(root, "monster")
    print(f"[XML]    ✓ Racine créée - {time.time() - step_start:.3f}s")
    
    # Identité
    step_start = time.time()
    print("[XML] 2. Ajout de l'identité (nom, type, niveau)...")
    etree.SubElement(monster, "name").text = data.get('name')
    etree.SubElement(monster, "type").text = data.get('type')
    etree.SubElement(monster, "level").text = data.get('level')
    print(f"[XML]    ✓ Identité ajoutée - {time.time() - step_start:.3f}s")
    
    # Traits
    step_start = time.time()
    print("[XML] 3. Ajout des traits de créature...")
    c_traits = etree.SubElement(monster, "creatureTraits")
    etree.SubElement(c_traits, "trait", type="size").text = data.get('size')
    for t in data.get('traits', []):
        etree.SubElement(c_traits, "trait").text = t
    print(f"[XML]    ✓ {1 + len(data.get('traits', []))} trait(s) ajouté(s) - {time.time() - step_start:.3f}s")

    # Perception
    step_start = time.time()
    print("[XML] 4. Ajout de la perception et des sens...")
    percep = etree.SubElement(monster, "perception")
    etree.SubElement(percep, "bonus").text = data.get('perception_bonus')
    senses = etree.SubElement(percep, "senses")
    sense_count = 0
    for s in data.get('senses', []):
        sense_count += 1
        sens = etree.SubElement(senses, "sens")
        etree.SubElement(sens, "name").text = s['name']
        if s['precision']: 
            etree.SubElement(sens, "precision").text = s['precision']
        if s['range']: 
            etree.SubElement(sens, "range").text = s['range']
        if s['source']: 
            etree.SubElement(sens, "source").text = s['source']
    print(f"[XML]    ✓ Perception et {sense_count} sens ajoutés - {time.time() - step_start:.3f}s")

    # Langues
    step_start = time.time()
    print("[XML] 6. Ajout des langues...")
    # Création du nœud parent unique
    langs_node = etree.SubElement(monster, "languages")
    
    # 1. Ajout des langues classiques
    for l in data.get('languages', []):
        etree.SubElement(langs_node, "language").text = l
    
    # 2. Gestion du "Spécial" (ex: ; *langage universel*)
    if data.get('lang_special'):
        special_text = data['lang_special']
        spec_elem = etree.SubElement(langs_node, "langSpecial")
        
        # On cherche si le texte contient de l'italique Markdown (*sort*)
        spell_match = re.search(r'\*(.*?)\*', special_text)
        
        if spell_match:
            # Si on trouve des étoiles, on crée une balise <spell>
            spell_node = etree.SubElement(spec_elem, "spell")
            spell_node.text = spell_match.group(1).strip()
            
            # Note : Si tu as du texte AVANT ou APRÈS l'étoile (ex: "via *sort*"), 
            # il faudrait utiliser spec_elem.text et spell_node.tail, 
            # mais pour PF2e c'est généralement juste le nom du sort.
        else:
            # Sinon, on met juste le texte brut
            spec_elem.text = special_text
            
    print(f"[XML]    ✓ Structure des langues finalisée - {time.time() - step_start:.3f}s")

    # ... (création root, name, type, level, traits, perception, languages) ...

    # 7. Skills (Compétences)
    if data.get('skills'):
        skills_node = etree.SubElement(monster, "skills")
        for s in data['skills']:
            skill_item = etree.SubElement(skills_node, "skill")
            etree.SubElement(skill_item, "name").text = s['name']
            etree.SubElement(skill_item, "bonus").text = str(s['bonus'])

    # 8. Ajout des Attributes (sous forme d'attributs XML)
    # L'ordre dans la balise n'importe pas en XML, mais la balise doit être au bon endroit
    if data.get('attributes'):
        attr_node = etree.SubElement(monster, "attributes")
        # On boucle sur le mapping pour être sûr de ne rien oublier
        for attr_key in ['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA']:
            val = data['attributes'].get(attr_key, "+0") # Valeur par défaut si l'attribut est manquant
            attr_node.set(attr_key, val)

    # 9. Interaction Abilities (Auras, etc.)
    # ... (Ajoute ici tes interactionAbilities avant la CA pour respecter le XSD) ...

    # Défenses
    step_start = time.time()
    print("[XML] 10. Ajout des défenses (CA, PV, Saves)...")
    etree.SubElement(monster, "armorClass").text = data.get('ac')
    save_node = etree.SubElement(monster, "saves", **data.get('saves', {}))
    if 'save_special' in data: 
        save_node.set("saveSpecial", data['save_special'])
    etree.SubElement(monster, "health").text = data.get('hp')
    print(f"[XML]    ✓ Défenses ajoutées - {time.time() - step_start:.3f}s")

    # 11. Vitesses (Speeds)
    # IMPORTANT : À placer APRÈS reactiveAbilities et AVANT strikes
    step_start = time.time()
    print("[XML] 11. Ajout des vitesses...")
    if data.get('speeds') and data['speeds']['list']:
        speeds_node = etree.SubElement(monster, "speeds")
        
        # Attribut speedSpecial s'il y a du texte après le point-virgule
        if data['speeds'].get('special'):
            speeds_node.set("speedSpecial", data['speeds']['special'])
            
        # Création des balises <speed>
        for s in data['speeds']['list']:
            speed_elem = etree.SubElement(speeds_node, "speed")
            speed_elem.text = s['value']
            
            # Ajout de l'attribut type VO uniquement s'il n'est pas None (fly, climb...)
            if s['type']:
                speed_elem.set("type", s['type'])
                
        print(f"[XML]    ✓ Vitesses ajoutées au XML - {time.time() - step_start:.3f}s")
    else:
        # Fallback de sécurité si le monstre n'a pas de bloc vitesse mais que le XSD l'exige
        speeds_node = etree.SubElement(monster, "speeds")
        etree.SubElement(speeds_node, "speed").text = "0 m"
        print(f"[XML]    ⚠ Bloc vitesses créé par défaut (0 m) - {time.time() - step_start:.3f}s")

    # Frappes
    step_start = time.time()
    print("[XML] 7. Ajout des frappes...")
    strikes_node = etree.SubElement(monster, "strikes")
    strike_count = 0
    for strike in data.get('strikes', []):
        strike_count += 1
        strike_elem = etree.SubElement(strikes_node, "strike")
        etree.SubElement(strike_elem, "name").text = strike['name']
        etree.SubElement(strike_elem, "bonus").text = strike['bonus']
        traits_elem = etree.SubElement(strike_elem, "traits")
        for trait in strike['traits']:
            etree.SubElement(traits_elem, "trait").text = trait
        damages_elem = etree.SubElement(strike_elem, "damages")
        for dmg in strike['damages']:
            dmg_elem = etree.SubElement(damages_elem, "damage")
            etree.SubElement(dmg_elem, "amount").text = dmg['amount']
            etree.SubElement(dmg_elem, "damageType").text = dmg['type']
    print(f"[XML]    ✓ {strike_count} frappe(s) ajoutée(s) - {time.time() - step_start:.3f}s")

    # Réactions
    step_start = time.time()
    print("[XML] 8. Ajout des réactions...")
    if data.get('reactive'):
        react = etree.SubElement(monster, "reactiveAbilities")
        react_count = 0
        for r in data['reactive']:
            react_count += 1
            spec = etree.SubElement(react, "special", type="reaction")
            etree.SubElement(spec, "name").text = r['name']
            etree.SubElement(spec, "trigger").text = r['trigger']
            etree.SubElement(spec, "effect").text = r['effect']
        print(f"[XML]    ✓ {react_count} réaction(s) ajoutée(s) - {time.time() - step_start:.3f}s")
    else:
        print(f"[XML]    ℹ Aucune réaction à ajouter - {time.time() - step_start:.3f}s")

    # Sorts
    step_start = time.time()
    print("[XML] 9. Ajout des sorts...")
    if data.get('spells'):
        s = data['spells']
        s_list = etree.SubElement(monster, "spellList", source=s['source'], tradition=s['tradition'], DD=s['DD'])
        if s['attack']: 
            s_list.set("attack", s['attack'])
        rank_count = 0
        spell_total = 0
        for r in s['ranks']:
            rank_count += 1
            r_node = etree.SubElement(s_list, "rank", rank=r['rank'])
            if r.get('constant'): 
                r_node.set("constant", "TRUE")
            if r.get('cantrips'): 
                r_node.set("cantrips", "TRUE")
            spells_node = etree.SubElement(r_node, "spells")
            for sp_name in r['spells']:
                spell_total += 1
                spell_elem = etree.SubElement(spells_node, "spell")
                spell_elem.text = sp_name
                # Ajoute l'attribut spellSpecial si présent
                if r.get('special'):
                    spell_elem.set("spellSpecial", r['special'])
        print(f"[XML]    ✓ {rank_count} rang(s) de sort(s) avec {spell_total} sort(s) total - {time.time() - step_start:.3f}s")
    else:
        print(f"[XML]    ℹ Aucun sort à ajouter - {time.time() - step_start:.3f}s")

    # Sauvegarde
    step_start = time.time()
    print("[XML] 20. Sauvegarde du fichier XML...")

    # Juste avant la sauvegarde finale dans generate_monster_xml :
    tree = etree.ElementTree(root)

    # Création de l'instruction de traitement
    pi = etree.ProcessingInstruction(
        "xml-stylesheet", 
        'href="../../xslt/decodeMonster.xsl" type="text/xsl"'
    )

    # Insertion de l'instruction avant le nœud racine
    root.addprevious(pi)

    # Sauvegarde avec déclaration XML
    tree.write(output_path, encoding="UTF-8", xml_declaration=True, pretty_print=True)
    
    print(f"[XML]    ✓ Fichier sauvegardé à {output_path} - {time.time() - step_start:.3f}s")

    total_time = time.time() - start_time
    print(f"[XML] ✓ Génération complète en {total_time:.3f}s\n")

def validate_xml(xml_path, xsd_path):
    """Vérifie si le fichier XML est valide par rapport au schéma XSD."""
    print(f"[VALIDATION] Vérification de {xml_path} avec {xsd_path}...")
    try:
        # Charger le schéma XSD
        with open(xsd_path, 'rb') as f:
            schema_root = etree.XML(f.read())
        schema = etree.XMLSchema(schema_root)
        
        # Charger le fichier XML
        with open(xml_path, 'rb') as f:
            xml_doc = etree.parse(f)
            
        # Valider
        if schema.validate(xml_doc):
            print("[VALIDATION] ✓ Le fichier XML est VALIDE.")
            return True
        else:
            print("[VALIDATION] ✗ Le fichier XML est INVALIDE !")
            # Afficher les erreurs détaillées
            for error in schema.error_log:
                print(f"    - Ligne {error.line}, colonne {error.column}: {error.message}")
            return False
            
    except Exception as e:
        print(f"[VALIDATION] Erreur lors de la validation : {e}")
        return False

# Exécution
input_file = "./output/subset_4/young_empyreal_dragon.md"
output_file = "./output/subset_4/young_empyreal_dragon2.xml"

print("="*60)
print("DÉBUT DU TRAITEMENT")
print("="*60 + "\n")

start_total = time.time()

if os.path.exists(input_file):
    print(f"[MAIN] Lecture du fichier {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    print(f"[MAIN] ✓ Fichier chargé ({len(md_content)} caractères)\n")
    
    monster_data = parse_monster_md(md_content)
    generate_monster_xml(monster_data, output_file)
    
    print(f"[MAIN] ✓ Succès ! Le fichier {output_file} a été généré.")

    xsd_file = "./xslt/monster.xsd"
    if os.path.exists(output_file) and os.path.exists(xsd_file):
        validate_xml(output_file, xsd_file)
    else:
        print(f"[ERROR] Fichier(s) manquant(s) pour la validation (XML: {output_file}, XSD: {xsd_file})")
else:
    print(f"[MAIN] ✗ Erreur : le fichier {input_file} n'existe pas.")

total_elapsed = time.time() - start_total
print(f"\n[MAIN] Temps total de traitement: {total_elapsed:.3f}s")
print("="*60)