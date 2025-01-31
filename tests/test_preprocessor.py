import unittest

import numpy as np
from modelscope.models.nlp.structbert import SbertTokenizer
from modelscope.preprocessors.builder import build_preprocessor

from adaseq.data.preprocessors import NLPPreprocessor


class TestPreprocessor(unittest.TestCase):
    def setUp(self):
        self.setUp_ner_examples()
        self.setUp_typing_examples()

    def setUp_ner_examples(self):
        self.ner_input1 = {
            'tokens': 'EU rejects German call to boycott British lamb .'.split(),
            'spans': [
                {'start': 0, 'end': 1, 'type': 'ORG'},
                {'start': 2, 'end': 3, 'type': 'MISC'},
                {'start': 6, 'end': 7, 'type': 'MISC'},
            ],
        }
        self.ner_labels1 = ['O'] + [f'{a}-{b}' for a in 'BI' for b in ['LOC', 'MISC', 'ORG', 'PER']]
        self.ner_label2id1 = dict((v, k) for k, v in enumerate(self.ner_labels1))

        self.ner_labels1_bioes = ['O'] + [
            f'{a}-{b}' for a in 'BIES' for b in ['LOC', 'MISC', 'ORG', 'PER']
        ]
        self.ner_label2id1_bioes = dict((v, k) for k, v in enumerate(self.ner_labels1_bioes))

        self.ner_input2 = {
            'tokens': list('国正先生在我心中就是这样的一位学长。'),
            'spans': [{'start': 0, 'end': 2, 'type': 'PER'}],
        }
        self.ner_labels2 = ['O', 'B-PER', 'I-PER', 'B-ORG', 'I-ORG', 'B-LOC', 'I-LOC']
        self.ner_label2id2 = dict((v, k) for k, v in enumerate(self.ner_labels2))

        self.ner_labels3 = ['PER', 'ORG', 'LOC']
        self.ner_label2id3 = dict((v, k) for k, v in enumerate(self.ner_labels3))

    def test_bert_sequence_labeling_preprocessor(self):
        cfg = dict(
            type='sequence-labeling-preprocessor',
            model_dir='bert-base-cased',
            label2id=self.ner_label2id1,
        )
        preprocessor = build_preprocessor(cfg)
        output1 = preprocessor(self.ner_input1)
        self.assertEqual(
            output1['input_ids'],
            [101, 7270, 22961, 1528, 1840, 1106, 21423, 1418, 2495, 12913, 119, 102],
        )
        self.assertEqual(output1['attention_mask'], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
        self.assertEqual(output1['emission_mask'], [0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0])
        self.assertEqual(output1['label_ids'], [3, 0, 2, 0, 0, 0, 2, 0, 0])

    def test_bert_sequence_labeling_bioes_preprocessor(self):
        cfg = dict(
            type='sequence-labeling-preprocessor',
            model_dir='bert-base-cased',
            label2id=self.ner_label2id1_bioes,
        )
        preprocessor = build_preprocessor(cfg)
        output1 = preprocessor(self.ner_input1)
        self.assertEqual(
            output1['input_ids'],
            [101, 7270, 22961, 1528, 1840, 1106, 21423, 1418, 2495, 12913, 119, 102],
        )
        self.assertEqual(output1['attention_mask'], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
        self.assertEqual(output1['emission_mask'], [0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0])
        self.assertEqual(output1['label_ids'], [15, 0, 14, 0, 0, 0, 14, 0, 0])

    def test_lstm_sequence_labeling_preprocessor(self):
        cfg = dict(
            type='sequence-labeling-preprocessor',
            model_dir='pangda/word2vec-skip-gram-mixed-large-chinese',
            label2id=self.ner_label2id2,
            add_cls_sep=False,
        )
        preprocessor = build_preprocessor(cfg)
        output2 = preprocessor(self.ner_input2)
        self.assertEqual(
            output2['input_ids'],
            [217, 211, 286, 266, 8, 24, 391, 29, 41, 11, 42, 1391, 5, 16, 140, 352, 179, 6],
        )
        self.assertEqual(
            output2['attention_mask'], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        )
        self.assertEqual(
            output2['emission_mask'], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        )
        self.assertEqual(
            output2['label_ids'], [1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        )

    def test_bert_global_pointer_preprocessor(self):
        cfg = dict(
            type='global-pointer-preprocessor',
            model_dir='bert-base-cased',
            labels=None,
            label2id=self.ner_label2id3,
        )
        preprocessor = build_preprocessor(cfg)
        output2 = preprocessor(self.ner_input2)
        self.assertEqual(
            output2['input_ids'],
            [
                101,
                1004,
                1045,
                100,
                1056,
                100,
                100,
                1027,
                980,
                100,
                100,
                100,
                100,
                100,
                976,
                100,
                100,
                100,
                886,
                102,
            ],
        )
        self.assertEqual(
            output2['attention_mask'], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        )
        self.assertEqual(
            output2['offset_mapping'],
            [
                (0, 0),
                (0, 1),
                (1, 2),
                (2, 3),
                (3, 4),
                (4, 5),
                (5, 6),
                (6, 7),
                (7, 8),
                (8, 9),
                (9, 10),
                (10, 11),
                (11, 12),
                (12, 13),
                (13, 14),
                (14, 15),
                (15, 16),
                (16, 17),
                (17, 18),
                (0, 0),
            ],
        )
        expected_label_matrix = np.zeros((3, 20, 20))
        expected_label_matrix[0][1][2] = 1
        self.assertEqual((output2['label_matrix'] == expected_label_matrix).all(), True)

    def setUp_typing_examples(self):
        self.typing_input = {
            'tokens': list('国正先生在我心中就是这样的一位学长。'),
            'spans': [{'start': 0, 'end': 2, 'type': ['人名', '老师']}],
        }

        self.typing_labels = ['人名', '地名', '老师']
        self.typing_label2id = dict(zip(self.typing_labels, range(len(self.typing_labels))))

    def test_span_typing_preprocessor(self):
        cfg = dict(
            type='multilabel-span-typing-preprocessor',
            model_dir='bert-base-cased',
            labels=None,
            label2id=self.typing_label2id,
        )
        preprocessor = build_preprocessor(cfg)
        output = preprocessor(self.typing_input)
        self.assertEqual(
            output['input_ids'],
            [
                101,
                1004,
                1045,
                100,
                1056,
                100,
                100,
                1027,
                980,
                100,
                100,
                100,
                100,
                100,
                976,
                100,
                100,
                100,
                886,
                102,
            ],
        )
        self.assertEqual(
            output['attention_mask'], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        )
        self.assertEqual(
            output['offset_mapping'],
            [
                (0, 0),
                (0, 1),
                (1, 2),
                (2, 3),
                (3, 4),
                (4, 5),
                (5, 6),
                (6, 7),
                (7, 8),
                (8, 9),
                (9, 10),
                (10, 11),
                (11, 12),
                (12, 13),
                (13, 14),
                (14, 15),
                (15, 16),
                (16, 17),
                (17, 18),
                (0, 0),
            ],
        )
        self.assertEqual(output['mention_boundary'], [[1], [2]])
        self.assertEqual(output['type_ids'], [[1, 0, 1]])

    def test_load_modelscope_tokenizer(self):
        processor = NLPPreprocessor(model_dir='damo/nlp_structbert_backbone_tiny_std')
        self.assertTrue(isinstance(processor.tokenizer, SbertTokenizer))


if __name__ == '__main__':
    unittest.main()
