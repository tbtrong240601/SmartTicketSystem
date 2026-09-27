"""Deterministic lexical retrieval. No embeddings, training or external calls."""
from collections import Counter
import math
import re
import unicodedata

STOP = set("va la cua cho toi cac mot nhung voi duoc can khi thi de da hay gi bi co khong".split())


def normalize(text):
    plain = unicodedata.normalize("NFKD", text.lower().replace("đ", "d"))
    return "".join(char for char in plain if not unicodedata.combining(char))


def baseline_tokens(text):
    return set(re.findall(r"[a-z0-9]{2,}", normalize(text))) - STOP


def terms(text):
    # Normalize common technical spellings, not a semantic embedding model.
    plain = re.sub(r"\bwi[ -]?fi\b", "wifi", normalize(text))
    return [word for word in re.findall(r"[a-z0-9]{2,}", plain) if word not in STOP]


def rank_articles(question, articles, method="bm25", limit=3):
    articles = list(articles)
    if not articles or limit <= 0:
        return []
    if method == "baseline":
        query = baseline_tokens(question)
        scores = [(3 * len(query & baseline_tokens(a.title)) + len(query & baseline_tokens(a.content)), a) for a in articles]
    elif method == "bm25":
        query = set(terms(question))
        documents = [terms(a.title) * 3 + terms(a.content) for a in articles]
        counters = [Counter(document) for document in documents]
        frequencies = Counter(word for counter in counters for word in counter)
        average_length = sum(map(len, documents)) / len(documents) or 1
        scores = []
        for article, document, counter in zip(articles, documents, counters):
            score = 0.0
            for word in query:
                frequency = counter[word]
                if not frequency:
                    continue
                idf = math.log(1 + (len(documents) - frequencies[word] + 0.5) / (frequencies[word] + 0.5))
                norm = frequency + 1.5 * (1 - 0.75 + 0.75 * len(document) / average_length)
                score += idf * frequency * 2.5 / norm
            scores.append((score, article))
    else:
        raise ValueError("Unknown retrieval method")
    return [article for score, article in sorted(scores, key=lambda row: (-row[0], -row[1].id)) if score > 0][:limit]
