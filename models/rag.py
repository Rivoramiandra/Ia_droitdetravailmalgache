import os
import re
import pickle
import string
import unicodedata
import logging
import time
from difflib import get_close_matches

import faiss
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer, CrossEncoder
from groq import Groq, RateLimitError, APIError, APIConnectionError

# Configuration des logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("RAG FILE =", __file__)

# ==============================
# CONFIGURATION
# ==============================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY manquant. Vérifiez votre fichier .env "
        "(GROQ_API_KEY=votre_cle_ici)."
    )

client = Groq(api_key=GROQ_API_KEY)

MODEL_EMBEDDING = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
# Reranker multilingue (le ms-marco classique est entraîné en anglais uniquement,
# on utilise donc une variante multilingue adaptée au français)
MODEL_RERANKER = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"

INDEX_PATH = "models/index.faiss"
CHUNKS_PATH = "models/chunks.pkl"

# Modèle principal + modèle de secours
# Le 70B n'est pas nécessaire ici : FAISS fait le travail de mémoire juridique,
# le LLM ne fait que reformuler à partir du contexte -> un modèle léger suffit
# et consomme beaucoup moins de quota.
PRIMARY_MODEL = "llama-3.1-8b-instant"
FALLBACK_MODEL = "llama-3.3-70b-versatile"

MAX_RETRIES = 2
RETRY_DELAY_SECONDS = 3
DEFAULT_MAX_TOKENS = 800  # 1500 était surdimensionné pour des réponses de 400-700 tokens

# ==============================
# SEUILS FAISS
# ==============================

# Nombre de candidats récupérés par FAISS avant reranking
# (30 en base, jusqu'à 40 pour les questions larges/générales)
FAISS_TOP_K_CANDIDATES = 30
FAISS_TOP_K_WIDE = 40
# Nombre de chunks finaux gardés après reranking
RERANK_TOP_N = 8
RERANK_TOP_N_WIDE = 10

FAISS_MAX_DISTANCE = float(os.getenv("FAISS_MAX_DISTANCE", "1.2"))
# Relevé de 0.3 -> 0.45 : le seuil précédent était trop permissif et laissait
# passer des articles peu pertinents (ex: "droits du salarié" -> article sur
# le service médical du travail)
FAISS_MIN_SIMILARITY = float(os.getenv("FAISS_MIN_SIMILARITY", "0.45"))
# En dessous de ce score, on prévient l'utilisateur que la correspondance est faible
LOW_CONFIDENCE_THRESHOLD = float(os.getenv("LOW_CONFIDENCE_THRESHOLD", "0.55"))

# Paramètres de correction orthographique
MIN_WORD_LEN_FOR_CORRECTION = 4
SPELLING_CUTOFF = 0.85

# Mots français courants à ne jamais corriger
COMMON_FRENCH_WORDS = {
    "combien", "comment", "pourquoi", "quand", "lequel", "laquelle",
    "lesquels", "lesquelles", "quelle", "quelles", "quel", "quels",
    "avant", "apres", "pendant", "depuis", "jusqu", "jusque",
    "dure", "dur", "duree", "durée",
    "parle", "parles", "parlent", "parler",
    "toujours", "jamais", "encore", "aussi", "ainsi", "alors",
    "donc", "cependant", "pourtant", "malgre", "beaucoup",
    "plusieurs", "certains", "certaines", "chaque", "quelque",
    "quelques", "vraiment", "exactement", "actuellement",
    "normalement", "legalement", "personnellement", "egalement",
    "seulement", "simplement", "rapidement", "recemment",
    "maintenant", "aujourd", "hier", "demain", "bonjour", "bonsoir",
    "merci", "svp", "possible", "impossible", "obligatoire",
    "facultatif", "gratuit", "payant",
    "quels", "quelles", "quel", "quelle", "comment", "pourquoi",
    "quand", "ou", "où", "que", "quoi", "qui", "dont",
}

# ==============================
# DICTIONNAIRE DE SYNONYMES JURIDIQUES
# ==============================

