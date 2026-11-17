"""Dependency-free retrieval and diagnostic primitives; no fixture or label I/O."""
from __future__ import annotations

from collections import Counter
import math
import re

EPS = 1e-12
PRIMARY_K = 3
PRIMARY_DEPTH = 6
CUTOFFS = (1, 3, 5)
DEPTHS = (1, 3, 6)
WEIGHTS = (0.3, 0.5, 0.7)


def tokens(text):
    """Keep exact hyphenated identifiers intact. No stemming or stopword tuning."""
    return re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", text.casefold())


def ranked(scores):
    """All methods break ties by document ID, never by a relevance label."""
    return sorted(scores.items(), key=lambda row: (-row[1], row[0]))


class LexicalIndex:
    def __init__(self, documents):
        self.tf = {d['id']: Counter(tokens(d['text'])) for d in documents}
        self.lengths = {key: sum(tf.values()) for key, tf in self.tf.items()}
        self.avg_length = sum(self.lengths.values()) / max(1, len(self.tf))
        self.df = Counter(t for tf in self.tf.values() for t in tf)

    def search(self, text, *, bm25=True, depth=6):
        scores = {}
        for key, tf in self.tf.items():
            score = 0.0
            for term in sorted(set(tokens(text))):
                freq = tf[term]
                if not freq:
                    continue
                if not bm25:
                    score += 1
                    continue
                # Positive Robertson IDF; flat field, k1=.9, b=.4.
                idf = math.log(1 + (len(self.tf) - self.df[term] + .5) / (self.df[term] + .5))
                norm = .9 * (1 - .4 + .4 * self.lengths[key] / self.avg_length)
                score += idf * freq * 1.9 / (freq + norm)
            if score > 0:
                scores[key] = score
        return ranked(scores)[:depth]


def validate_vectors(doc_vectors, query_vectors):
    vectors = [*doc_vectors.values(), *query_vectors.values()]
    if not vectors or not isinstance(vectors[0], list) or not vectors[0]:
        raise ValueError('Vectors must be nonempty arrays')
    size = len(vectors[0])
    if size > 4096:
        raise ValueError('Vector dimension exceeds diagnostic bound')
    for vector in vectors:
        if (not isinstance(vector, list) or len(vector) != size
                or any(type(x) not in (int, float) or not math.isfinite(x) for x in vector)
                or not any(vector)):
            raise ValueError('Vectors must have equal dimensions, finite numbers and nonzero norm')


class VectorFixtureIndex:
    """Actual cosine search over supplied vectors; this is not a neural encoder."""
    def __init__(self, vectors):
        validate_vectors(vectors, {})
        self.vectors = {key: self.normalize(vector) for key, vector in vectors.items()}

    @staticmethod
    def normalize(vector):
        norm = math.sqrt(sum(x*x for x in vector))
        return [x / norm for x in vector]

    def search(self, vector, depth=6):
        validate_vectors(self.vectors, {'query': vector})
        query = self.normalize(vector)
        scores = {key: sum(x*y for x, y in zip(query, values))
                  for key, values in self.vectors.items()}
        return ranked({key: value for key, value in scores.items() if value > 0})[:depth]


def rrf(lists, constant=60):
    if constant <= 0:
        raise ValueError('RRF constant must be positive')
    scores = Counter()
    for rows in lists:
        seen = set()
        for position, (key, _) in enumerate(rows, 1):
            if key not in seen:
                scores[key] += 1 / (constant + position)
                seen.add(key)
    return ranked(scores)


def minmax(rows):
    if not rows:
        return {}
    low, high = min(x[1] for x in rows), max(x[1] for x in rows)
    # A constant-score nonempty list preserves presence rather than vanishing.
    if high == low:
        return {key: 1.0 for key, _ in rows}
    return {key: (value - low) / (high - low) for key, value in rows}


def interpolate(sparse, vector, alpha):
    if not 0 <= alpha <= 1:
        raise ValueError('Interpolation vector weight must lie in [0,1]')
    left, right = minmax(sparse), minmax(vector)
    return ranked({key: (1-alpha)*left.get(key, 0) + alpha*right.get(key, 0)
                   for key in left.keys() | right.keys()})


def retrieve_methods(lexical, vector, text, query_vector, depth):
    sparse = lexical.search(text, depth=depth)
    dense_fixture = vector.search(query_vector, depth=depth)
    return {
        'lexical_overlap': lexical.search(text, bm25=False, depth=depth),
        'bm25': sparse,
        'vector_fixture': dense_fixture,
        'rrf': rrf([sparse, dense_fixture]),
        **{f'interpolation_{alpha:.1f}': interpolate(sparse, dense_fixture, alpha)
           for alpha in WEIGHTS},
    }


METHODS = ('lexical_overlap', 'bm25', 'vector_fixture', 'rrf',
           *(f'interpolation_{alpha:.1f}' for alpha in WEIGHTS))


def search_method(method, lexical, vector, text, query_vector, depth=6):
    """One request includes all upstream component search needed by that method."""
    if method == 'lexical_overlap':
        return lexical.search(text, bm25=False, depth=depth)
    if method == 'bm25':
        return lexical.search(text, depth=depth)
    if method == 'vector_fixture':
        return vector.search(query_vector, depth=depth)
    if method not in METHODS:
        raise ValueError('Unknown retrieval method')
    sparse = lexical.search(text, depth=depth)
    supplied = vector.search(query_vector, depth=depth)
    if method == 'rrf':
        return rrf([sparse, supplied])
    return interpolate(sparse, supplied, float(method.rsplit('_', 1)[1]))


