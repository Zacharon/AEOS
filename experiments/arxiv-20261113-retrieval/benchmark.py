"""Human terminal / JSON diagnostic, sharing one offline command handler."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import statistics
import subprocess
import sys
import time

from retrieval import (CUTOFFS, DEPTHS, METHODS, PRIMARY_DEPTH, PRIMARY_K,
                       LexicalIndex, VectorFixtureIndex, metrics, paired,
                       search_method, select_from_development, summary,
                       validate_vectors, word_context)

ROOT = Path(__file__).resolve().parent
REPOSITORY = ROOT.parents[1]
SOURCE = ('distribution/agentic-engineering-os-2026.10.17-public.4/'
          'vault/09_TOOLS/agent_runner_v1/unified_handoff/handoff.py')
MAX_REQUEST_BYTES = 8192


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def strict_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON key')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Non-finite JSON value')))


def load_handoff():
    """Import only the genuine public package module; no mutable path discovery."""
    source = REPOSITORY / SOURCE
    spec = importlib.util.spec_from_file_location('public_aeos_handoff', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FixtureAdapter:
    """Explicit synthetic allowlist mapped through existing handoff read guards."""
    def __init__(self):
        self.handoff = load_handoff()
        self.base = ROOT / 'fixtures'
        manifest_raw = self.handoff.read_bytes(self.base / 'manifest.json', 128 * 1024)
        self.manifest_hash = digest(manifest_raw)
        if self.handoff.read_bytes(self.base / 'manifest.sha256', 256).decode('ascii').strip() != self.manifest_hash:
            raise ValueError('Frozen manifest digest mismatch')
        self.manifest = strict_json(manifest_raw)
        if self.manifest['schema'] != 1:
            raise ValueError('Unsupported fixture schema')
        if len(self.manifest['files']) > 100:
            raise ValueError('Too many fixtures')
        self.raw = {}
        # Verify bytes of all heldout fixtures now, but do not parse labels for selection.
        for relative, expected in self.manifest['files'].items():
            path = self.handoff.within(self.base, relative)
            raw = self.handoff.read_bytes(path, 128 * 1024)
            if digest(raw) != expected:
                raise ValueError('Frozen fixture digest mismatch: ' + relative)
            self.raw[relative] = raw
        self.documents = []
        corpus = self.read_json('corpus.json')
        if len(corpus) > 80 or len({row['id'] for row in corpus}) != len(corpus):
            raise ValueError('Invalid or duplicate corpus identities')
        for row in corpus:
            relative = row['path']
            if relative not in self.raw:
                raise ValueError('Document not in frozen allowlist')
            path = self.handoff.within(self.base, relative, markdown=True)
            raw = self.handoff.markdown_bytes(path)
            if raw != self.raw[relative]:
                raise ValueError('Document changed while loading')
            self.documents.append({**row, 'text': raw.decode('utf8'),
                                   'sha256': self.handoff.digest(raw)})
        self.by_id = {row['id']: row for row in self.documents}
        supplied = self.read_json('vectors.json')
        validate_vectors(supplied['documents'], supplied['queries'])
        if set(supplied['documents']) != set(self.by_id):
            raise ValueError('Vector/corpus identity mismatch')
        self.query_vectors = supplied['queries']
        started = time.perf_counter_ns()
        self.lexical = LexicalIndex(self.documents)
        self.vector = VectorFixtureIndex(supplied['documents'])
        self.index_build_ms = (time.perf_counter_ns()-started)/1e6

    def read_json(self, name):
        return strict_json(self.raw[name])

    def queries(self, split):
        if split not in ('development', 'heldout'):
            raise ValueError('Unknown split')
        rows = self.read_json(split + '.json')
        if not 1 <= len(rows) <= 100 or len({row['id'] for row in rows}) != len(rows):
            raise ValueError('Invalid or duplicate query identities')
        for row in rows:
            if (not isinstance(row['text'], str) or not row['text'].strip() or len(row['text']) > 2000
                    or row['id'] not in self.query_vectors):
                raise ValueError('Invalid query or absent supplied vector')
            if (not isinstance(row['relevant'], dict)
                    or not set(row['relevant']) <= self.by_id.keys()
                    or any(type(grade) is not int or grade not in (1, 2) for grade in row['relevant'].values())):
                raise ValueError('Invalid authored qrels')
        return rows

    def suggestions(self, ids):
        return [{'id': key, 'path': 'fixtures/' + self.by_id[key]['path'],
                 'sha256': self.by_id[key]['sha256'], 'status': 'synthetic suggestion; no read grant'}
                for key in ids]


def measure(adapter, query, method, depth):
    def run():
        # The retriever receives text and the explicit vector only, never qrels/kind.
        return search_method(method, adapter.lexical, adapter.vector, query['text'],
                             adapter.query_vectors[query['id']], depth)
    rows = run()  # untimed warmup
    samples = []
    for _ in range(9):
        start = time.perf_counter_ns()
        repeated = run()
        samples.append((time.perf_counter_ns()-start)/1e6)
        if repeated != rows:
            raise ValueError('Non-deterministic ranking')
    return rows, {'median': statistics.median(samples),
                  'p95': sorted(samples)[math.ceil(.95*len(samples))-1], 'samples': samples}


def evaluate_queries(adapter, queries, split, depth):
    results = []
    for query in queries:
        methods = {}
        for method in METHODS:
            rows, latency = measure(adapter, query, method, depth)
            ids = [key for key, _ in rows]
            relevance = query['relevant']
            raw = metrics(ids, relevance, max(1, len(ids)))
            methods[method] = {
                'ranking': [{'id': key, 'score': score} for key, score in rows],
                'candidate_metrics': raw,
                'at_k': {str(k): metrics(ids, relevance, k) for k in CUTOFFS},
                'candidate_to_context_recall_loss': (raw['recall'] - metrics(ids, relevance, PRIMARY_K)['recall'])
                    if relevance else None,
                'latency_ms': latency,
                'word_budgets': {},
            }
            for budget in (30, 60, 120):
                context, used = word_context(ids, adapter.by_id, budget)
                methods[method]['word_budgets'][str(budget)] = {
                    'ids': context, 'words_used': used,
                    'metrics': metrics(context, relevance, max(1, len(context))),
                    'lost_relevant_ids': sorted((set(ids) & relevance.keys()) - set(context)),
                }
        results.append({'id': query['id'], 'split': split, 'kind': query['kind'],
                        'text': query['text'], 'answerable': bool(query['relevant']),
                        'authored_qrels': query['relevant'], 'methods': methods})
    return results


def aggregate(query_results):
    methods = {}
    for method in METHODS:
        latencies = [sample for row in query_results for sample in row['methods'][method]['latency_ms']['samples']]
        answerable = [row for row in query_results if row['answerable']]
        methods[method] = {
            'at_k': {str(k): summary(query_results, method, k) for k in CUTOFFS},
            'mean_candidate_recall': statistics.mean(row['methods'][method]['candidate_metrics']['recall']
                                                    for row in answerable),
            'mean_candidate_to_context_recall_loss': statistics.mean(
                row['methods'][method]['candidate_to_context_recall_loss'] for row in answerable),
            'word_budgets': {str(budget): {
                'mean_recall': statistics.mean(row['methods'][method]['word_budgets'][str(budget)]['metrics']['recall']
                                               for row in answerable),
                'mean_ndcg': statistics.mean(row['methods'][method]['word_budgets'][str(budget)]['metrics']['ndcg']
                                             for row in answerable),
            } for budget in (30, 60, 120)},
            'latency_ms': {'median': statistics.median(latencies),
                           'p95': sorted(latencies)[math.ceil(.95*len(latencies))-1],
                           'n': len(latencies)},
            'paired_at_3': {ref: paired(query_results, method, ref)
                            for ref in ('lexical_overlap', 'bm25', 'vector_fixture', 'better_component')},
        }
    categories = sorted({row['kind'] for row in query_results})
    return {'methods': methods,
            'by_kind_at_3': {kind: {method: summary([row for row in query_results if row['kind'] == kind], method)
                                   for method in METHODS} for kind in categories}}


def benchmark(adapter):
    development = adapter.queries('development')
    dev_results = evaluate_queries(adapter, development, 'development', PRIMARY_DEPTH)
    selection = select_from_development(dev_results)
    policy_hash = digest(json.dumps(selection, sort_keys=True).encode())
    # Selection is finished before heldout labels are parsed. Depth sweeps are diagnostic.
    heldout = adapter.queries('heldout')
    if {q['id'] for q in development} & {q['id'] for q in heldout}:
        raise ValueError('Development and heldout IDs must be disjoint')
    test_results = evaluate_queries(adapter, heldout, 'heldout', PRIMARY_DEPTH)
    depths = {}
    for depth in DEPTHS:
        dev = dev_results if depth == PRIMARY_DEPTH else evaluate_queries(adapter, development, 'development', depth)
        test = test_results if depth == PRIMARY_DEPTH else evaluate_queries(adapter, heldout, 'heldout', depth)
        depths[str(depth)] = {'development': {'aggregate': aggregate(dev), 'queries': dev},
                              'heldout': {'aggregate': aggregate(test), 'queries': test}}
    selected = selection['selected_method']
    baseline = selection['component_default']
    return {
        'capability': 'synthetic-retrieval-diagnostic/v1', 'status': 'BOUNDED_LOCAL_CANDIDATE',
        'provenance': {'source_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPOSITORY,
                                                              text=True).strip(),
                       'worktree': 'dedicated checkout; repository-relative experiment scope only',
                       'python': sys.version.split()[0], 'fixtures_manifest_sha256': adapter.manifest_hash,
                       'handoff_module': SOURCE, 'handoff_module_sha256': digest((REPOSITORY / SOURCE).read_bytes()),
                       'implementation_sha256': {name: digest((ROOT/name).read_bytes())
                                                 for name in ('benchmark.py', 'retrieval.py')},
                       'neural_retrieval': 'NOT RUN; no cached local sentence model found in bounded availability check',
                       'vector_retrieval': 'RUN; cosine of authored fixture vectors, not measured embeddings',
                       'manual_file_selection_baseline': 'NOT RUN; no human selections were supplied',
                       'ground_truth': 'implementer authored, frozen synthetic graded relevance; not user labels'},
        'configuration': {'primary_candidate_depth_per_component': PRIMARY_DEPTH, 'context_k': PRIMARY_K,
                           'depth_sweep': list(DEPTHS), 'context_k_sweep': list(CUTOFFS), 'word_budgets': [30,60,120],
                           'latency': 'warm CPU search plus required component searches and fusion; no embedding inference, imports, I/O or reranker',
                           'index_build_ms': adapter.index_build_ms,
                           'reranking': 'NOT RUN; prefix and whole-document word-budget truncation only',
                           'generation': 'NOT RUN; evidence availability is not answer quality'},
        'selection': selection, 'selection_sha256': policy_hash,
        'heldout_selected_vs_component_default': paired(test_results, selected, baseline),
        'depths': depths,
        'integration_recommendation': 'Keep existing explicit manual selection. Do not enable fusion by default on this evidence. Validate a read-only suggestion adapter with a real approved local retriever and fresh frozen cases before any product proposal.',
    }


def execute(request):
    """Shared human / agent handler. Returned data is identical before formatting."""
    if not isinstance(request, dict) or set(request) - {'operation', 'query_id', 'output'}:
        raise ValueError('Request must contain only operation, query_id and optional output')
    operation = request.get('operation')
    if operation not in ('benchmark', 'query'):
        raise ValueError('operation must be benchmark or query')
    if operation == 'benchmark' and 'query_id' in request:
        raise ValueError('benchmark takes no query_id')
    # Validate the output destination before doing work; only new local JSON basenames.
    output = request.get('output')
    target = None
    if output is not None:
        if (not isinstance(output, str) or not output or Path(output).name != output
                or '/' in output or '\\' in output or ':' in output or not output.endswith('.json')):
            raise ValueError('output must be a new JSON basename inside the experiment directory')
        if output.startswith('.') or output in {'fixtures.json'}:
            raise ValueError('Unsupported output basename')
        target = ROOT/output
        if target.exists() or target.is_symlink():
            raise ValueError('Existing output refused; preserve it and choose another basename')
    adapter = FixtureAdapter()
    if operation == 'benchmark':
        result = benchmark(adapter)
    else:
        query_id = request.get('query_id')
        queries = [(split, query) for split in ('development', 'heldout') for query in adapter.queries(split)
                   if query['id'] == query_id]
        if len(queries) != 1:
            raise ValueError('Unknown query_id; use an ID from the frozen query lists')
        split, query = queries[0]
        result = evaluate_queries(adapter, [query], split, PRIMARY_DEPTH)[0]
        for method in METHODS:
            ids = [row['id'] for row in result['methods'][method]['ranking'][:PRIMARY_K]]
            result['methods'][method]['suggestions'] = adapter.suggestions(ids)
    if target is not None:
        with target.open('x', encoding='utf8', newline='\n') as handle:
            json.dump(result, handle, indent=2, allow_nan=False)
            handle.write('\n')
    return result


def human_display(result):
    if 'selection' not in result:
        lines = [f"Query {result['id']}: {result['text']}"]
        for method, row in result['methods'].items():
            ids = ', '.join(item['id'] for item in row['ranking'][:3]) or '(empty)'
            lines.append(f"{method:20} {ids}")
        return '\n'.join(lines)
    selected = result['selection']['selected_method']
    lines = ['Synthetic fixture diagnostic; neural retrieval NOT RUN',
             f'Development-only global selection: {selected}',
             'Heldout (10 answerable, 2 no-answer):',
             'method                R@3     MRR@3   nDCG@3  harm/BM25 harm/vector']
    methods = result['depths']['6']['heldout']['aggregate']['methods']
    for method, row in methods.items():
        at = row['at_k']['3']
        harm = row['paired_at_3']
        lines.append(f"{method:21} {at['recall']:.4f}  {at['mrr']:.4f}  {at['ndcg']:.4f}  "
                     f"{harm['bm25']['hurt_n']:9} {harm['vector_fixture']['hurt_n']:11}")
    lines.append('No-answer false positives, candidate/context losses and measured latency are in JSON.')
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    bench = sub.add_parser('benchmark', help='Run all frozen cases; select on development only')
    bench.add_argument('--output', help='New local JSON basename; existing evidence is refused')
    query = sub.add_parser('query', help='Inspect a frozen case, without changing selection')
    query.add_argument('query_id')
    agent = sub.add_parser('json', help='Read a JSON request from stdin; use the same handler')
    args = parser.parse_args(argv)
    try:
        if args.command == 'json':
            raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES+1)
            if len(raw) > MAX_REQUEST_BYTES:
                raise ValueError('JSON request exceeds 8192-byte bound')
            request = strict_json(raw)
        else:
            request = {'operation': args.command}
            if args.command == 'benchmark' and args.output is not None:
                request['output'] = args.output
            if args.command == 'query':
                request['query_id'] = args.query_id
        result = execute(request)
        print(json.dumps(result, allow_nan=False) if args.command == 'json' else human_display(result))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        # Do not serialize absolute machine paths from imported guard errors.
        message = str(exc)
        if str(REPOSITORY) in message or str(ROOT) in message:
            message = 'Local fixture/source validation failed; inspect the frozen inputs'
        print(json.dumps({'status': 'REFUSED', 'error': message}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
