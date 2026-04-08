#!/usr/bin/env python3
"""
compare_pipeline_loss.py

Compares raw PDF extraction (source) vs Obsidian output (output) to detect
text silently dropped during the pipeline.

Strategy: extract individual spell blocks from both files, then compare
content words per spell to find text lost in the pipeline.
"""

import re
import unicodedata
from collections import defaultdict
from pathlib import Path

# ── Configuration ────────────────────────────────────────────────────────────

SOURCE_FILE = Path("output/batch_01_extract/PF2R_01_Livre_des_Joueurs_web_v1.md")
OUTPUT_FILE = Path("obsidian_vault/preview/sorts_batch_01.md")
BASE = Path("/Users/slither/Documents/dev/repositories/pf2_data_Claude")

# Words to exclude from comparison (mechanical/structural/stopwords)
NOISE = {
    # Very common French
    "le", "la", "les", "un", "une", "des", "de", "du", "et", "ou", "a", "en",
    "par", "pour", "sur", "dans", "avec", "qui", "que", "qu", "se", "sa",
    "son", "ses", "ce", "cet", "cette", "ces", "ne", "pas", "plus", "tout",
    "toute", "tous", "toutes", "il", "elle", "ils", "elles", "vous", "nous",
    "on", "je", "si", "mais", "donc", "or", "ni", "car", "est", "sont",
    "etre", "avoir", "aux", "au", "y", "dont", "tu", "me", "te", "lui",
    "leur", "leurs", "meme", "aussi", "bien", "tres", "lors", "apres",
    "avant", "comme", "entre", "vers", "jusqu", "afin", "lorsque", "lorsqu",
    "cela", "celle", "ceux", "celles", "peut", "sont", "sera", "serait",
    "doit", "font", "fait", "faire", "dun", "une", "cas",
    # Spell mechanics labels
    "tradition", "traditions", "portee", "cible", "cibles", "defense",
    "duree", "zone", "incantation", "declencheur", "intensifie", "intensifies",
    "succes", "echec", "sort", "sorts", "focalise", "tour", "magie",
    "arcanique", "divine", "occulte", "primordiale", "concentration",
    "manipulation", "audible", "discret", "emotion", "mental", "guerison",
    "vitalite", "air", "feu", "terre", "eau", "bois", "lumiere", "tenebres",
    "tromperie", "illusion", "fortune", "prediction", "mort", "necromancie",
    "transmutation", "evocation", "abjuration", "divination", "invocation",
    "enchantement", "action", "actions", "reaction", "libre", "niveau",
    "rang", "rituel", "rituels", "composante", "composantes",
    "critique", "critiques", "deux", "trois", "une", "deux", "dix",
    # Structural markers
    "page", "table", "flux", "principal", "encarts", "detectes", "lore",
    "annexes", "metadata", "start", "end", "header", "row", "tablerow",
    # Navigation / book meta
    "introduction", "ascendances", "historiques", "classes", "competences",
    "dons", "equipement", "regles", "listes", "barde", "druide", "magicien",
    "pretre", "rodeur", "sorcier", "annexe", "etats", "feuille",
    "personnage", "glossaire", "index", "jouer", "partie",
    "joueurs", "livre", "christophe", "cavalier", "pont", "gmail", "com",
    # Abbreviations
    "cf", "ex", "nb", "etc", "vs", "base", "pnj", "pnjs", "pj", "pjs",
}

RATIO_THRESHOLD = 2.0
MIN_SRC_COUNT = 2


# ── Normalization ─────────────────────────────────────────────────────────────

def normalize(word: str) -> str:
    """Lowercase, strip accents, keep only letters."""
    word = word.lower()
    word = unicodedata.normalize("NFKD", word)
    word = "".join(c for c in word if not unicodedata.combining(c))
    word = re.sub(r"[^a-z]", "", word)
    return word


def tokenize(text: str) -> list[str]:
    """Split into content words, normalized."""
    raw = re.split(r"[^\w''àâäéèêëîïôùûüçœæ]+", text, flags=re.UNICODE)
    result = []
    for t in raw:
        t = t.strip("''")
        n = normalize(t)
        if len(n) <= 2:
            continue
        if re.fullmatch(r"\d+", n):
            continue
        if n in NOISE:
            continue
        result.append(n)
    return result


def word_freq(text: str) -> dict[str, int]:
    freq: dict[str, int] = defaultdict(int)
    for w in tokenize(text):
        freq[w] += 1
    return freq


# ── Spell extraction from source ──────────────────────────────────────────────

# Source pattern: **SPELL NAME** N ** SORT N
SRC_SPELL_HEADER = re.compile(
    r"\*\*([A-ZÀÂÄÉÈÊËÎÏÔÙÛÜÇ][A-ZÀÂÄÉÈÊËÎÏÔÙÛÜÇ\s\-']+)\*\*\s+\d+\s*\*\*\s+SORT"
)