def metrics(ids, relevance, k):
    """No-answer queries have undefined retrieval relevance metrics, never zero/one."""
    if not relevance:
        return {'recall': None, 'mrr': None, 'ndcg': None, 'complete': None,
                'false_positive': bool(ids[:k])}
    top = ids[:k]
    if len(set(top)) != len(top):
        raise ValueError('Duplicate document IDs must not inflate metrics')
    dcg = sum((2**relevance.get(key, 0)-1) / math.log2(i+2)
              for i, key in enumerate(top))
    ideal = sum((2**grade-1) / math.log2(i+2)
                for i, grade in enumerate(sorted(relevance.values(), reverse=True)[:k]))
    hits = set(top) & relevance.keys()
    return {'recall': len(hits) / len(relevance),
            'mrr': next((1/(i+1) for i, key in enumerate(top) if key in relevance), 0.0),
            'ndcg': dcg / ideal, 'complete': len(hits) == len(relevance),
            'false_positive': None}


def word_context(ids, documents, budget):
    """Whole-document ranked prefix, measured in whitespace words, not model tokens."""
    kept, used = [], 0
    for key in ids:
        size = len(documents[key]['text'].split())
        if used + size > budget:
            break
        kept.append(key)
        used += size
    return kept, used


def summary(query_results, method, k=3):
    answerable = [q['methods'][method]['at_k'][str(k)] for q in query_results if q['answerable']]
    unanswerable = [q['methods'][method]['at_k'][str(k)] for q in query_results if not q['answerable']]
    mean = lambda values: sum(values) / len(values) if values else None
    return {'answerable_n': len(answerable), 'no_answer_n': len(unanswerable),
            **{name: mean([row[name] for row in answerable])
               for name in ('recall', 'mrr', 'ndcg', 'complete')},
            'no_answer_false_positive_rate': mean([row['false_positive'] for row in unanswerable])}


def paired(query_results, method, reference, k=3):
    """Positive tax is harm; reference='better_component' is diagnostic only."""
    deltas = []
    recalls = []
    by_query = []
    for query in query_results:
        if not query['answerable']:
            continue
        current = query['methods'][method]['at_k'][str(k)]
        if reference == 'better_component':
            base = {metric: max(query['methods'][component]['at_k'][str(k)][metric]
                                for component in ('bm25', 'vector_fixture'))
                    for metric in ('ndcg', 'recall')}
        else:
            base = query['methods'][reference]['at_k'][str(k)]
        delta = current['ndcg'] - base['ndcg']
        recall_delta = current['recall'] - base['recall']
        deltas.append(delta)
        recalls.append(recall_delta)
        by_query.append({'query_id': query['id'], 'ndcg_delta': delta,
                         'recall_delta': recall_delta, 'fusion_tax': -delta})
    hurt = [x for x in deltas if x < -EPS]
    helped = [x for x in deltas if x > EPS]
    return {'reference': reference, 'n': len(deltas), 'hurt_n': len(hurt),
            'helped_n': len(helped), 'tied_n': len(deltas)-len(hurt)-len(helped),
            'mean_ndcg_delta': sum(deltas)/len(deltas) if deltas else None,
            'mean_recall_delta': sum(recalls)/len(recalls) if recalls else None,
            'mean_loss_when_hurt': -sum(hurt)/len(hurt) if hurt else 0.0,
            'mean_gain_when_helped': sum(helped)/len(helped) if helped else 0.0,
            'worst_ndcg_loss': -min([0.0, *deltas]), 'per_query': by_query}


def select_from_development(development_results):
    """One global policy, no access to test labels, identifiers or query kind at serve time."""
    if not development_results or any(q['split'] != 'development' for q in development_results):
        raise ValueError('Selection accepts development evidence only')
    components = ('bm25', 'vector_fixture')
    averages = {method: summary(development_results, method) for method in components}
    if any(averages[method]['ndcg'] is None for method in components):
        raise ValueError('Selection requires answerable development evidence')
    baseline = max(components, key=lambda method: (averages[method]['ndcg'], method == 'bm25'))
    chosen = baseline
    decisions = []
    for candidate in ('rrf', *(f'interpolation_{weight:.1f}' for weight in WEIGHTS)):
        score = summary(development_results, candidate)
        gain = score['ndcg'] - averages[baseline]['ndcg']
        harms = {method: paired(development_results, candidate, method)['hurt_n'] for method in components}
        hop_safe = all(q['methods'][candidate]['at_k']['3']['complete'] >=
                       q['methods'][baseline]['at_k']['3']['complete']
                       for q in development_results if q['kind'] == 'multi_hop')
        no_answer_safe = all(not q['methods'][candidate]['at_k']['3']['false_positive']
                             or q['methods'][baseline]['at_k']['3']['false_positive']
                             for q in development_results if not q['answerable'])
        eligible = gain >= .02 and not any(harms.values()) and hop_safe and no_answer_safe
        decisions.append({'candidate': candidate, 'ndcg_gain_vs_component_default': gain,
                          'hurt_n_vs_each_component': harms, 'multi_hop_safe': hop_safe,
                          'no_answer_safe': no_answer_safe, 'eligible': eligible})
        if eligible and score['ndcg'] > summary(development_results, chosen)['ndcg'] + EPS:
            chosen = candidate
    return {'schema': 1, 'source_split': 'development', 'query_ids': [q['id'] for q in development_results],
            'component_default': baseline, 'selected_method': chosen, 'is_fusion': chosen not in components,
            'rule': 'global; minimum .02 nDCG@3 gain and zero component harm; no heldout routing',
            'component_development_summary': averages, 'candidate_decisions': decisions}
