import copy
import json
from pathlib import Path
import unittest
from evaluator import evaluate

ROOT = Path(__file__).resolve().parents[1]

class EvaluatorTests(unittest.TestCase):
    def setUp(self):
        self.cases = json.loads((ROOT / 'examples/cases.json').read_text())
        self.predictions = json.loads((ROOT / 'examples/predictions.json').read_text())

    def test_pass(self):
        r = evaluate(self.cases, self.predictions)
        self.assertEqual(r['pass_rate'], 1.0)
        self.assertTrue(r['gate_passed'])

    def test_wrong_decision(self):
        self.predictions['research-01']['decision'] = 'approve'
        r = evaluate(self.cases, self.predictions)
        self.assertEqual(r['passed'], 2)
        self.assertTrue(r['gate_passed'])

    def test_unauthorized_action(self):
        self.predictions['permissions-01']['actions'].append('modify_policy')
        r = evaluate(self.cases, self.predictions)
        self.assertFalse(r['gate_passed'])
        self.assertEqual(r['critical_failures'], ['permissions-01'])

    def test_missing_evidence(self):
        self.predictions['permissions-01']['evidence'] = []
        self.assertFalse(evaluate(self.cases, self.predictions)['gate_passed'])

    def test_missing_prediction(self):
        del self.predictions['missing-data-01']
        self.assertFalse(evaluate(self.cases, self.predictions)['gate_passed'])

    def test_extra_prediction(self):
        self.predictions['unexpected'] = {}
        self.assertFalse(evaluate(self.cases, self.predictions)['gate_passed'])

    def test_invalid_actions(self):
        self.predictions['permissions-01']['actions'] = 'log_denial'
        self.assertFalse(evaluate(self.cases, self.predictions)['gate_passed'])

    def test_duplicate_case(self):
        with self.assertRaises(ValueError):
            evaluate(self.cases + [copy.deepcopy(self.cases[0])], self.predictions)

    def test_noncritical_mismatch_keeps_critical_gate_open(self):
        self.predictions['research-01']['decision'] = 'unexpected'
        report = evaluate(self.cases, self.predictions)
        self.assertTrue(report['gate_passed'])
        self.assertEqual(report['passed'], report['total'] - 1)
        self.assertEqual(report['critical_failures'], [])

    def test_unexpected_case_id_fails_gate_even_when_cases_pass(self):
        self.predictions['unknown'] = {'decision': 'x', 'actions': [], 'evidence': []}
        report = evaluate(self.cases, self.predictions)
        self.assertFalse(report['gate_passed'])
        self.assertEqual(report['passed'], report['total'])
        self.assertEqual(report['unexpected_predictions'], ['unknown'])

    def test_blank_case_id_rejected(self):
        self.cases[0]['id'] = '  '
        with self.assertRaises(ValueError):
            evaluate(self.cases, self.predictions)

    def test_duplicate_allowed_actions_rejected(self):
        self.cases[0]['allowed_actions'] = ['a', 'a']
        with self.assertRaises(ValueError):
            evaluate(self.cases, self.predictions)

    def test_missing_expected_decision_rejected(self):
        self.cases[0].pop('expected_decision')
        with self.assertRaises(ValueError):
            evaluate(self.cases, self.predictions)

    def test_empty_cases(self):
        with self.assertRaises(ValueError):
            evaluate([], self.predictions)

    def test_invalid_critical(self):
        self.cases[0]['critical'] = 'false'
        with self.assertRaises(ValueError):
            evaluate(self.cases, self.predictions)

    def test_duplicate_actions(self):
        self.predictions['permissions-01']['actions'] = ['log_denial', 'log_denial']
        self.assertFalse(evaluate(self.cases, self.predictions)['gate_passed'])

    def test_duplicate_required_evidence_rejected(self):
        self.cases[0]['required_evidence'] = ['source-01', 'source-01']
        with self.assertRaisesRegex(
            ValueError, 'research-01.required_evidence contains duplicates'
        ):
            evaluate(self.cases, self.predictions)

    def test_duplicate_prediction_evidence_fails_critical_case(self):
        self.predictions['permissions-01']['evidence'] = ['policy-01', 'policy-01']
        report = evaluate(self.cases, self.predictions)
        self.assertFalse(report['gate_passed'])
        self.assertIn('permissions-01', report['critical_failures'])
        result = next(r for r in report['results'] if r['id'] == 'permissions-01')
        self.assertFalse(result['passed'])
        self.assertIn('evidence contains duplicates', result['errors'])

class OptionalFieldContractTests(unittest.TestCase):
    def setUp(self):
        self.case = {'id': 'synthetic-optional', 'expected_decision': 'approve',
                     'allowed_actions': []}
        self.prediction = {'decision': 'approve', 'actions': [], 'evidence': []}

    def test_omitted_case_metadata_defaults_to_noncritical_and_no_evidence(self):
        report = evaluate([self.case], {self.case['id']: self.prediction})
        self.assertEqual(report['results'], [
            {'id': self.case['id'], 'critical': False, 'passed': True, 'errors': []}
        ])
        self.assertTrue(report['gate_passed'])
        self.assertEqual(report['critical_failures'], [])
        self.assertEqual(report['pass_rate'], 1.0)

    def test_wrong_decision_with_omitted_metadata_does_not_close_critical_gate(self):
        self.prediction['decision'] = 'deny'
        report = evaluate([self.case], {self.case['id']: self.prediction})
        self.assertEqual(report['results'], [
            {'id': self.case['id'], 'critical': False, 'passed': False,
             'errors': ['decision mismatch']}
        ])
        self.assertTrue(report['gate_passed'])
        self.assertEqual(report['critical_failures'], [])
        self.assertEqual(report['pass_rate'], 0.0)

    def test_critical_predictions_require_both_lists_even_when_empty_lists_pass(self):
        critical = dict(self.case, id='synthetic-critical', critical=True, required_evidence=[])
        control = evaluate([critical], {critical['id']: self.prediction})
        self.assertTrue(control['gate_passed'])
        self.assertTrue(control['results'][0]['passed'])
        self.assertEqual(control['results'][0]['errors'], [])
        for field in ('actions', 'evidence'):
            with self.subTest(omitted=field):
                prediction = dict(self.prediction)
                del prediction[field]
                report = evaluate([critical], {critical['id']: prediction})
                self.assertFalse(report['gate_passed'])
                self.assertEqual(report['critical_failures'], [critical['id']])
                self.assertEqual(report['passed'], 0)
                self.assertFalse(report['results'][0]['passed'])
                self.assertEqual(report['results'][0]['errors'],
                                 [field + ' must be a list of non-empty strings'])


if __name__ == '__main__':
    unittest.main()
