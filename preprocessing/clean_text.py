"""
clean_text.py
--------------

Etape du pipeline LegalAI :
Nettoyage du texte brut extrait du PDF.

Objectif :
Transformer un texte PDF bruité en texte propre
pour le parsing des articles juridiques.

Pipeline :

PDF
 |
pdf_loader.py
 |
pages.json
 |
clean_text.py
 |
texte nettoyé
 |
article_parser.py
"""


import re


# ============================================================
# REGEX
# ============================================================


# Numéro de page seul :
# Exemple :
# 12
# 45
PAGE_NUMBER_RE = re.compile(
    r"^\s*\d{1,4}\s*$"
)


# Correction des mots coupés par le PDF :
#
# améliora-
# tion
#
# devient :
#
# amélioration

HYPHEN_WRAP_RE = re.compile(
    r"([a-zàâçéèêëîïôûùüÿñæœ])-\n([a-zàâçéèêëîïôûùüÿñæœ])",
    re.IGNORECASE
)



# Espaces multiples

MULTIPLE_SPACE_RE = re.compile(
    r"[ \t]+"
)



# Plusieurs lignes vides

MULTIPLE_NEWLINES_RE = re.compile(
    r"\n{3,}"
)



# Espaces avant ponctuation française

SPACE_BEFORE_PUNCT_RE = re.compile(
    r"\s+([,.;:!?])"
)



# Caractères invisibles PDF

INVISIBLE_CHAR_RE = re.compile(
    r"[\u200b\u200c\u200d\ufeff]"
)



# ============================================================
# NETTOYAGES ELEMENTAIRES
# ============================================================


def remove_invisible_characters(text: str) -> str:
    """
    Supprime les caractères invisibles ajoutés par les PDF.
    """
    return INVISIBLE_CHAR_RE.sub("", text)



def strip_page_number(text: str) -> str:
    """
    Supprime les lignes qui contiennent uniquement
    un numéro de page.
    """

    lines = text.split("\n")

    cleaned = []

    for line in lines:

        if PAGE_NUMBER_RE.match(line):
            continue

        cleaned.append(line)


    return "\n".join(cleaned)



def dehyphenate(text: str) -> str:
    """
    Recollage des mots coupés par les retours
    à la ligne du PDF.

    Exemple :

    obliga-
    tion

    devient :

    obligation
    """

    return HYPHEN_WRAP_RE.sub(
        r"\1\2",
        text
    )



def normalize_spaces(line: str) -> str:
    """
    Normalise les espaces dans une ligne.
    """

    line = line.replace(
        "\xa0",
        " "
    )

    line = MULTIPLE_SPACE_RE.sub(
        " ",
        line
    )

    return line.strip()



def fix_french_punctuation(text: str) -> str:
    """
    Corrige les espaces avant ponctuation.

    Exemple :

    Article 5 :

    devient :

    Article 5:
    """

    return SPACE_BEFORE_PUNCT_RE.sub(
        r"\1",
        text
    )



def collapse_blank_lines(text: str) -> str:
    """
    Réduit les lignes vides multiples.
    """

    return MULTIPLE_NEWLINES_RE.sub(
        "\n\n",
        text
    )



# ============================================================
# DETECTION STRUCTURE JURIDIQUE
# ============================================================


def is_structure_line(line: str) -> bool:
    """
    Détecte les lignes importantes du Code du travail.

    On évite de supprimer leur séparation.
    """

    patterns = [

        r"^TITRE",
        r"^CHAPITRE",
        r"^Section",
        r"^Sous-section",
        r"^Article"

    ]


    return any(
        re.match(pattern, line, re.IGNORECASE)
        for pattern in patterns
    )



# ============================================================
# PIPELINE PRINCIPAL
# ============================================================


def clean_page_text(page_text: str) -> str:
    """
    Nettoyage complet d'une page PDF.
    """

    if not page_text:
        return ""



    # 1 - caractères invisibles

    text = remove_invisible_characters(
        page_text
    )



    # 2 - suppression pagination

    text = strip_page_number(
        text
    )



    # 3 - correction mots coupés

    text = dehyphenate(
        text
    )



    # 4 - nettoyage ligne par ligne

    lines = []

    for line in text.split("\n"):

        cleaned = normalize_spaces(
            line
        )


        if cleaned:
            lines.append(cleaned)



    text = "\n".join(lines)



    # 5 - correction ponctuation

    text = fix_french_punctuation(
        text
    )



    # 6 - réduction lignes vides

    text = collapse_blank_lines(
        text
    )


    return text.strip()



# ============================================================
# TEST LOCAL
# ============================================================


if __name__ == "__main__":


    test = """

    Article 1 -

    Le contrat de tra-
    vail est conclu.


    12

    """

    print(
        clean_page_text(test)
    )