from lxml import etree

# ==========================================
# VALIDATION XSD
# ==========================================

def validate_xml(xml_path, xsd_path, silent=False):
    """Vérifie si le fichier XML est valide par rapport au schéma XSD.

    Si silent=True, supprime toute sortie console (utile pour le traitement en lot).
    """
    if not silent:
        print(f"[VALIDATION] Vérification de {xml_path} avec {xsd_path}...")
    try:
        with open(xsd_path, 'rb') as f:
            schema_root = etree.XML(f.read())
        schema = etree.XMLSchema(schema_root)

        with open(xml_path, 'rb') as f:
            xml_doc = etree.parse(f)

        if not schema.validate(xml_doc):
            if not silent:
                print("[VALIDATION] ✗ Le fichier XML est INVALIDE !")
                for error in schema.error_log:
                    print(f"    - Ligne {error.line}, colonne {error.column}: {error.message}")
            return False

        # Assertions XSD 1.1 (lxml ne les vérifie pas, on les applique ici)
        assertion_errors = []
        root = xml_doc.getroot()
        if root.tag == 'spells':
            for spell in root.findall('spell'):
                spell_type = spell.get('type')
                name = spell.findtext('name', '?')
                traditions = spell.findall('traditions/tradition')
                if spell_type == 'spell' and len(traditions) == 0:
                    assertion_errors.append(
                        f"Sort '{name}' (type=spell) n'a aucune tradition (obligatoire)"
                    )
                if spell_type == 'focus' and len(traditions) > 0:
                    assertion_errors.append(
                        f"Sort '{name}' (type=focus) ne devrait pas avoir de traditions"
                    )

        if assertion_errors:
            if not silent:
                print("[VALIDATION] ✗ Violations des contraintes de gestion (XSD 1.1 assert) :")
                for err in assertion_errors:
                    print(f"    - {err}")
            return False

        if not silent:
            print("[VALIDATION] ✓ Le fichier XML est VALIDE.")
        return True
    except Exception as e:
        if not silent:
            print(f"[VALIDATION] Erreur lors de la validation : {e}")
        return False