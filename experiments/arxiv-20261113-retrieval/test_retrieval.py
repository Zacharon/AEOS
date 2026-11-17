"""Counterexamples and contract checks for the isolated synthetic diagnostic."""
import copy
import io
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import benchmark as b
from retrieval import (LexicalIndex, VectorFixtureIndex, interpolate, metrics, paired,
                       rrf, select_from_development, validate_vectors, word_context)


def without_timings(result):
    result = copy.deepcopy(result)
    for row in result['methods'].values():
        row.pop('latency_ms')
        row.pop('suggestions', None)
    return result


class RetrievalTests(unittest.TestCase):
    def test_bm25_known_numeric_result_and_exact_identifier(self):
        index = LexicalIndex([{'id': 'a', 'text': 'REF-104'}, {'id': 'b', 'text': 'REF-140'}])
        rows = index.search('REF-104')
        self.assertEqual([key for key, _ in rows], ['a'])
        self.assertAlmostEqual(rows[0][1], math.log(2))

    def test_no_lexical_evidence_returns_empty(self):
        index = LexicalIndex([{'id': 'a', 'text': 'a pipe'}])
        self.assertEqual(index.search('tachyon pension'), [])

    def test_cosine_requires_real_supplied_vector_and_handles_nonunit_values(self):
        index = VectorFixtureIndex({'a': [2, 0], 'b': [1, 1], 'c': [-1, 0]})
        self.assertEqual([key for key, _ in index.search([7, 0])], ['a', 'b'])
        self.assertAlmostEqual(index.search([7, 0])[1][1], 1/math.sqrt(2))
        for query in ([1], [0, 0], [float('nan'), 1], [True, 1]):
            with self.assertRaises(ValueError):
                index.search(query)

    def test_rrf_deduplicates_and_keeps_missing_component_candidates(self):
        rows = rrf([[('b', 100), ('b', 90), ('a', 80)], [('a', 1)]])
        self.assertEqual(rows[0][0], 'a')
        self.assertAlmostEqual(dict(rows)['b'], 1/61)
        self.assertAlmostEqual(dict(rows)['a'], 1/63 + 1/61)

    def test_interpolation_calibrates_scales_and_empty_constant_lists(self):
        sparse = [('a', 1000), ('b', 500)]
        vector = [('b', .9), ('a', .8)]
        self.assertEqual(interpolate(sparse, vector, .7)[0][0], 'b')
        self.assertAlmostEqual(dict(interpolate(sparse, vector, .7))['b'], .7)
        self.assertEqual(interpolate([], [('a', .5)], .7), [('a', .7)])
        self.assertEqual(interpolate([], [], .7), [])

    def test_authored_graded_metrics_and_no_answer_are_not_conflated(self):
        relevance = {'a': 2, 'b': 1}
        result = metrics(['x', 'a', 'b'], relevance, 2)
        self.assertEqual(result['recall'], .5)
        self.assertEqual(result['mrr'], .5)
        self.assertAlmostEqual(result['ndcg'], (3/math.log2(3))/(3+1/math.log2(3)))
        no_answer = metrics(['x'], {}, 3)
        self.assertIsNone(no_answer['ndcg'])
        self.assertTrue(no_answer['false_positive'])
        self.assertFalse(metrics([], {}, 3)['false_positive'])
        with self.assertRaises(ValueError):
            metrics(['a', 'a'], relevance, 2)

    def test_word_budget_cannot_silently_skip_an_oversized_first_document(self):
        docs = {'a': {'text': 'one two three four'}, 'b': {'text': 'five'}}
        self.assertEqual(word_context(['a', 'b'], docs, 3), ([], 0))
        self.assertEqual(word_context(['b', 'a'], docs, 3), (['b'], 1))

    def test_aggregate_gain_can_hide_query_harm(self):
        def query(id, component, fusion):
            return {'id': id, 'answerable': True, 'methods': {
                'bm25': {'at_k': {'3': {'ndcg': component, 'recall': 1}}},
                'rrf': {'at_k': {'3': {'ndcg': fusion, 'recall': 1}}}}}
        diagnostic = paired([query('one', .2, .9), query('two', 1, .7)], 'rrf', 'bm25')
        self.assertGreater(diagnostic['mean_ndcg_delta'], 0)
        self.assertEqual(diagnostic['hurt_n'], 1)
        self.assertAlmostEqual(diagnostic['worst_ndcg_loss'], .3)

    def test_development_selection_refuses_test_or_empty_evidence(self):
        for rows in ([], [{'split': 'heldout'}]):
            with self.assertRaisesRegex(ValueError, 'development'):
                select_from_development(rows)


