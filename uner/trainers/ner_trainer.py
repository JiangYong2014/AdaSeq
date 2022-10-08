import os
import random
from typing import Callable, Mapping, Optional, Tuple, Union

import torch
from modelscope.preprocessors.base import Preprocessor
from modelscope.trainers.builder import TRAINERS
from modelscope.trainers.optimizer.builder import OPTIMIZERS
from modelscope.utils.config import ConfigDict
from modelscope.utils.registry import build_from_cfg, default_group
from torch import nn

from uner.metainfo import Trainers
from uner.models.base import Model
from uner.utils.common_utils import has_keys
from uner.utils.data_utils import gen_label2id, get_labels
from .default_trainer import DefaultTrainer


@TRAINERS.register_module(module_name=Trainers.ner_trainer)
class NERTrainer(DefaultTrainer):

    def after_build_dataset(self, **kwargs):
        # labels
        if 'label2id' in kwargs:
            self.label2id = kwargs.pop('label2id')
        elif 'train_dataset' in kwargs and kwargs[
                'train_dataset'] is not None and has_keys(
                    self.cfg, 'preprocessor', 'type'):
            labels = get_labels(kwargs.pop('train_dataset'))
            self.label2id = gen_label2id(
                labels, mode=self.cfg.preprocessor.type)
        else:
            raise ValueError('label2id must be set!')

    def after_build_preprocessor(self, **kwargs):
        # update label2id
        if self.train_preprocessor is not None:
            self.label2id = self.train_preprocessor.label2id
        elif self.eval_preprocessor is not None:
            self.label2id = self.eval_preprocessor.label2id

        self.id2label = {v: k for k, v in self.label2id.items()}
        self.logger.info('label2id:', self.label2id)

    def build_preprocessor(self,
                           **kwargs) -> Tuple[Preprocessor, Preprocessor]:
        return super().build_preprocessor(label2id=self.label2id, **kwargs)

    def build_model(self) -> nn.Module:
        cfg = self.cfg.model
        cfg['num_labels'] = len(self.label2id)
        return Model.from_config(cfg)

    @staticmethod
    def build_optimizer(model: nn.Module,
                        cfg: ConfigDict,
                        default_args: dict = None):
        if hasattr(model, 'module'):
            model = model.module
        if default_args is None:
            default_args = {}
        if 'crf_lr' in cfg:
            finetune_parameters = [
                v for k, v in model.named_parameters()
                if v.requires_grad and 'crf' not in k
            ]
            transition_parameters = [
                v for k, v in model.named_parameters()
                if v.requires_grad and 'crf' in k
            ]
            default_args['params'] = [{
                'params': finetune_parameters
            }, {
                'params': transition_parameters,
                'lr': cfg.pop('crf_lr')
            }]
        else:
            default_args['params'] = model.parameters()
        return build_from_cfg(
            cfg,
            OPTIMIZERS,
            group_key=default_group,
            default_args=default_args)
