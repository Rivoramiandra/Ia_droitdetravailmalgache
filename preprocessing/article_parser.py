"""
article_parser.py
-----------------

Transformation du Code du Travail nettoyé
en articles juridiques structurés.

Pipeline :

pages.json
    |
clean_text.py
    |
texte propre
    |
article_parser.py
    |
articles.json
    |
splitter.py
    |
embeddings
    |
FAISS
    |
RAG


Structure sortie :

{
"id":"art_001",

"article_num":1,

"metadata":{
    "titre":"",
    "chapitre":"",
    "section":""
},

"content":"texte article",

"full_context":"titre chapitre section article"
}
"""


import json
import re
import sys

from pathlib import Path



# =====================================================
# REGEX JURIDIQUES
# =====================================================


TITRE_RE = re.compile(
    r"^TITRE\s+(.+)$",
    re.IGNORECASE
)


CHAPITRE_RE = re.compile(
    r"^CHAPITRE\s+(.+)$",
    re.IGNORECASE
)


SECTION_RE = re.compile(
    r"^(Section|Sous-section)\s+(.+)$",
    re.IGNORECASE
)


PARAGRAPHE_RE = re.compile(
    r"^§\s*(.+)$"
)



ARTICLE_RE = re.compile(
    r"^Article\s+(premier|\d+)\s*(?:er)?[\s.\-–]*(.*)$",
    re.IGNORECASE
)



COLON_ONLY_RE = re.compile(
    r":\s*$"
)



# =====================================================
# UTILITAIRES
# =====================================================


def normalize_text(text:str)->str:
    """
    Nettoyage léger après parsing.
    """

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()



def article_number_to_int(value:str)->int:

    if value.lower().startswith("premier"):
        return 1

    return int(value)




def is_header(line:str)->bool:

    return bool(
        ARTICLE_RE.match(line)
        or TITRE_RE.match(line)
        or CHAPITRE_RE.match(line)
        or SECTION_RE.match(line)
        or PARAGRAPHE_RE.match(line)
    )



def is_upper_label(line:str)->bool:

    chars=[
        c for c in line
        if c.isalpha()
    ]

    return (
        len(chars)>0
        and all(
            c.isupper()
            for c in chars
        )
    )



# =====================================================
# GESTION TITRE / CHAPITRE
# =====================================================


def extract_header(
        line,
        lines,
        index
):

    label=line

    consumed=0


    if (
        COLON_ONLY_RE.search(line)
        and index+1<len(lines)
    ):

        nxt=lines[index+1]


        if not is_header(nxt):

            label += " "+nxt

            consumed=1


    return label.strip(), consumed




# =====================================================
# PARSER PRINCIPAL
# =====================================================


def parse_articles(lines:list[str])->list[dict]:


    articles=[]


    current_titre=None
    current_chapitre=None
    current_section=None


    current_article=None

    body=[]



    def save_current():

        nonlocal current_article


        if current_article:


            content=normalize_text(
                " ".join(body)
            )


            current_article["content"]=content


            meta=current_article["metadata"]


            context=[]


            for value in [
                meta["titre"],
                meta["chapitre"],
                meta["section"],
                f"Article {current_article['article_num']}"
            ]:

                if value:
                    context.append(value)



            current_article["full_context"] = (
                " | ".join(context)
                +" | "
                +content[:500]
            )



            articles.append(
                current_article
            )





    i=0


    while i<len(lines):


        line=lines[i].strip()


        if not line:

            i+=1
            continue



        # -------------------
        # TITRE
        # -------------------

        titre=TITRE_RE.match(line)


        if titre:

            save_current()

            current_article=None
            body=[]


            label,extra=extract_header(
                line,
                lines,
                i
            )


            current_titre=label

            current_chapitre=None
            current_section=None


            i+=1+extra

            continue



        # -------------------
        # CHAPITRE
        # -------------------

        chapitre=CHAPITRE_RE.match(line)


        if chapitre:


            save_current()


            current_article=None
            body=[]


            label,extra=extract_header(
                line,
                lines,
                i
            )


            current_chapitre=label

            current_section=None


            i+=1+extra

            continue



        # -------------------
        # SECTION
        # -------------------

        section=SECTION_RE.match(line)


        if section:


            save_current()


            current_article=None
            body=[]


            label,extra=extract_header(
                line,
                lines,
                i
            )


            current_section=label


            i+=1+extra

            continue



        # -------------------
        # ARTICLE
        # -------------------

        article=ARTICLE_RE.match(line)


        if article:


            save_current()


            num=article_number_to_int(
                article.group(1)
            )


            current_article={


                "id":
                f"art_{num:03d}",


                "article_num":
                num,


                "metadata":{


                    "titre":
                    current_titre,


                    "chapitre":
                    current_chapitre,


                    "section":
                    current_section
                },


                "content":"",

                "full_context":""

            }



            first_text=article.group(2)


            body=[]


            if first_text:

                body.append(first_text)



            i+=1

            continue



        # contenu article

        if current_article:

            body.append(line)


        i+=1



    save_current()


    return articles



# =====================================================
# SAUVEGARDE
# =====================================================


def save_articles(
        articles,
        output
):

    Path(output).parent.mkdir(
        parents=True,
        exist_ok=True
    )


    with open(
        output,
        "w",
        encoding="utf-8"
    ) as f:


        json.dump(
            articles,
            f,
            ensure_ascii=False,
            indent=2
        )



# =====================================================
# EXECUTION
# =====================================================


if __name__=="__main__":


    input_file = (
        sys.argv[1]
        if len(sys.argv)>1
        else
        "data/processed/raw_text.txt"
    )


    output_file = (
        sys.argv[2]
        if len(sys.argv)>2
        else
        "data/processed/articles.json"
    )



    lines=Path(
        input_file
    ).read_text(
        encoding="utf-8"
    ).splitlines()



    articles=parse_articles(
        lines
    )


    save_articles(
        articles,
        output_file
    )



    nums=[
        a["article_num"]
        for a in articles
    ]


    print("="*50)

    print(
        f"{len(articles)} articles extraits"
    )


    print(
        f"Fichier : {output_file}"
    )



    if nums:


        print(
            f"Articles {min(nums)} -> {max(nums)}"
        )


        missing=set(
            range(
                1,
                max(nums)+1
            )
        )-set(nums)



        if missing:

            print(
                "⚠️ Articles manquants :",
                sorted(missing)
            )

        else:

            print(
                "✅ Séquence complète"
            )


    print("="*50)