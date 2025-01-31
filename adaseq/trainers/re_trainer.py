# Copyright (c) Alibaba, Inc. and its affiliates.
from typing import Tuple

from modelscope.preprocessors.base import Preprocessor
from modelscope.trainers.builder import TRAINERS
from modelscope.trainers.optimizer.builder import OPTIMIZERS
from modelscope.utils.config import ConfigDict
from modelscope.utils.registry import build_from_cfg, default_group
from torch import nn

from adaseq.metainfo import Trainers
from adaseq.models.base import Model
from adaseq.utils.common_utils import has_keys
from adaseq.utils.data_utils import get_labels

from .default_trainer import DefaultTrainer


@TRAINERS.register_module(module_name=Trainers.re_trainer)
class RETrainer(DefaultTrainer):
    """Trainer for RE task"""

    def after_build_dataset(self, **kwargs):
        """Collect labels from datasets and create label to id mapping"""
        # get label info from dataset
        self.labels = None
        self.label2id = None
        if 'label2id' in kwargs:
            self.label2id = kwargs.pop('label2id')
        elif (
            'train_dataset' in kwargs
            and kwargs['train_dataset'] is not None
            and has_keys(self.cfg, 'preprocessor', 'type')
        ):
            self.labels = get_labels(kwargs.pop('train_dataset'))
        else:
            raise ValueError('label2id must be set!')

    def after_build_preprocessor(self, **kwargs):
        """Update label2id, since label set was exteded. e.g., B-X->S-X"""
        if self.train_preprocessor is not None:
            self.label2id = self.train_preprocessor.label2id
        elif self.eval_preprocessor is not None:
            self.label2id = self.eval_preprocessor.label2id

        self.id2label = {v: k for k, v in self.label2id.items()}
        self.logger.info('label2id:', self.label2id)

    def build_preprocessor(self, **kwargs) -> Tuple[Preprocessor, Preprocessor]:
        """Build preprocessor with labels and label2id"""
        return super().build_preprocessor(labels=self.labels, label2id=self.label2id, **kwargs)

    def build_model(self) -> nn.Module:
        """Build model with labels"""
        self.cfg.model['num_labels'] = len(self.label2id)
        return Model.from_config(self.cfg)

    @staticmethod
    def build_optimizer(model: nn.Module, cfg: ConfigDict, default_args: dict = None):
        """Build optimizer with layer-wise learning rate"""
        if hasattr(model, 'module'):
            model = model.module
        if default_args is None:
            default_args = {}
        if 'classifier_lr' in cfg:
            finetune_parameters = [
                v for k, v in model.named_parameters() if v.requires_grad and 'encoder' in k
            ]
            classifier_parameters = [
                v for k, v in model.named_parameters() if v.requires_grad and 'encoder' not in k
            ]
            default_args['params'] = [
                {'params': finetune_parameters},
                {'params': classifier_parameters, 'lr': cfg.pop('classifier_lr')},
            ]
        else:
            default_args['params'] = model.parameters()
        return build_from_cfg(cfg, OPTIMIZERS, group_key=default_group, default_args=default_args)
