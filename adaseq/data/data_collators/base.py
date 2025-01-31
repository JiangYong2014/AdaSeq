# Copyright (c) Alibaba, Inc. and its affiliates.
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import torch
from modelscope.utils.config import ConfigDict
from modelscope.utils.registry import Registry, build_from_cfg, default_group
from transformers import PreTrainedTokenizerBase

from adaseq.metainfo import DataCollators

DATA_COLLATORS = Registry('data_collators')


def build_data_collator(
    tokenizer: PreTrainedTokenizerBase, cfg: ConfigDict, default_args: Optional[dict] = None
):
    """build data collator from config."""
    if default_args is None:
        default_args = {}
    default_args['tokenizer'] = tokenizer
    return build_from_cfg(cfg, DATA_COLLATORS, group_key=default_group, default_args=default_args)


class DataBatch(Mapping):
    """represent a data batch, support `tensorize` function."""

    def __init__(self, batch, keep_fields=[]):
        self.keep_fields = keep_fields
        # modelscope/utils/data_utils.py: 17 会调这个 __init__,
        # 传入参数只有dict类型的batch, 但是value其实都是tensorize好的，
        # 所以不需要再做一次。
        if len(keep_fields) == 0:
            if isinstance(batch, tuple):
                batch = dict(batch)
            self.batch = batch
        else:
            self.batch = self.tensorize(batch)

    def __repr__(self):
        return str(self.batch)

    def __getitem__(self, key):
        return self.batch.get(key, None)

    def __contains__(self, key):
        return key in self.batch

    def __iter__(self):
        return iter(self.batch)

    def __len__(self):
        return len(self.batch)

    def tensorize(self, batch):
        """convert all possible fields to tensor."""

        if isinstance(batch, tuple):
            return dict(batch)
        return {
            k: torch.tensor(v, dtype=torch.int64 if not k.endswith('mask') else torch.bool)
            if k not in self.keep_fields
            else v
            for k, v in batch.items()
        }

    def to(self, device):
        """move to device"""
        self.batch = {
            k: v.to(device) if k not in [self.token_field] else v for k, v in self.batch.items()
        }


@DATA_COLLATORS.register_module(module_name=DataCollators.data_collator_with_padding)
@dataclass
class DataCollatorWithPadding:
    """
    A `DataCollator` support padding some fields to same length.
    Only padding encoder related fields: input_ids, token_type_ids, mask
    """

    tokenizer: PreTrainedTokenizerBase

    def __init__(self, tokenizer, **kwargs):
        self.tokenizer = tokenizer
        self.keep_fields = [
            'tokens',
            'offset_mapping',
            'reverse_offset_mapping',
        ]
        self.keep_fields.extend([f'origin_{f}' for f in self.keep_fields])

    def padding_token(
        self,
        batch: Dict[str, Any],
        fields: List[str],
        batch_size: int,
        max_length: int,
        padding_side: str,
    ) -> Dict[str, Any]:
        """pad token related fields (hf.transformers style)"""
        for i in range(batch_size):
            for field in fields:
                difference = max_length - len(batch[field][i])
                if difference > 0:
                    if field.endswith('input_ids'):
                        pad_id = self.tokenizer.pad_token_id
                    elif field.endswith('token_type_ids'):
                        pad_id = self.tokenizer.pad_token_type_id
                    elif field.endswith('mask'):
                        pad_id = 0
                    else:
                        continue

                    if padding_side == 'right':
                        batch[field][i] = batch[field][i] + [pad_id] * difference
                    elif padding_side == 'left':
                        batch[field][i] = [pad_id] * difference + batch[field][i]
                    else:
                        raise ValueError('Invalid padding strategy:' + str(self.padding_side))
        return batch

    def padding(
        self,
        batch: Dict[str, Any],
        fields: List[str],
        batch_size: int,
        max_length: int,
        padding_side: str,
    ) -> Dict[str, Any]:
        """pad other fields."""
        return batch

    def __call__(self, features: List[Dict[str, Any]]) -> DataBatch:
        """pad list of instances to batch"""
        batch_size = len(features)
        fields = features[0].keys()
        batch = {key: [example[key] for example in features] for key in fields}

        input_ids_field = 'input_ids' if 'ext_input_ids' not in fields else 'ext_input_ids'
        max_length = max([len(input_ids) for input_ids in batch[input_ids_field]])
        padding_side = self.tokenizer.padding_side
        padded_batch = self.padding_token(batch, fields, batch_size, max_length, padding_side)
        padded_batch = self.padding(padded_batch, fields, batch_size, max_length, padding_side)
        batch = DataBatch(padded_batch, self.keep_fields)
        return batch
