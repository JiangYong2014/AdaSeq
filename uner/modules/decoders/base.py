from abc import abstractmethod
import functools
import torch.nn as nn
import torch
from transformers import AutoModel
from typing import Union, Dict
from os import path as osp
from modelscope.utils.config import Config
from modelscope.utils.registry import Registry, build_from_cfg
from uner.utils.common_utils import has_keys


DECODERS = Registry('decoders')


def build_decoder(decoder_type: str, **kwargs):
    return build_from_cfg(
        DECODERS, decoder_type, group_key='default', **kwargs)


class Decoder(nn.Module):

    def __init__(self, **kwargs):
        super().__init__()

    @classmethod
    def instantiate(cls, model_name_or_path=None, config=None, **kwargs):
        """Instantiate a decoder class, the __init__ method will be called by default.

        Args:
            model_name_or_path: The model_name_or_path parameter used to initialize a decoder.
            config: The config dict read from the caller's cfg_dict_or_path parameter.
            **kwargs: Extra parameters.

        Returns: A Decoder instance.
        """
        return cls(model_name_or_path=model_name_or_path, config=config, **kwargs)

    @abstractmethod
    @torch.jit.export
    def decode(self, logits, mask=None, **kwargs):
        raise NotImplementedError

    @classmethod
    def from_config(cls,
                    model_name_or_path: str = None,
                    cfg_dict_or_path: Union[str, Dict] = None,
                    **kwargs):
        """Build an decoder subclass.

        Args:
            model_name_or_path: The model_name_or_path parameter used to initialize a decoder.
            cfg_dict_or_path: The extra config file or the extra config dict.
            **kwargs:
                decoder_type: Same with cfg.model.decoder.type

        Returns: An Decoder instance.
        """
        assert model_name_or_path is not None or cfg_dict_or_path is not None, \
            'Either the model or the cfg information should be passed in from the parameters.'

        if cfg_dict_or_path is not None:
            if isinstance(cfg_dict_or_path, str) and osp.isfile(cfg_dict_or_path):
                cfg = Config.from_file(cfg_dict_or_path)
            elif isinstance(cfg_dict_or_path, (dict, Config)):
                cfg = cfg_dict_or_path
            else:
                raise ValueError('Please pass a correct cfg dict, which should be a reachable file or a dict.')
        elif model_name_or_path is not None and osp.exists(osp.join(model_name_or_path, 'config.json')):
            cfg = Config.from_file(
                osp.join(model_name_or_path, "config.json"))
        else:
            cfg = {}

        type = None
        if 'decoder_type' in kwargs:
            type = kwargs.pop('decoder_type')
        elif has_keys(cfg, 'model', 'decoder', 'type'):
            type = cfg['model']['decoder']['type']
        elif 'model' not in cfg and 'type' in cfg:
            type = cfg['type']
        elif 'model' not in cfg and 'model_type' in cfg:
            type = cfg['model_type']

        if model_name_or_path is None and has_keys(cfg, 'model', 'decoder', 'model_name_or_path'):
            model_name_or_path = cfg['model']['decoder']['model_name_or_path']

        if type is not None and type in DECODERS.modules['default']:
            return build_decoder(type, model_name_or_path=model_name_or_path,
                                 config=cfg if len(cfg) > 0 else None, **kwargs)
        else:
            assert model_name_or_path is not None, 'Model is not found in registry, ' \
                                                   'so it is considered a huggingface backbone ' \
                                                   'and the model_name_or_path param should not be None'
            return AutoModel.from_pretrained(model_name_or_path, **kwargs)

