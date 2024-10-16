"""主训练脚本入口，调用各模块进行模型训练"""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/00_main.ipynb.

# %% auto 0
__all__ = ['config', 'cls_task', 'trainer']

# %% ../nbs/00_main.ipynb 5
from .core import ClassificationTask, ClassificationTaskConfig
config = ClassificationTaskConfig()
# config.learning_rate = 1e-1
# config.learning_rate = 1
config.learning_rate = 1e-3
# config.learning_rate = 3e-4
# config.learning_rate = 1e-6
config.dataset_config.batch_size = 64
cls_task = ClassificationTask(config)
cls_task.print_model_pretty()
import torch
# cls_task.cls_model = torch.compile(cls_task.cls_model, mode='reduce-overhead')
#  fullgraph=True

# %% ../nbs/00_main.ipynb 8
import lightning as L
from .utils import runs_path
from lightning.pytorch.callbacks.early_stopping import EarlyStopping
from lightning.pytorch.callbacks import ModelSummary, StochasticWeightAveraging, DeviceStatsMonitor
from lightning.pytorch.loggers import TensorBoardLogger, CSVLogger

trainer = L.Trainer(default_root_dir=runs_path, enable_checkpointing=True, 
                    enable_model_summary=True, 
                    num_sanity_val_steps=2, # 防止 val 在训了好久train才发现崩溃
                    callbacks=[
                        # EarlyStopping(monitor="val_loss", mode="min")
                        EarlyStopping(monitor="val_acc1", mode="max", check_finite=True, 
                                      patience=5, 
                                      check_on_train_epoch_end=False,  # check on validation end
                                      verbose=True),
                        ModelSummary(max_depth=3),
                        # StochasticWeightAveraging(swa_lrs=1e-2), 
                        DeviceStatsMonitor(cpu_stats=True)
                               ]
                    
                    # , gradient_clip_val=1.0, gradient_clip_algorithm="value"
                    , logger=[TensorBoardLogger(save_dir=runs_path/"tensorboard"), CSVLogger(save_dir=runs_path)]
                    # , profiler="simple"
                    # , fast_dev_run=True
                    # limit_train_batches=10, limit_val_batches=5
                    # strategy="ddp", accelerator="gpu", devices=4
                    )
trainer.fit(cls_task, datamodule=cls_task.lit_data)
