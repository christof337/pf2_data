import re
import os
import sys
import time
from lxml import etree
from xml_validator import validate_xml

# ==========================================
# UTILITAIRES DE TEXTE
# ==========================================

def clean_text(text):
    """Nettoie les sauts de ligne et espaces superflus."""
    return re.sub(r'\s+', ' ', text).strip()

# ==========================================
# PARSING SPÉCIFIQUE MONSTRES
# ==========================================

def parse_ability_block(text):
    """Extraction robuste des capacités, traits et actions depuis le bloc Markdown."""
    abilities = []
    if not text or not text.strip(): 
        return abilities
    
    # 1. Capture des titres en gras (évite de capturer les listes à puces)
    pattern = r'(?:^|\n)[ \t]*(?:([0-3,9R])[ \t]*\n)?[ \t]*\*\*([A-ZÀ-Ÿ][^*]+?)\*\*'
    all_matches = list(re.finditer(pattern, text))
    
    # 2. Filtrage des mots-clés "Déclencheur" et "Effet" pour isoler les capacités parentes
    matches = [m for m in all_matches if m.group(2).strip().rstrip('.').lower() not in ["déclencheur", "effet"]]
    
    for i, m in enumerate(matches):
        action_code = m.group(1)
        name = m.group(2).strip().rstrip('.')
        
        # Délimitation du bloc courant
        start = m.end()
        end = matches[i+1].start() if i+1 < len(matches) else len(text)
        raw_body = text[start:end].strip()
        
        ability = {
            'name': name,
            'traits': [],
            'action_code': action_code,
            'trigger': None, 
            'effect': None, 
            'desc': None,
            'list_items': []
        }
        
        # A. Capture de l'action si elle est située sous le titre
        if not ability['action_code']:
            action_match = re.search(r'^\s*([0-3,9R])', raw_body)
            if action_match:
                ability['action_code'] = action_match.group(1)
                raw_body = raw_body[action_match.end():].strip()

        # B. Extraction des traits de la capacité
        traits_match = re.search(r'^\s*\((.*?)\)', raw_body)
        if traits_match:
            ability['traits'] = [t.strip() for t in traits_match.group(1).split(',')]
            raw_body = raw_body[traits_match.end():].strip()
            
        # C. Séparation Trigger / Effet
        trigger_match = re.search(r'(?:\*\*Déclencheur\.?\*\*|Déclencheur\.)\s*(.*?)(?=(?:\*\*Effet\.?\*\*|Effet\.)|$)', raw_body, re.DOTALL | re.IGNORECASE)
        effect_match = re.search(r'(?:\*\*Effet\.?\*\*|Effet\.)\s*(.*)', raw_body, re.DOTALL | re.IGNORECASE)
        
        if trigger_match:
            ability['trigger'] = clean_text(trigger_match.group(1))
        if effect_match:
            ability['effect'] = clean_text(effect_match.group(1))

        # D. Description (texte précédant le déclencheur/effet)
        desc_parts = re.split(r'\*\*Déclencheur\.?\*\*|Déclencheur\.|\*\*Effet\.?\*\*|Effet\.', raw_body, flags=re.IGNORECASE)
        desc_raw = desc_parts[0].strip()
        
        # E. Extraction des listes à puces
        if '•' in desc_raw:
            parts = re.split(r'\s*•\s*', desc_raw)
            intro = parts[0].strip()
            ability['list_items'] = [clean_text(p) for p in parts[1:] if p.strip()]
            ability['desc'] = clean_text(intro) if intro else None
        else:
            ability['desc'] = clean_text(desc_raw) if desc_raw else None
            
        abilities.append(ability)
        
    return abilities

