import unittest
from types import SimpleNamespace
from app.services.retrieval import rank_articles
from evaluation.run import evaluate, summarize, write_review_template
from pathlib import Path
from tempfile import TemporaryDirectory


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        self.articles = [SimpleNamespace(id=1, title='Kết nối Wi-Fi', content='Kiểm tra mạng wifi'),
                         SimpleNamespace(id=2, title='Máy in', content='Kiểm tra hàng đợi in')]

    def test_accents_and_wifi_spelling(self):
        for question in ('kết nối wifi', 'ket noi wi-fi', 'ket noi wi fi'):
            self.assertEqual(rank_articles(question, self.articles)[0].id, 1)

    def test_no_overlap_or_empty_input(self):
        for question in ('', 'và là của', 'xyz987'):
            self.assertEqual(rank_articles(question, self.articles), [])
        self.assertEqual(rank_articles('wifi', []), [])

    def test_baseline_and_limit(self):
        self.assertEqual(rank_articles('máy in', self.articles, 'baseline')[0].id, 2)
        self.assertEqual(len(rank_articles('kiểm tra', self.articles, limit=1)), 1)
        with self.assertRaises(ValueError):
            rank_articles('wifi', self.articles, 'unknown')

    def test_evaluation_metrics_and_review_preservation(self):
        cases = [dict(id='A', question='wifi', relevant_ids=[1]),
                 dict(id='B', question='xyz987', relevant_ids=[])]
        summary = summarize(evaluate(self.articles, cases, 'bm25'))
        self.assertEqual(summary['hit_at_3'], 1)
        self.assertEqual(summary['negative_abstention_rate'], 1)
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'review.csv'
            path.write_text('human scores', encoding='utf-8')
            with self.assertRaises(FileExistsError):
                write_review_template(path, cases)
            self.assertEqual(path.read_text(encoding='utf-8'), 'human scores')