def extract_src_spells(text: str) -> dict[str, str]:
    """Extract {spell_name: full_text} from source markdown."""
    # Split into pages first (dedup across repeated pages)
    # Find all spell start positions
    positions = [(m.start(), m.group(1).strip()) for m in SRC_SPELL_HEADER.finditer(text)]
    if not positions:
        return {}

    spells = {}
    for i, (start, name) in enumerate(positions):
        end = positions[i + 1][0] if i + 1 < len(positions) else len(text)
        block = text[start:end]
        # Deduplicate: if same name appears, merge (take longest)
        if name not in spells or len(block) > len(spells[name]):
            spells[name] = block
    return spells


# ── Spell extraction from output ──────────────────────────────────────────────

# Output pattern: # SPELL NAME `[actions]`
OUT_SPELL_HEADER = re.compile(r"^# ([A-ZÀÂÄÉÈÊËÎÏÔÙÛÜÇ][A-ZÀÂÄÉÈÊËÎÏÔÙÛÜÇ\s\-']+)", re.MULTILINE)

def extract_out_spells(text: str) -> dict[str, str]:
    """Extract {spell_name: full_text} from output markdown."""
    positions = [(m.start(), m.group(1).strip()) for m in OUT_SPELL_HEADER.finditer(text)]
    if not positions:
        return {}
    spells = {}
    for i, (start, name) in enumerate(positions):
        end = positions[i + 1][0] if i + 1 < len(positions) else len(text)
        spells[name] = text[start:end]
    return spells


# ── Find example line ─────────────────────────────────────────────────────────

def find_example(word: str, text: str, max_len: int = 120) -> str:
    for line in text.splitlines():
        if word in tokenize(line):
            return line.strip()[:max_len]
    return "(introuvable)"


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    src_text = (BASE / SOURCE_FILE).read_text(encoding="utf-8")
    out_text = (BASE / OUTPUT_FILE).read_text(encoding="utf-8")

    print(f"Source : {len(src_text.splitlines())} lignes")
    print(f"Output : {len(out_text.splitlines())} lignes")
    print()

    src_spells = extract_src_spells(src_text)
    out_spells = extract_out_spells(out_text)

    common = sorted(set(src_spells) & set(out_spells))
    only_src = sorted(set(src_spells) - set(out_spells))
    only_out = sorted(set(out_spells) - set(src_spells))

    print(f"Sorts en commun (source & output) : {len(common)}")
    print(f"Sorts dans source mais PAS dans output : {len(only_src)}")
    print(f"Sorts dans output mais PAS dans source : {len(only_out)}")
    print()

    if only_src:
        print("SORTS ABSENTS DE L'OUTPUT :")
        for s in only_src:
            print(f"  - {s}")
        print()

    # ── Per-spell word diff ───────────────────────────────────────────────────
    print("=" * 80)
    print("ANALYSE MOT-PAR-MOT PAR SORT : TEXTE PERDU DANS LE PIPELINE")
    print("=" * 80)
    print()

    grand_total_lost: dict[str, list[str]] = defaultdict(list)  # word → [spell names]

    for spell_name in common:
        src_block = src_spells[spell_name]
        out_block = out_spells[spell_name]

        src_freq = word_freq(src_block)
        out_freq = word_freq(out_block)

        src_words = set(src_freq)
        out_words = set(out_freq)

        # Words completely absent from output
        absent = {w for w in src_words if w not in out_words and src_freq[w] >= MIN_SRC_COUNT}

        # Words much more frequent in source
        underrep = {
            w for w in src_words
            if w in out_words
            and src_freq[w] >= MIN_SRC_COUNT
            and src_freq[w] / max(out_freq[w], 1) >= RATIO_THRESHOLD
            and src_freq[w] - out_freq[w] >= 2
        }

        lost = absent | underrep
        if not lost:
            continue

        print(f"  ── {spell_name} ──")
        for word in sorted(lost, key=lambda w: -src_freq[w]):
            src_c = src_freq[word]
            out_c = out_freq.get(word, 0)
            status = "ABSENT" if word in absent else f"sous-représenté ({src_c}→{out_c})"
            example = find_example(word, src_block)
            print(f"    [{word}]  src={src_c} out={out_c}  ({status})")
            print(f"      └─ {example}")
            grand_total_lost[word].append(spell_name)
        print()

    # ── Summary across all spells ─────────────────────────────────────────────
    print()
    print("=" * 80)
    print("RÉCAPITULATIF : MOTS LES PLUS SOUVENT PERDUS (toutes sortes)")
    print("=" * 80)
    print()

    if not grand_total_lost:
        print("  Aucune perte détectée sur les sorts en commun. Pipeline propre.")
        return

    sorted_summary = sorted(grand_total_lost.items(), key=lambda x: -len(x[1]))
    for word, spells in sorted_summary[:50]:
        print(f"  [{word}]  perdu dans {len(spells)} sort(s) : {', '.join(spells[:5])}")


if __name__ == "__main__":
    main()
