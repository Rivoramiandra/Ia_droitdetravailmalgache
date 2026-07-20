"""
splitter.py
-----------

Etape RAG :
Transformation des articles juridiques
en petits chunks pour embeddings.

Entrée:
articles.json

Sortie:
chunks.json


Compatible :
- Sentence Transformers
- FAISS
- LangChain
"""


import json
import re
import sys

from pathlib import Path



# ======================================================
# CONFIGURATION
# ======================================================


MAX_CHARS = 900

OVERLAP_CHARS = 150



# Découpage sous articles

LIST_ITEM_RE = re.compile(
    r"(?=\s\d{1,2}(?:\.\d+)?\.\s)"
)



# phrases

SENTENCE_RE = re.compile(
    r"(?<=[.;!?])\s+"
)



# paragraphes

PARAGRAPH_RE = re.compile(
    r"\n+"
)



# ======================================================
# CONTEXTE JURIDIQUE
# ======================================================


def make_header(article):

    metadata = article.get(
        "metadata",
        {}
    )


    parts=[]


    for key in [
        "titre",
        "chapitre",
        "section"
    ]:

        value=metadata.get(key)

        if value:
            parts.append(value)



    article_num = article["article_num"]


    label = (
        "Article premier"
        if article_num == 1
        else
        f"Article {article_num}"
    )



    context=" > ".join(parts)


    if context:

        return (
            f"{context} > {label}"
        )


    return label





# ======================================================
# SPLIT INTELLIGENT
# ======================================================


def split_text(
        text,
        max_chars=MAX_CHARS,
        overlap=OVERLAP_CHARS
):


    if len(text)<=max_chars:

        return [text]



    # Niveau 1 :
    # paragraphes


    pieces=[
        p.strip()
        for p in PARAGRAPH_RE.split(text)
        if p.strip()
    ]



    # Niveau 2 :
    # sous points


    if len(pieces)==1:


        pieces=[
            p.strip()
            for p in LIST_ITEM_RE.split(text)
            if p.strip()
        ]



    # Niveau 3 :
    # phrases


    if len(pieces)==1:


        pieces=[
            p.strip()
            for p in SENTENCE_RE.split(text)
            if p.strip()
        ]



    chunks=[]

    current=""



    for piece in pieces:


        candidate=(
            current+" "+piece
        ).strip()



        if len(candidate)<=max_chars:


            current=candidate



        else:


            if current:

                chunks.append(
                    current
                )



                overlap_text=current[
                    -overlap:
                ]

                current=(
                    overlap_text
                    +" "
                    +piece
                ).strip()



            else:


                current=piece



    if current:

        chunks.append(
            current
        )



    return chunks





# ======================================================
# CREATION DES CHUNKS
# ======================================================


def build_chunks(
        articles
):


    chunks=[]



    for article in articles:


        header=make_header(
            article
        )


        # compatible nouveau parser

        text=article.get(
            "content",
            article.get("text","")
        )



        segments=split_text(
            text
        )



        for index,segment in enumerate(segments):


            chunk_id=(

                f"{article['id']}"
                if len(segments)==1

                else

                f"{article['id']}_chunk_{index+1}"

            )



            page_content=(

                header
                +
                "\n\n"
                +
                segment

            )



            chunks.append({

                "chunk_id":
                chunk_id,


                "page_content":
                page_content,


                "metadata":{


                    "article_id":
                    article["id"],


                    "article_num":
                    article["article_num"],


                    "titre":
                    article.get(
                        "metadata",
                        {}
                    ).get(
                        "titre"
                    ),


                    "chapitre":
                    article.get(
                        "metadata",
                        {}
                    ).get(
                        "chapitre"
                    ),


                    "section":
                    article.get(
                        "metadata",
                        {}
                    ).get(
                        "section"
                    ),


                    "chunk_index":
                    index+1,


                    "total_chunks":
                    len(segments)

                }

            })


    return chunks





# ======================================================
# SAUVEGARDE
# ======================================================


def save_chunks(
        chunks,
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
            chunks,
            f,
            ensure_ascii=False,
            indent=2
        )





# ======================================================
# EXECUTION
# ======================================================


if __name__=="__main__":


    input_file=(

        sys.argv[1]
        if len(sys.argv)>1

        else

        "data/processed/articles.json"

    )


    output_file=(

        sys.argv[2]
        if len(sys.argv)>2

        else

        "data/processed/chunks.json"

    )



    articles=json.loads(

        Path(input_file)
        .read_text(
            encoding="utf-8"
        )

    )



    chunks=build_chunks(
        articles
    )



    save_chunks(
        chunks,
        output_file
    )



    sizes=[
        len(c["page_content"])
        for c in chunks
    ]



    print("="*50)

    print(
        f"{len(articles)} articles"
    )

    print(
        f"{len(chunks)} chunks créés"
    )


    print(
        f"Taille min : {min(sizes)}"
    )

    print(
        f"Taille max : {max(sizes)}"
    )


    print(
        f"Fichier : {output_file}"
    )

    print("="*50)