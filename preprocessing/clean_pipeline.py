import json
import re
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "processed" / "pages.json"

OUTPUT_FILE = BASE_DIR / "data" / "processed" / "raw_text.txt"



# ============================================================
# REGEX
# ============================================================


# Numéro de page seul
# Exemple:
# 1
# 25
PAGE_NUMBER_RE = re.compile(
    r"^\s*\d{1,4}\s*$"
)



# Coupure PDF
# Exemple:
# travail-
# leur
#
# devient:
# travailleur

HYPHEN_WRAP_RE = re.compile(
    r"([a-zàâçéèêëîïôûùüÿñæœ])-\n([a-zàâçéèêëîïôûùüÿñæœ])"
)



# Plusieurs espaces
MULTI_SPACE_RE = re.compile(
    r"[ \t]+"
)



# Plusieurs lignes vides
MULTI_EMPTY_LINE_RE = re.compile(
    r"\n{3,}"
)



# ============================================================
# NETTOYAGE
# ============================================================


def remove_page_numbers(text: str) -> str:
    """
    Supprime les numéros de pages seuls.
    Exemple:
        Article 1...
        5
        Article 2...
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
    Recolle les mots coupés par le PDF.
    
    Exemple:
        main-
        d'œuvre
        
    devient:
        main-d'œuvre
    """

    return HYPHEN_WRAP_RE.sub(
        r"\1\2",
        text
    )



def normalize_line(line: str) -> str:
    """
    Nettoyage d'une ligne.
    """

    # espace insécable PDF
    line = line.replace(
        "\xa0",
        " "
    )


    # espaces multiples
    line = MULTI_SPACE_RE.sub(
        " ",
        line
    )


    return line.strip()



def clean_page_text(text: str) -> str:
    """
    Pipeline complet sur une page.
    """

    # supprimer pagination
    text = remove_page_numbers(text)


    # correction mots coupés
    text = dehyphenate(text)


    # nettoyage lignes
    lines = []

    for line in text.split("\n"):

        clean = normalize_line(line)

        if clean:
            lines.append(clean)



    text = "\n".join(lines)


    # réduire espaces verticaux
    text = MULTI_EMPTY_LINE_RE.sub(
        "\n\n",
        text
    )


    return text



# ============================================================
# MAIN
# ============================================================


def main():

    print("="*60)
    print("Nettoyage du texte PDF LegalAI")
    print("="*60)



    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"Fichier introuvable : {INPUT_FILE}"
        )



    print("Lecture :", INPUT_FILE)



    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        pages = json.load(f)



    print(
        "Nombre de pages :",
        len(pages)
    )



    all_pages = []



    for index,page in enumerate(pages,1):

        cleaned = clean_page_text(
            page["text"]
        )


        all_pages.append(cleaned)



    final_text = "\n\n".join(
        all_pages
    )



    OUTPUT_FILE.parent.mkdir(
        exist_ok=True
    )



    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(final_text)



    print()
    print("✅ Nettoyage terminé")
    print(
        "Pages traitées :",
        len(pages)
    )

    print(
        "Fichier généré :",
        OUTPUT_FILE
    )

    print("="*60)



if __name__ == "__main__":
    main()