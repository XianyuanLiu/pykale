"""This example is about domain adaptation for action recognition, using PyTorch Lightning.

Reference: https://github.com/thuml/CDAN/blob/master/pytorch/train_image.py
"""

import argparse
import logging
import os

import pytorch_lightning as pl
from pytorch_lightning import loggers as pl_loggers
from pytorch_lightning.callbacks.early_stopping import EarlyStopping
from pytorch_lightning.callbacks import LearningRateMonitor

from config import get_cfg_defaults
from model import get_model
from kale.loaddata.action_multi_domain import VideoMultiDomainDatasets
from kale.loaddata.video_access import VideoDataset
from kale.utils.csv_logger import setup_logger
from kale.utils.seed import set_seed


def arg_parse():
    """Parsing arguments"""
    parser = argparse.ArgumentParser(description="Domain Adversarial Networks on Action Datasets")
    parser.add_argument("--cfg", required=True, help="path to config file", type=str)
    parser.add_argument("--gpus", default="0", help="gpu id(s) to use", type=str)
    parser.add_argument("--resume", default="", type=str)
    parser.add_argument("--ckpt", default="", type=str)
    args = parser.parse_args()
    return args


def main():
    """The main for this domain adaptation example, showing the workflow"""
    args = arg_parse()

    # ---- setup configs ----
    cfg = get_cfg_defaults()
    cfg.merge_from_file(args.cfg)
    cfg.freeze()
    print(cfg)

    # ---- setup output ----
    os.makedirs(cfg.OUTPUT.DIR, exist_ok=True)
    format_str = "@%(asctime)s %(name)s [%(levelname)s] - (%(message)s)"
    logging.basicConfig(format=format_str)
    # ---- setup dataset ----
    seed = cfg.SOLVER.SEED
    source, target, num_classes = VideoDataset.get_source_target(VideoDataset(cfg.DATASET.SOURCE.upper()),
                                                                 VideoDataset(cfg.DATASET.TARGET.upper()),
                                                                 seed,
                                                                 cfg)
    dataset = VideoMultiDomainDatasets(source, target,
                                       image_modality=cfg.DATASET.IMAGE_MODALITY,
                                       seed=seed,
                                       config_weight_type=cfg.DATASET.WEIGHT_TYPE,
                                       config_size_type=cfg.DATASET.SIZE_TYPE)

    # ---- setup model and logger ----
    model, train_params = get_model(cfg, dataset, num_classes)
    trainer = pl.Trainer(
        # progress_bar_refresh_rate=cfg.OUTPUT.PB_FRESH,  # in steps
        resume_from_checkpoint=args.ckpt,
        gpus=args.gpus,
    )

    # test scores
    trainer.test(model=model)


if __name__ == "__main__":
    main()