SYNONYMS = {
    "licenciement": [
        "renvoi", "renvoyer", "virer", "viré", "mise à pied",
        "rupture du contrat", "fin de contrat", "congédiement",
        "révocation", "mettre dehors", "mettre à la porte",
    ],
    "démission": [
        "quitter le travail", "démissionner", "abandon de poste",
        "quitter mon emploi", "quitter mon travail", "partir de mon travail",
    ],
    "salaire": [
        "paie", "paye", "rémunération", "solde", "traitement",
        "salaire minimum", "smig", "argent du travail",
    ],
    "congé": [
        "conges", "congé", "congés", "congé payé", "congés payés",
        "repos annuel", "jours de repos", "jours libres", "vacances",
        "permission", "absence autorisée", "absence",
    ],
    "congé de maladie": [
        "arrêt maladie", "congé maladie", "malade", "certificat médical",
    ],
    "congé de maternité": [
        "maternité", "grossesse", "accouchement",
    ],
    "heures supplémentaires": [
        "heure sup", "heures sup", "travail supplémentaire", "heures en plus",
    ],
    "contrat de travail": [
        "contrat", "cdd", "cdi", "engagement",
    ],
    "période d'essai": [
        "essai", "essai professionnel",
    ],
    "préavis": [
        "délai de préavis", "délai congé",
    ],
    "indemnité": [
        "indemnisation", "compensation", "dédommagement",
    ],
    "faute grave": [
        "faute lourde", "faute professionnelle grave",
    ],
    "employeur": [
        "patron", "chef d'entreprise", "société", "entreprise", "chef", "boss",
    ],
    "employé": [
        "salarié", "travailleur", "ouvrier", "personnel",
    ],
    "syndicat": [
        "délégué du personnel", "représentant syndical",
    ],
    "harcèlement": [
        "harcèlement moral", "harcèlement au travail", "intimidation",
    ],
    "accident de travail": [
        "accident du travail", "accident professionnel",
    ],
    "convention collective": [
        "accord collectif", "convention",
    ],
}

# Index inversé synonyme -> terme canonique
_SYNONYM_LOOKUP = {}
for canonical, variants in SYNONYMS.items():
    for variant in variants:
        _SYNONYM_LOOKUP[variant.lower()] = canonical
    _SYNONYM_LOOKUP[canonical.lower()] = canonical

# ==============================
# CHARGEMENT MODELES
# ==============================

print("Chargement FAISS...")

if not os.path.exists(INDEX_PATH):
    raise FileNotFoundError(f"Index FAISS introuvable : {INDEX_PATH}")
if not os.path.exists(CHUNKS_PATH):
    raise FileNotFoundError(f"Fichier chunks introuvable : {CHUNKS_PATH}")

index = faiss.read_index(INDEX_PATH)

try:
    IS_SIMILARITY_METRIC = (index.metric_type == faiss.METRIC_INNER_PRODUCT)
except AttributeError:
    IS_SIMILARITY_METRIC = False

print(f"Type de métrique FAISS détecté : {'similarité (produit scalaire)' if IS_SIMILARITY_METRIC else 'distance (L2)'}")

with open(CHUNKS_PATH, "rb") as f:
    chunks = pickle.load(f)

embedding_model = SentenceTransformer(MODEL_EMBEDDING)

print("Chargement du reranker...")
try:
    reranker_model = CrossEncoder(MODEL_RERANKER)
    RERANKER_AVAILABLE = True
except Exception as e:
    logger.warning(f"Reranker indisponible, on continue sans ({e})")
    reranker_model = None
    RERANKER_AVAILABLE = False

print("Construction du vocabulaire pour la correction orthographique...")


def _normalize_text(text):
    """Normalise un texte pour la comparaison uniquement."""
    text = text.lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _build_vocabulary(chunks):
    """Construit un ensemble de mots à partir des chunks."""
    vocab = set()
    for chunk in chunks:
        text = chunk.get("page_content", "")
        text = _normalize_text(text)
        for word in text.split():
            if len(word) >= MIN_WORD_LEN_FOR_CORRECTION:
                vocab.add(word)
    return vocab


VOCABULARY = None

print("RAG prêt")
print("VERSION RAG API ACTIVE")

# ==============================
# CORRECTION ORTHOGRAPHIQUE
# ==============================