def parse_monster_md(content):
    """Analyse le Markdown brut (issu de pdfplumber) pour extraire les données du monstre."""
    monster_data = {}
    print("[PARSING] Début de l'analyse du Markdown...")
    
    # 1. Flux principal
    main_section = content.split("# FLUX PRINCIPAL (STATS/BASE)")[1]
    
    # 2. Nom, Niveau et Traits globaux
    header_match = re.search(r'([A-ZÀ-Ÿ\s\-]+?)\s+(CRÉATURE)\s+(\d+)', main_section)
    if header_match:
        monster_data['name'] = clean_text(header_match.group(1))
        monster_data['type'] = header_match.group(2).strip()
        monster_data['level'] = header_match.group(3).strip()
        
        traits_match = re.search(r'(TRÈS PETITE|PETITE|MOYENNE|GRANDE|TRÈS GRANDE|GIGANTESQUE)\s+([A-ZÀ-Ÿ\s]+)(?=\n|Perception)', main_section)
        if traits_match:
            monster_data['size'] = traits_match.group(1).strip()
            monster_data['traits'] = [t for t in traits_match.group(2).split() if t.isupper()]
            
        main_section = main_section[header_match.end():]
        print(f"[PARSING]    ✓ Nom: {monster_data['name']}, Niveau: {monster_data['level']}")

    # 3. Perception
    percept_match = re.search(r'Perception\*\*\s*\+?(\d+)\s*;\s*(.*?)(?=\n\s*\*\*)', main_section, re.DOTALL)
    if percept_match:
        monster_data['perception_bonus'] = "+" + percept_match.group(1)
        senses_raw = clean_text(percept_match.group(2))
        monster_data['senses'] = []
        for s in senses_raw.split(','):
            if not s.strip(): continue
            s_match = re.match(r'([a-zA-Zà-ÿ\s]+?)(?:\s*\((.*?)\))?(?:\s*(\d+\s*m))?(?:\s\((.*?)\))?$', s.strip())
            if s_match:
                monster_data['senses'].append({
                    'name': s_match.group(1).strip(),
                    'precision': s_match.group(2),
                    'range': s_match.group(3),
                    'source': s_match.group(4)
                })
        main_section = main_section[percept_match.end():]
        print(f"[PARSING]    ✓ Perception et {len(monster_data['senses'])} sens détectés.")

    # 4. Langues
    lang_match = re.search(r'\*\*Langues\*\*\s+(.*?)(?=\n\s*\*\*Compétences)', main_section, re.DOTALL)
    if lang_match:
        parts = lang_match.group(1).split(';')
        monster_data['languages'] = [l.strip() for l in parts[0].split(',') if l.strip()]
        monster_data['lang_special'] = clean_text(parts[1]) if len(parts) > 1 else None
        main_section = main_section[lang_match.end():]
    
    # 5. Compétences
    skills_match = re.search(r'\*\*Compétences\*\*\s+(.*?)(?=\n\s*\*\*For)', main_section, re.S)
    monster_data['skills'] = []
    if skills_match:
        for s in clean_text(skills_match.group(1)).split(','):
            s_m = re.search(r'(.*?)\s+([\+\-]\d+)', s.strip())
            if s_m: monster_data['skills'].append({'name': s_m.group(1).strip(), 'bonus': s_m.group(2).strip()})
        main_section = main_section[skills_match.end():]

    # 6. Attributs
    attr_map = {'For': 'STR', 'Dex': 'DEX', 'Con': 'CON', 'Int': 'INT', 'Sag': 'WIS', 'Cha': 'CHA'}
    monster_data['attributes'] = {}
    attr_match = re.search(r'(\*\*For\*\*\s+[\+\-]\s*\d+.*?\*\*Cha\*\*\s+[\+\-]\s*\d+)', main_section, re.S)
    if attr_match:
        pairs = re.findall(r'\*\*(For|Dex|Con|Int|Sag|Cha)\*\*\s+([\+\-]\s*\d+)', attr_match.group(1))
        for key, val in pairs: monster_data['attributes'][attr_map[key]] = val.replace(" ", "")
        main_section = main_section[attr_match.end():].lstrip()

    # 7. Capacités d'interaction
    ca_match = re.search(r'(?:^|\n)\*\*CA\s*\*\*', main_section)
    if ca_match:
        monster_data['interaction_abilities'] = parse_ability_block(main_section[:ca_match.start()])
        main_section = main_section[ca_match.start():].lstrip()
    else: 
        monster_data['interaction_abilities'] = []

    # 8. Défenses (CA, PV, Sauvegardes, Immunités, Faiblesses)
    pv_match = re.search(r'\*\*PV\s*\*\*\s*\d+', main_section)
    if pv_match:
        end_def = re.search(r'(?:\n\s*(?:\d+\s*\n)?\s*\*\*|\n\s*\*\*Vitesses)', main_section[pv_match.end():])
        cut_idx = pv_match.end() + end_def.start() if end_def else len(main_section)
        defenses_text = clean_text(main_section[:cut_idx])
        main_section = main_section[cut_idx:].lstrip()
        
        ac_m = re.search(r'\*\*CA\s*\*\*\s*(\d+)', defenses_text)
        monster_data['ac'] = ac_m.group(1) if ac_m else "0"
        
        hp_m = re.search(r'\*\*PV\s*\*\*\s*(\d+)', defenses_text)
        monster_data['hp'] = hp_m.group(1) if hp_m else "0"
        
        saves_m = re.search(r'\*\*Réf\s*\*\*\s*([\+\-]\d+).*?\*\*Vig\s*\*\*\s*([\+\-]\d+).*?\*\*Vol\s*\*\*\s*([\+\-]\d+)', defenses_text)
        if saves_m: monster_data['saves'] = {'REF': saves_m.group(1), 'FOR': saves_m.group(2), 'WIL': saves_m.group(3)}
        
        save_spec = re.search(r'\*\*Vol\s*\*\*\s*[\+\-]\d+\s*;\s*(.*?)(?=\*\*PV|$)', defenses_text)
        if save_spec: monster_data['save_special'] = save_spec.group(1).strip()

        imm_m = re.search(r'\*\*Immunités\s*\*\*\s*(.*?)(?:;|$)', defenses_text)
        monster_data['immunities'] = [i.strip() for i in imm_m.group(1).split(',')] if imm_m else []
        
        weak_m = re.search(r'\*\*Faiblesse[s]?\s*\*\*\s*([a-zA-Zà-ÿ\s]+)\s+(\d+)', defenses_text)
        monster_data['weaknesses'] = [{'name': weak_m.group(1).strip(), 'value': weak_m.group(2)}] if weak_m else []
        print("[PARSING]    ✓ Défenses extraites.")

    # 9. Capacités réactives
    vit_match = re.search(r'(?:^|\n)\*\*Vitesses\*\*', main_section)
    if vit_match:
        monster_data['reactive_abilities'] = parse_ability_block(main_section[:vit_match.start()])
        main_section = main_section[vit_match.start():].lstrip()
    else: 
        monster_data['reactive_abilities'] = []

    # 10. Vitesses
    speeds_m = re.search(r'\*\*Vitesses\*\*\s+(.*?)(?=\n\s*(?:\d+\s*)?\*\*Corps à corps|\n\s*(?:\d+\s*)?\*\*À distance|\n\s*[A-ZÀ-Ÿ])', main_section)
    monster_data['speeds'] = {'list': [], 'special': None}
    if speeds_m:
        parts = clean_text(speeds_m.group(1)).split(';')
        if len(parts) > 1: monster_data['speeds']['special'] = parts[1].strip()
        
        for s in parts[0].split(','):
            s = s.strip()
            speed_type = next((en for fr, en in {'vol': 'fly', 'escalade': 'climb', 'nage': 'swim', 'creusement': 'burrow'}.items() if s.lower().startswith(fr)), None)
            val = re.sub(r'^(vol|escalade|nage|creusement)\s+', '', s, flags=re.IGNORECASE).strip()
            monster_data['speeds']['list'].append({'value': val, 'type': speed_type})
        main_section = main_section[speeds_m.end():]

    # 11. Frappes (Strikes)
    strikes = []
    strike_matches = list(re.finditer(r'\*\*(Corps à corps|À distance)\*\*\s+(.*?)\s+([\+\-]\d+)\s+\((.*?)\),\s*\*\*Dégâts\s*\*\*\s*(.*?)(?=\n\s*(?:\d+\s*)?\*\*(?:Corps à corps|À distance|Sorts|[A-ZÀ-Ÿ])|$)', main_section, re.DOTALL))
    
    for m in strike_matches:
        strike_type = "melee" if m.group(1).strip().lower() == "corps à corps" else "ranged"
        raw_name = clean_text(m.group(2))
        clean_name = re.sub(r'^\d+\s+', '', raw_name).strip()

        # Protection des virgules décimales dans les traits (ex: 4,5 m)
        raw_traits = re.sub(r'(\d),(\d)', r'\1__DECIMAL__\2', m.group(4))
        traits_list = [t.strip().replace('__DECIMAL__', ',') for t in raw_traits.split(',')]

        dmgs = []
        for p in re.split(r'\s+plus\s+', clean_text(m.group(5))):
            d_m = re.search(r'(\d+d\d+[\+\-]?\d*)\s+(.*)', p)
            if d_m: dmgs.append({'amount': d_m.group(1), 'type': re.sub(r"^d'", '', d_m.group(2).strip())})
            
        strikes.append({
            'type': strike_type,
            'name': clean_name, 
            'bonus': m.group(3).strip(), 
            'traits': traits_list,
            'damages': dmgs
        })
        
    if strike_matches: 
        main_section = main_section[strike_matches[-1].end():]
        
    monster_data['strikes'] = strikes

    # 12. Sorts
    spell_h = re.search(r'\*\*Sorts\s+(.*?)\*\*\s*DD\s+(\d+)(?:,\s+attaque\s+([\+\-]\d+))?', main_section)
    if spell_h:
        next_sec = re.search(r'\n\s*(?:\d+\s*\n)?\s*\*\*[A-ZÀ-Ÿ]', main_section[spell_h.end():])
        end_pos = spell_h.end() + next_sec.start() if next_sec else len(main_section)
        
        spells_text = re.sub(r'\*+', '', main_section[spell_h.start():end_pos])
        main_section = main_section[end_pos:]
        
        s_data = {
            'source': 'innate' if 'inné' in spell_h.group(1) else ('spontaneous' if 'spontané' in spell_h.group(1) else 'prepared'), 
            'tradition': 'divine' if 'divins' in spell_h.group(1) else ('arcane' if 'arcaniques' in spell_h.group(1) else ('occult' if 'occultes' in spell_h.group(1) else ('primal' if 'primordiaux' in spell_h.group(1) else None))), 
            'DD': spell_h.group(2), 'attack': spell_h.group(3), 'ranks': []
        }
        
        for entry in [s.strip() for s in clean_text(spells_text).split(';') if s.strip() and not 'DD' in s and not 'Sorts' in s]:
            const_match = re.match(r'Constant\s*\(\s*(\d)e\s*\)\s*(.*)', entry)
            if const_match:
                s_data['ranks'].append({'rank': const_match.group(1), 'spells': [const_match.group(2).strip()], 'constant': True, 'cantrips': False, 'special': None})
                continue
            rank_match = re.match(r'(\d)e\s+(.*)', entry)
            if rank_match:
                spell_info = rank_match.group(2)
                special = 'à volonté' if '(à volonté)' in spell_info else ('constant' if '(constant)' in spell_info else None)
                s_data['ranks'].append({'rank': rank_match.group(1), 'spells': [re.sub(r'\((à volonté|constant)\)', '', spell_info).strip()], 'constant': False, 'cantrips': False, 'special': special})
        monster_data['spells'] = s_data

    # 13. Capacités offensives (Le reste)
    # Exclut les blocs de texte annexes (ex: Lore en fin de page)
    footer_match = re.search(r'\n\s*\*\*?[A-ZÀ-Ÿ\s]{10,}', main_section)
    offensive = main_section[:footer_match.start()].strip() if footer_match else main_section
    monster_data['offensive_abilities'] = parse_ability_block(offensive)

    return monster_data

