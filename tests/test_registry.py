import os
import shutil
import unittest

from transformers import BertModel

from uner.metainfo import Models
from uner.models import *  # noqa
from uner.models.base import Model
from uner.models.sequence_labeling_model import SequenceLabelingModel
from uner.modules.encoders import Encoder, NeZhaModel


class TestRegistry(unittest.TestCase):

    def setUp(self):
        self.bert_config_file = os.path.join('tests', 'resources', 'configs',
                                             'bert.yaml')
        self.nezha_config_file = os.path.join('tests', 'resources', 'configs',
                                              'nezha.yaml')

    def test_get_encoder(self):
        """可以不指定配置文件并初始化一个Encoder
        """
        model = Encoder.from_config(model_name_or_path='bert-base-uncased')
        self.assertTrue(isinstance(model, BertModel))

    def test_get_encoder_from_cfg_bert(self):
        """可以指定配置文件初始化一个Encoder，本例中配置文件中存在model_name_or_path参数
        """
        model = Encoder.from_config(cfg_dict_or_path=self.bert_config_file)
        self.assertTrue(isinstance(model, BertModel))

    def test_get_encoder_from_cfg_nezha(self):
        """可以指定配置文件初始化一个Encoder，本例中配置文件中存在type和model_name_or_path参数
        """
        model = Encoder.from_config(cfg_dict_or_path=self.nezha_config_file)
        self.assertTrue(isinstance(model, NeZhaModel))

    def test_get_model(self):
        """可以不配置文件初始化一个模型
        """
        model = Model.from_config(
            type=Models.sequence_labeling_model,
            num_labels=2,
            encoder={'model_name_or_path': 'bert-base-uncased'})
        self.assertTrue(isinstance(model, SequenceLabelingModel))

    def test_get_model_from_cfg_bert(self):
        """可以指定配置文件初始化一个模型，本例中配置文件中存在model_name_or_path参数
        """
        model = Model.from_config(cfg_dict_or_path=self.bert_config_file)
        self.assertTrue(isinstance(model, SequenceLabelingModel))
        self.assertTrue(isinstance(model.encoder, BertModel))


if __name__ == '__main__':
    unittest.main()