def correct_spelling(question):
    """Corrige les fautes d'orthographe dans la question."""
    global VOCABULARY

    if VOCABULARY is None:
        VOCABULARY = _build_vocabulary(chunks)

    corrected_words = []

    for original_word in question.split():
        clean = _normalize_text(original_word)

        if not clean or clean.isdigit():
            corrected_words.append(original_word)
            continue

        if len(clean) < MIN_WORD_LEN_FOR_CORRECTION:
            corrected_words.append(original_word)
            continue

        if clean in COMMON_FRENCH_WORDS:
            corrected_words.append(original_word)
            continue

        if clean in VOCABULARY or clean in _SYNONYM_LOOKUP:
            corrected_words.append(original_word)
            continue

        matches = get_close_matches(
            clean,
            VOCABULARY | set(_SYNONYM_LOOKUP.keys()),
            n=1,
            cutoff=SPELLING_CUTOFF,
        )

        if matches and matches[0][:2] == clean[:2]:
            corrected_words.append(matches[0])
        else:
            corrected_words.append(original_word)

    return " ".join(corrected_words)

# ==============================
# EXPANSION PAR SYNONYMES
# ==============================

def expand_with_synonyms(question):
    """Enrichit la question avec les termes juridiques canoniques."""
    normalized = _normalize_text(question)
    normalized_words = set(normalized.split())
    extra_terms = set()

    for variant, canonical in _SYNONYM_LOOKUP.items():
        variant_normalized = _normalize_text(variant)
        if not variant_normalized:
            continue

        pattern = r"\b" + re.escape(variant_normalized) + r"\b"
        if re.search(pattern, normalized):
            extra_terms.add(canonical)

    extra_terms = {
        term for term in extra_terms
        if _normalize_text(term) not in normalized_words
        and not re.search(r"\b" + re.escape(_normalize_text(term)) + r"\b", normalized)
    }

    if not extra_terms:
        return question

    return question + " " + " ".join(sorted(extra_terms))

# ==============================
# RECHERCHE DOCUMENTS
# ==============================

# Détecte : "article 58", "art 58", "art.58", "l'article 58", "larticle 58",
# "l article 58", "article n°58", "ART 45", etc.
# L'ordre "article" avant "art" est important : sur "article 58" le moteur
# doit essayer "article" en premier (sinon "art" matcherait puis casserait
# sur le "icle" restant).
ARTICLE_PATTERN = re.compile(
    r"\bl?['’]?\s*(?:article|art)\.?\s*(?:n[°o]?\.?\s*|num[eé]ro\s*)?(\d+)",
    re.IGNORECASE,
)


def _find_article_number(question):
    """Détecte un numéro d'article dans la question."""
    match = ARTICLE_PATTERN.search(question.lower())
    if match:
        return int(match.group(1))
    return None


DURATION_KEYWORDS = {
    "combien", "duree", "jours", "jour", "mois", "semaines",
    "semaine", "delai", "delais", "annees", "annee", "ans",
}


def _needs_wider_search(corrected_question):
    words = set(_normalize_text(corrected_question).split())
    return bool(words & DURATION_KEYWORDS) or _is_general_question(corrected_question)


# Questions larges/génériques ("quels sont mes droits ?", "quelles sont les
# obligations de l'employeur ?") : un seul article ne suffit jamais à
# répondre, il faut élargir la recherche pour couvrir plusieurs angles.
GENERAL_QUESTION_KEYWORDS = {
    "droits", "droit", "obligations", "obligation", "regles", "règles",
    "tout", "generalites", "généralités",
}
GENERAL_QUESTION_PATTERNS = [
    re.compile(r"\bquels?\s+sont\b", re.IGNORECASE),
    re.compile(r"\bquelles?\s+sont\b", re.IGNORECASE),
    re.compile(r"\bque\s+dit\s+le\s+code\b", re.IGNORECASE),
]


def _is_general_question(question):
    normalized = _normalize_text(question)
    words = set(normalized.split())

    if words & GENERAL_QUESTION_KEYWORDS:
        return True

    return any(p.search(question) for p in GENERAL_QUESTION_PATTERNS)