# ==========================================
# GÉNÉRATION XML
# ==========================================

def add_abilities_to_xml(parent_node, abilities_list, tag_name):
    """Génère un bloc XML (ex: offensiveAbilities) à partir d'une liste de capacités."""
    if not abilities_list: return
    
    container = etree.SubElement(parent_node, tag_name)
    for abi in abilities_list:
        if abi['action_code'] == '9':
            spec = etree.SubElement(container, "special", type="reaction")
        elif abi['action_code'] in ['0', '1', '2', '3']:
            spec = etree.SubElement(container, "special", type="activity", actions=abi['action_code'])
        else:
            spec = etree.SubElement(container, "special")

        etree.SubElement(spec, "name").text = abi['name']
        
        if abi['traits']:
            t_node = etree.SubElement(spec, "traits")
            for t in abi['traits']:
                etree.SubElement(t_node, "trait").text = t
        
        if abi['trigger']:
            etree.SubElement(spec, "trigger").text = abi['trigger']
            target_node = etree.SubElement(spec, "effect")
            content_text = abi['effect']
        else:
            target_node = etree.SubElement(spec, "description")
            content_text = abi['desc']

        if content_text:
            target_node.text = content_text
        
        if abi['list_items']:
            list_node = etree.SubElement(target_node, "list")
            for item in abi['list_items']:
                etree.SubElement(list_node, "listItem").text = item

