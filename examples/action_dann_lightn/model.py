"""
Define the learning model and configure training parameters.
References from https://github.com/criteo-research/pytorch-ada/blob/master/adalib/ada/utils/experimentation.py
"""
# Author: Haiping Lu & Xianyuan Liu
# Initial Date: 7 December 2020

from copy import deepcopy

import torch

from kale.embed.video_cnn.i3d import InceptionI3d
from kale.embed.video_cnn.res3d import r3d_18, r2plus1d_18, mc3_18
from kale.predict.class_domain_nets import ClassNetSmallImage, \
    DomainNetSmallImage
import kale.pipeline.domain_adapter as domain_adapter


def get_config(cfg):
    """
    Sets the hyper parameter for the optimizer and experiment using the config file

    Args:
        cfg: A YACS config object.
    """
    config_params = {
        "train_params": {
            "adapt_lambda": cfg.SOLVER.AD_LAMBDA,
            "adapt_lr": cfg.SOLVER.AD_LR,
            "lambda_init": cfg.SOLVER.INIT_LAMBDA,
            "nb_adapt_epochs": cfg.SOLVER.MAX_EPOCHS,
            "nb_init_epochs": cfg.SOLVER.MIN_EPOCHS,
            "init_lr": cfg.SOLVER.BASE_LR,
            "batch_size": cfg.SOLVER.TRAIN_BATCH_SIZE,
            "optimizer": {
                "type": cfg.SOLVER.TYPE,
                "optim_params": {
                    "momentum": cfg.SOLVER.MOMENTUM,
                    "weight_decay": cfg.SOLVER.WEIGHT_DECAY,
                    "nesterov": cfg.SOLVER.NESTEROV
                }
            }
        },
        "data_params": {
            # "dataset_group": cfg.DATASET.NAME,
            "dataset_name": cfg.DATASET.SOURCE + '2' + cfg.DATASET.TARGET,
            "source": cfg.DATASET.SOURCE,
            "target": cfg.DATASET.TARGET,
            "size_type": cfg.DATASET.SIZE_TYPE,
            "weight_type": cfg.DATASET.WEIGHT_TYPE
        }
    }
    return config_params


def get_feat_extractor(model_name, num_classes, num_channels):
    if model_name == 'I3D':
        model = InceptionI3d()
        model.load_state_dict(torch.load('./models/rgb_imagenet.pt'))
        # model.replace_logits(num_classes)
        feature_dim = 1024
    elif model_name == 'R3D_18':
        model = r3d_18(pretrained=True)
        feature_dim = 512
    elif model_name == 'R2PLUS1D_18':
        model = r2plus1d_18(pretrained=True)
        feature_dim = 512
    elif model_name == 'MC3_18':
        model = mc3_18(pretrained=True)
        feature_dim = 512
    else:
        raise ValueError("Unsupported model: {}".format(model_name))
    return model, feature_dim


# Based on https://github.com/criteo-research/pytorch-ada/blob/master/adalib/ada/utils/experimentation.py
def get_model(cfg, dataset, num_channels):
    """
    Builds and returns a model and associated hyper parameters according to the config object passed.

    Args:
        cfg: A YACS config object.
        dataset: A multi domain dataset consisting of source and target datasets.
        num_channels: The number of image channels.        
    """

    # setup feature extractor
    feature_network, feature_dim = get_feat_extractor(cfg.MODEL.METHOD.upper(), cfg.DATASET.NUM_CLASSES, num_channels)
    # setup classifier
    classifier_network = ClassNetSmallImage(feature_dim, cfg.DATASET.NUM_CLASSES)

    config_params = get_config(cfg)
    train_params = config_params["train_params"]
    train_params_local = deepcopy(train_params)
    method_params = {}

    method = domain_adapter.Method(cfg.DAN.METHOD)

    if method.is_mmd_method():
        model = domain_adapter.create_mmd_based(
            method=method,
            dataset=dataset,
            feature_extractor=feature_network,
            task_classifier=classifier_network,
            **method_params,
            **train_params_local,
        )
    else:
        critic_input_size = feature_dim
        # setup critic network
        if method.is_cdan_method():
            if cfg.DAN.USERANDOM:
                critic_input_size = cfg.DAN.RANDOM_DIM
            else:
                critic_input_size = feature_dim * cfg.DATASET.NUM_CLASSES
        critic_network = DomainNetSmallImage(critic_input_size)

        if cfg.DAN.METHOD == 'CDAN':
            method_params["use_random"] = cfg.DAN.USERANDOM

        # The following calls kale.loaddata.dataset_access for the first time
        model = domain_adapter.create_dann_like(
            method=method,
            dataset=dataset,
            feature_extractor=feature_network,
            task_classifier=classifier_network,
            critic=critic_network,
            **method_params,
            **train_params_local,
        )

    return model, train_params