def _dedupe_by_article(ranked_pairs, top_n):
    """
    Parcourt les paires (chunk, score) déjà triées par pertinence décroissante
    et ne garde qu'un seul chunk par numéro d'article (le mieux classé),
    jusqu'à obtenir top_n articles distincts. Évite qu'un même article
    (ex: 182) monopolise plusieurs places du contexte final.
    """
    seen_articles = set()
    deduped = []

    for chunk, score in ranked_pairs:
        article_num = chunk.get("metadata", {}).get("article_num", None)

        if article_num is not None and article_num in seen_articles:
            continue

        if article_num is not None:
            seen_articles.add(article_num)

        deduped.append((chunk, score))

        if len(deduped) >= top_n:
            break

    return deduped


def _rerank(question, candidate_chunks, top_n=RERANK_TOP_N):
    """
    Rerank les chunks candidats avec un cross-encoder pour affiner la
    pertinence sémantique (FAISS seul reste assez lexical/approximatif),
    puis déduplique par article pour maximiser la diversité du contexte.
    Retourne (chunks_reordonnes, scores_associes).
    """
    if not candidate_chunks:
        return [], []

    if not RERANKER_AVAILABLE:
        ranked = [(c, None) for c in candidate_chunks]
        deduped = _dedupe_by_article(ranked, top_n)
        return [c for c, _ in deduped], [s for _, s in deduped]

    pairs = [(question, c.get("page_content", "")) for c in candidate_chunks]
    scores = reranker_model.predict(pairs)

    ranked = sorted(zip(candidate_chunks, scores), key=lambda x: x[1], reverse=True)
    deduped = _dedupe_by_article(ranked, top_n)

    reranked_chunks = [c for c, _ in deduped]
    reranked_scores = [float(s) if s is not None else None for _, s in deduped]

    print(f"[Reranker] Top {len(reranked_chunks)} après reranking (dédupliqué) : "
          f"{[c['metadata'].get('article_num') for c in reranked_chunks]}")

    return reranked_chunks, reranked_scores


def search_documents(question, k=FAISS_TOP_K_CANDIDATES):
    """
    Recherche hybride :
    1. Correction orthographique + expansion par synonymes
    2. Recherche exacte article XX
    3. Recherche vectorielle FAISS (candidats larges)
    4. Reranking cross-encoder (précision fine)

    Retourne (results, corrected_question, low_confidence, max_score)
    """

    corrected_question = correct_spelling(question)
    enriched_question = expand_with_synonyms(corrected_question)

    if corrected_question != question:
        print(f"[Correction orthographique] '{question}' -> '{corrected_question}'")

    if enriched_question != corrected_question:
        print(f"[Expansion synonymes] -> '{enriched_question}'")

    top_n = RERANK_TOP_N

    if _needs_wider_search(corrected_question):
        k = max(k, FAISS_TOP_K_WIDE)
        top_n = RERANK_TOP_N_WIDE
        print(f"[Recherche élargie] question de durée/délai détectée (k={k}, top_n={top_n})")

    # ==========================
    # Recherche article exacte
    # ==========================

    # On cherche d'abord dans la question brute (cas normal), puis dans la
    # version corrigée orthographiquement (ex: "ariticle 100" -> "article 100")
    # si rien n'a été trouvé. Sans ça, une faute de frappe sur "article" fait
    # échouer la détection même si correct_spelling() l'a bien corrigée.
    article_num = _find_article_number(question)
    if article_num is None:
        article_num = _find_article_number(corrected_question)

    if article_num is not None:
        exact_results = [
            chunk for chunk in chunks
            if chunk["metadata"]["article_num"] == article_num
        ]

        if exact_results:
            print(f"[Recherche exacte] Article {article_num}")
            return exact_results, corrected_question, False, None

    # ==========================
    # Recherche FAISS (candidats larges)
    # ==========================

    print("[Recherche FAISS]")

    vector = embedding_model.encode(
        [enriched_question],
        normalize_embeddings=True
    )
    vector = vector.astype("float32")

    scores, ids = index.search(vector, k)

    print("\n" + "=" * 50)
    print("DEBUG RETRIEVAL")
    print(f"Question : {question}")
    print(f"Corrigée : {corrected_question}")
    print(f"Enrichie : {enriched_question}")
    print(f"Scores : {scores[0][:5]}...")
    print(f"IDs : {ids[0][:5]}...")

    for idx in ids[0]:
        if idx != -1:
            print(f"Article trouvé : {chunks[idx]['metadata']['article_num']}")
    print("=" * 50 + "\n")

    candidates = []
    max_score = None

    for score, idx in zip(scores[0], ids[0]):
        if idx == -1:
            continue

        if IS_SIMILARITY_METRIC:
            if score < FAISS_MIN_SIMILARITY:
                continue
            if max_score is None or score > max_score:
                max_score = float(score)
        else:
            if score > FAISS_MAX_DISTANCE:
                continue

        candidates.append(chunks[idx])

    if not candidates:
        print("[Recherche FAISS] Aucun résultat suffisamment pertinent")
        return [], corrected_question, False, max_score

    # ==========================
    # Reranking
    # ==========================

    results, rerank_scores = _rerank(enriched_question, candidates, top_n=top_n)

    low_confidence = (
        IS_SIMILARITY_METRIC
        and max_score is not None
        and max_score < LOW_CONFIDENCE_THRESHOLD
    )

    return results, corrected_question, low_confidence, max_score