def generate_monster_xml(data, output_path):
    """Transforme le dictionnaire de données en un fichier XML formaté."""
    start_time = time.time()
    print("[XML] Début de la génération du fichier XML...")
    
    XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
    root = etree.Element("monsters", nsmap={'xsi': XSI_NS})
    root.set(f"{{{XSI_NS}}}noNamespaceSchemaLocation", "../../xslt/monster.xsd")

    monster = etree.SubElement(root, "monster")
    
    # Identité
    etree.SubElement(monster, "name").text = data.get('name')
    etree.SubElement(monster, "type").text = data.get('type')
    etree.SubElement(monster, "level").text = data.get('level')
    
    # Traits
    c_traits = etree.SubElement(monster, "creatureTraits")
    etree.SubElement(c_traits, "trait", type="size").text = data.get('size')
    for t in data.get('traits', []):
        etree.SubElement(c_traits, "trait").text = t

    # Perception
    percep = etree.SubElement(monster, "perception")
    etree.SubElement(percep, "bonus").text = data.get('perception_bonus')
    senses = etree.SubElement(percep, "senses")
    for s in data.get('senses', []):
        sens = etree.SubElement(senses, "sens")
        etree.SubElement(sens, "name").text = s['name']
        if s['precision']: etree.SubElement(sens, "precision").text = s['precision']
        if s['range']: etree.SubElement(sens, "range").text = s['range']
        if s['source']: etree.SubElement(sens, "source").text = s['source']

    # Langues
    langs_node = etree.SubElement(monster, "languages")
    for l in data.get('languages', []):
        etree.SubElement(langs_node, "language").text = l
    
    if data.get('lang_special'):
        special_text = data['lang_special']
        spec_elem = etree.SubElement(langs_node, "langSpecial")
        spell_match = re.search(r'\*(.*?)\*', special_text)
        if spell_match:
            spell_node = etree.SubElement(spec_elem, "spell")
            spell_node.text = spell_match.group(1).strip()
        else:
            spec_elem.text = special_text
            
    # Compétences
    if data.get('skills'):
        skills_node = etree.SubElement(monster, "skills")
        for s in data['skills']:
            skill_item = etree.SubElement(skills_node, "skill")
            etree.SubElement(skill_item, "name").text = s['name']
            etree.SubElement(skill_item, "bonus").text = str(s['bonus'])

    # Attributs
    if data.get('attributes'):
        attr_node = etree.SubElement(monster, "attributes")
        for attr_key in ['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA']:
            val = data['attributes'].get(attr_key, "+0")
            attr_node.set(attr_key, val)

    add_abilities_to_xml(monster, data['interaction_abilities'], "interactionAbilities")

    # Défenses
    etree.SubElement(monster, "armorClass").text = data.get('ac')
    save_node = etree.SubElement(monster, "saves", **data.get('saves', {}))
    if 'save_special' in data: 
        save_node.set("saveSpecial", data['save_special'])
    etree.SubElement(monster, "health").text = data.get('hp')

    if data.get('immunities'):
        imm_node = etree.SubElement(monster, "immunities")
        for imm in data['immunities']:
            etree.SubElement(imm_node, "immunity").text = imm

    if data.get('weaknesses'):
        weak_node = etree.SubElement(monster, "weaknesses")
        for w in data['weaknesses']:
            w_elem = etree.SubElement(weak_node, "weakness")
            etree.SubElement(w_elem, "name").text = w['name']
            etree.SubElement(w_elem, "value").text = w['value']

    add_abilities_to_xml(monster, data['reactive_abilities'], "reactiveAbilities")

    # Vitesses
    if data.get('speeds') and data['speeds']['list']:
        speeds_node = etree.SubElement(monster, "speeds")
        if data['speeds'].get('special'):
            speeds_node.set("speedSpecial", data['speeds']['special'])
            
        for s in data['speeds']['list']:
            speed_elem = etree.SubElement(speeds_node, "speed")
            speed_elem.text = s['value']
            if s['type']:
                speed_elem.set("type", s['type'])
    else:
        speeds_node = etree.SubElement(monster, "speeds")
        etree.SubElement(speeds_node, "speed").text = "0 m"

    # Frappes
    strikes_node = etree.SubElement(monster, "strikes")
    for strike in data.get('strikes', []):
        strike_elem = etree.SubElement(strikes_node, "strike")
        if strike.get('type'):
            strike_elem.set("type", strike['type'])
            
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
            
    # Sorts
    if data.get('spells'):
        s = data['spells']
        s_list = etree.SubElement(monster, "spellList", source=s['source'], tradition=s['tradition'], DD=s['DD'])
        if s['attack']: 
            s_list.set("attack", s['attack'])
        for r in s['ranks']:
            r_node = etree.SubElement(s_list, "rank", rank=r['rank'])
            if r.get('constant'): r_node.set("constant", "TRUE")
            if r.get('cantrips'): r_node.set("cantrips", "TRUE")
            spells_node = etree.SubElement(r_node, "spells")
            for sp_name in r['spells']:
                spell_elem = etree.SubElement(spells_node, "spell")
                spell_elem.text = sp_name
                if r.get('special'):
                    spell_elem.set("spellSpecial", r['special'])

    add_abilities_to_xml(monster, data['offensive_abilities'], "offensiveAbilities")

    # Finalisation et Sauvegarde
    tree = etree.ElementTree(root)
    pi = etree.ProcessingInstruction("xml-stylesheet", 'href="../../xslt/decodeMonster.xsl" type="text/xsl"')
    root.addprevious(pi)
    tree.write(output_path, encoding="UTF-8", xml_declaration=True, pretty_print=True)
    
    total_time = time.time() - start_time
    print(f"[XML] ✓ Génération complète en {total_time:.3f}s\n")

# ==========================================
# EXÉCUTION PRINCIPALE
# ==========================================

if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else "./output/subset_3/monstre_unique.md"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "./output/subset_3/young_empyreal_dragon.xml"

    print("="*60)
    print("DÉBUT DU TRAITEMENT (MONSTER MAPPER)")
    print("="*60 + "\n")

    start_total = time.time()

    if os.path.exists(input_file):
        print(f"[MAIN] Lecture du fichier {input_file}...")
        with open(input_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
        print(f"[MAIN] ✓ Fichier chargé ({len(md_content)} caractères)\n")
        
        monster_data = parse_monster_md(md_content)

        output_dir = "./data/monsters"
        output_file = os.path.join(output_dir, monster_data['name']+".xml") if monster_data['name'] else output_file
        
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