class AdapterTests(unittest.TestCase):
    def test_actual_public_handoff_helpers_and_frozen_hashes(self):
        adapter = b.FixtureAdapter()
        self.assertEqual(len(adapter.documents), 24)
        self.assertEqual(adapter.handoff.VERSION, '1.0')
        row = adapter.documents[0]
        suggestion = adapter.suggestions([row['id']])[0]
        self.assertEqual(suggestion['sha256'], b.digest(adapter.raw[row['path']]))
        for bad in ('../escape.md', '/absolute.md', 'docs/../escape.md'):
            with self.assertRaises(ValueError):
                adapter.handoff.within(adapter.base, bad, markdown=True)

    def test_changed_fixture_is_refused_before_retrieval(self):
        real_read = b.load_handoff
        module = real_read()
        actual_read = module.read_bytes
        def corrupted(path, limit):
            raw = actual_read(path, limit)
            return raw + b' ' if Path(path).name == 'heldout.json' else raw
        with patch.object(module, 'read_bytes', side_effect=corrupted), patch.object(b, 'load_handoff', return_value=module):
            with self.assertRaisesRegex(ValueError, 'digest mismatch'):
                b.FixtureAdapter()

    def test_selection_finishes_before_any_heldout_labels_are_parsed(self):
        actual_select = b.select_from_development
        actual_queries = b.FixtureAdapter.queries
        selected = []
        def select(rows):
            policy = actual_select(rows)
            selected.append(policy)
            return policy
        def queries(adapter, split):
            if split == 'heldout':
                self.assertTrue(selected, 'Heldout labels opened before selection')
            return actual_queries(adapter, split)
        with patch.object(b, 'select_from_development', side_effect=select), patch.object(b.FixtureAdapter, 'queries', queries):
            result = b.benchmark(b.FixtureAdapter())
        self.assertEqual(result['selection'], selected[0])
        self.assertTrue(all(id.startswith('d-') for id in result['selection']['query_ids']))

    def test_human_and_json_entrypoints_share_validation_and_rankings_after_restart(self):
        command = [sys.executable, '-B', str(b.ROOT/'benchmark.py')]
        request = {'operation': 'query', 'query_id': 'd-exact-1'}
        direct = b.execute(request)
        agent = subprocess.run(command+['json'], input=json.dumps(request), text=True,
                               capture_output=True, timeout=30, check=True)
        self.assertEqual(without_timings(direct), without_timings(json.loads(agent.stdout)))
        human = subprocess.run(command+['query', 'd-exact-1'], text=True,
                               capture_output=True, timeout=30, check=True)
        self.assertEqual(human.stdout.strip(), b.human_display(direct))
        bad = subprocess.run(command+['json'], input='{"operation":"query","query_id":"unknown"}',
                             text=True, capture_output=True, timeout=30)
        self.assertEqual(bad.returncode, 2)
        self.assertEqual(json.loads(bad.stderr)['status'], 'REFUSED')

    def test_multiterm_scores_are_identical_across_process_hash_seeds(self):
        command = [sys.executable, '-B', str(b.ROOT/'benchmark.py'), 'json']
        request = json.dumps({'operation': 'query', 'query_id': 'd-noise-2'})
        outputs = []
        for seed in ('1', '2'):
            process = subprocess.run(command, input=request, text=True, capture_output=True,
                                     timeout=30, check=True, env=dict(os.environ, PYTHONHASHSEED=seed))
            outputs.append(without_timings(json.loads(process.stdout)))
        self.assertEqual(outputs[0], outputs[1])

    def test_output_scope_and_existing_evidence_are_refused_before_execution(self):
        for output in ('../escape.json', 'sub/file.json', 'README.md', '.hidden.json'):
            with self.assertRaises(ValueError):
                b.execute({'operation': 'benchmark', 'output': output})
        with tempfile.NamedTemporaryFile(dir=b.ROOT, suffix='.json') as existing:
            with self.assertRaisesRegex(ValueError, 'Existing output refused'):
                b.execute({'operation': 'benchmark', 'output': Path(existing.name).name})

    def test_duplicate_json_and_unexpected_authority_fields_refused(self):
        with self.assertRaises(ValueError):
            b.strict_json('{"operation":"query","operation":"benchmark"}')
        with self.assertRaises(ValueError):
            b.execute({'operation': 'query', 'query_id': 'd-exact-1', 'approved': True})
        with self.assertRaises(ValueError):
            b.strict_json('{"weight":NaN}')


if __name__ == '__main__':
    unittest.main()