# ==============================
# APPEL GROQ AVEC RETRY + FALLBACK
# ==============================

def _call_groq(model, system_prompt, user_prompt, max_tokens=DEFAULT_MAX_TOKENS, temperature=0.1):
    return client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )


def call_groq_with_fallback(system_prompt, user_prompt, max_tokens=DEFAULT_MAX_TOKENS, temperature=0.1):
    """
    Essaie le modèle principal (avec retries sur erreurs réseau transitoires),
    puis bascule sur le modèle de secours en cas de rate limit ou d'échec
    persistant. Retourne (texte_reponse, modele_utilise).
    """

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = _call_groq(PRIMARY_MODEL, system_prompt, user_prompt, max_tokens, temperature)
            return response.choices[0].message.content, PRIMARY_MODEL

        except RateLimitError as e:
            logger.warning(f"[Groq] Rate limit atteint sur {PRIMARY_MODEL} : {e}")
            break

        except (APIConnectionError, APIError) as e:
            logger.warning(f"[Groq] Tentative {attempt}/{MAX_RETRIES} échouée sur {PRIMARY_MODEL} : {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)

    print(f"[Fallback] Basculement vers le modèle de secours : {FALLBACK_MODEL}")
    try:
        response = _call_groq(FALLBACK_MODEL, system_prompt, user_prompt, max_tokens, temperature)
        return response.choices[0].message.content, FALLBACK_MODEL

    except RateLimitError as e:
        raise RuntimeError(
            "Le quota quotidien de l'API Groq est dépassé pour les deux modèles. "
            "Merci de réessayer plus tard ou de vérifier votre quota sur console.groq.com."
        ) from e

    except (APIConnectionError, APIError) as e:
        raise RuntimeError(
            "Impossible de contacter l'API Groq (problème réseau ou service "
            "indisponible). Merci de réessayer dans quelques instants."
        ) from e

# ==============================
# VERIFICATION POST-REPONSE
# ==============================

CITED_ARTICLE_PATTERN = re.compile(r"article\s+(\d+)", re.IGNORECASE)


def _verify_answer(answer, articles_in_context):
    """
    Vérifie que tous les articles cités dans la réponse du LLM font bien
    partie du contexte fourni. Retourne une note d'avertissement si un
    article "halluciné" est détecté (cité mais absent du contexte).
    """
    cited = {int(m) for m in CITED_ARTICLE_PATTERN.findall(answer)}
    unsupported = cited - set(a for a in articles_in_context if isinstance(a, int))

    if unsupported:
        unsupported_str = ", ".join(str(a) for a in sorted(unsupported))
        logger.warning(f"[Verification] Articles cités mais absents du contexte : {unsupported_str}")
        return (
            f"\n\n⚠️ Vérification automatique : la réponse mentionne l'article "
            f"{unsupported_str} qui n'apparaît pas dans les documents consultés. "
            f"Merci de vérifier cette information avant de vous y fier."
        )
    return ""

# ==============================
# GENERATION (RAG + GROQ)
# ==============================

def ask_legal_ai(question):
    """
    Fonction principale : répond à une question juridique
    en utilisant le RAG sur le Code du travail malgache.
    """
    original_question = question

    documents, corrected_question, low_confidence, max_score = search_documents(question)

    if not documents:
        return (
            "Je ne trouve pas cette information dans le Code du "
            "travail malgache. Pouvez-vous reformuler votre question "
            "ou préciser l'article concerné ?"
        )

    # Construction du contexte (format compact, sans doublon avec "SOURCES")
    context_parts = []
    articles_set = set()

    for doc in documents:
        if isinstance(doc, dict):
            content = doc.get("page_content", str(doc))
            metadata = doc.get("metadata", {})
            article = metadata.get("article_num", "inconnu")
            articles_set.add(article)
            context_parts.append(f"ARTICLE {article}\n{content}")
        else:
            context_parts.append(str(doc))

    context = "\n\n".join(context_parts)

    nb_articles = len(articles_set)
    articles_str = ", ".join(str(a) for a in sorted(articles_set) if a != "inconnu")

    prompt = f"""
Tu es LegalAI, un assistant spécialisé dans le Code du travail malgache.

Règles STRICTES (à respecter impérativement) :
- Utilise UNIQUEMENT les articles présents dans le CONTEXTE ci-dessous. N'utilise AUCUNE connaissance externe.
- Si un droit, une obligation ou un délai n'est pas explicitement mentionné dans les articles fournis, ne l'invente pas et dis-le clairement.
- Ne transforme jamais une obligation de l'employeur en droit du salarié (ou l'inverse) sans que ce soit écrit noir sur blanc dans le texte fourni.
- Cite précisément les numéros d'articles que tu utilises ({nb_articles} articles disponibles : {articles_str}).
- Si la question est générale (ex: "congés"), mentionne tous les articles pertinents parmi ceux fournis, mais uniquement ceux-ci.
- Structure ta réponse de manière claire et pédagogique.
- Termine TOUJOURS par une section "Références :" listant les numéros d'articles réellement utilisés.

CONTEXTE JURIDIQUE ({nb_articles} articles) :
{context}

QUESTION ORIGINALE :
{original_question}

QUESTION NORMALISÉE :
{corrected_question}

RÉPONSE :
"""

    system_prompt = "Tu es un assistant juridique précis et exhaustif. Tu ne réponds jamais au-delà de ce que dit le texte fourni."

    try:
        answer, used_model = call_groq_with_fallback(system_prompt, prompt, max_tokens=DEFAULT_MAX_TOKENS, temperature=0.1)

        # Vérification anti-hallucination : les articles cités existent-ils dans le contexte ?
        answer += _verify_answer(answer, articles_set)

        if low_confidence:
            answer += (
                "\n\nℹ️ Remarque : la correspondance trouvée dans le Code du travail est "
                "assez faible pour cette question. N'hésitez pas à préciser votre demande "
                "(ex: préciser le sujet exact ou le numéro d'article) pour affiner la réponse."
            )

        if used_model != PRIMARY_MODEL:
            answer += f"\n\n_(Réponse générée avec le modèle de secours {used_model} suite à une indisponibilité du modèle principal.)_"

        return answer

    except RuntimeError as e:
        logger.error(f"[LegalAI] Échec définitif de la génération : {e}")
        return f"⚠️ {e}"

    except Exception:
        logger.exception("[LegalAI] Erreur inattendue lors de la génération")
        return (
            "⚠️ Une erreur inattendue est survenue lors de la génération de la "
            "réponse. Merci de réessayer."
        )

# ==============================
# MODE CHAT TERMINAL
# ==============================

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print(" LegalAI - Chatbot Droit du travail malgache")
    print("=" * 50)
    print("Tapez 'exit' pour quitter\n")

    while True:
        try:
            question = input("Vous : ")
        except (KeyboardInterrupt, EOFError):
            print("\nAu revoir !")
            break

        if question.lower() in ["exit", "quit", "q"]:
            print("Au revoir !")
            break

        if question.strip() == "":
            continue

        answer = ask_legal_ai(question)

        print("\n" + "=" * 50)
        print("LegalAI :")
        print("=" * 50)
        print(answer)
        print("\n" + "=" * 50 + "\n")
