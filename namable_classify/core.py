"""主要定义与任务相关的核心组件和配置"""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/00_core.ipynb.

# %% auto 0
__all__ = ['ClassificationModelConfig', 'HuggingfaceModel', 'ClassificationTaskConfig', 'ClassificationTask']

# %% ../nbs/00_core.ipynb 5
import os
os.environ['HF_ENDPOINT'] = "https://hf-mirror.com" # TODO this is optional for Foreigners

# %% ../nbs/00_core.ipynb 7
from pydantic import BaseModel
class ClassificationModelConfig(BaseModel):
    provider: str = "huggingface"
    checkpoint: str = "google/vit-base-patch16-224-in21k" # TODO 支持 hf  timm torch
    head_strategy: str = "linear"
    num_of_classes: int = -1
    
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from transformers import AutoModel, AutoConfig, ViTModel, ViTConfig
from transformers import AutoImageProcessor, BitImageProcessor, ViTImageProcessor

class HuggingfaceModel(nn.Module):
    """Some Information about HuggingfaceModel"""
    def __init__(self, config : ClassificationModelConfig, forward_with_hf_image_preprocessor=False):
        super().__init__()
        # self.image_preprocessor = BitImageProcessor.from_pretrained(config.model_checkpoint, use_fast=True)
        self.image_preprocessor = AutoImageProcessor.from_pretrained(config.checkpoint)
        self.backbone: ViTModel = AutoModel.from_pretrained(config.checkpoint) # TODO we now just consider ViTModel
        self.backbone.train()
        self.backbone_config: ViTConfig = self.backbone.config # 包括了 image_size 和 hidden_size 这两个重要信息
        if config.head_strategy == "linear":
            self.head = nn.Linear(self.backbone_config.hidden_size, config.num_of_classes)
        else:
            raise NotImplementedError("Only linear head is supported for now. ")
        self.config = config
        self.forward_with_hf_image_preprocessor = forward_with_hf_image_preprocessor
    
    
    
    def forward(self, x:torch.Tensor)->torch.Tensor:
        if self.forward_with_hf_image_preprocessor:
            x = self.image_preprocessor(images=x, return_tensors="pt")["pixel_values"]
        hf_output = self.backbone(x)
        # hidden_state = hf_output.last_hidden_state
        output = hf_output.pooler_output
        output = self.head(output)
        return output
    
from fastcore.basics import patch
@patch
def get_cls_model(self:ClassificationModelConfig):
    if self.provider == "huggingface":
        return HuggingfaceModel(self)
    else:
        raise NotImplementedError("Only huggingface is supported for now. ")

# %% ../nbs/00_core.ipynb 8
import lightning as L
from pydantic import BaseModel
from .data import ClassificationDataConfig, ClassificationDataModule

class ClassificationTaskConfig(BaseModel):
    experiment_index: int = 0  # [0, 1, 2, 3, 4, 5, 6, 7, 8, 9] 表示是第几次重复实验 # which is also the random seed
    label_smoothing: float = 0.1
    cls_model_config: ClassificationModelConfig = ClassificationModelConfig()
    dataset_config: ClassificationDataConfig = ClassificationDataConfig()
    learning_rate: float = 3e-4

# %% ../nbs/00_core.ipynb 9
@patch
def see_params_norm(self:nn.Module)->float:
    params = torch.cat([param.view(-1) for param in self.parameters()])
    # 计算范数，这里以2-范数为例
    norm = torch.norm(params, p=2)
    return norm.item()

@patch
def see_grad_norm(self:nn.Module)-> float:
    grads = torch.cat([param.grad.view(-1) for param in self.parameters() if param.grad is not None])
    # 计算范数，这里以2-范数为例
    norm = torch.norm(grads, p=2)
    return norm.item()
    

# %% ../nbs/00_core.ipynb 10
import lightning as L
from lightning.pytorch.utilities.types import EVAL_DATALOADERS, TRAIN_DATALOADERS, STEP_OUTPUT, OptimizerLRScheduler
from overrides import override
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from .utils import print_model_pretty
from .utils import partial_with_self, append_dict_list, compute_classification_metrics, ensure_array, logger
import numpy as np
from typing import Any
class ClassificationTask(L.LightningModule):
    def __init__(self, config: ClassificationTaskConfig)->None:
        super().__init__()
        self.save_hyperparameters(config.model_dump())
        L.seed_everything(config.experiment_index) # use index as the seed for reproducibility
        # 首先数据是可以加载的
        self.lit_data:ClassificationDataModule = config.dataset_config.get_lightning_data_module()
        # 数据怎么做Transform，取决于 Model的情况
        # 现在我们加载Model，刚才有了数据之后，首先可以更新 cls_model_config
        
        config.cls_model_config.num_of_classes = self.lit_data.num_of_classes
        self.cls_model:HuggingfaceModel = config.cls_model_config.get_cls_model()
        
        # 现在需要更新数据
        self.lit_data.set_transform_from_hf_image_preprocessor(hf_image_preprocessor=self.cls_model.image_preprocessor)
        
        model_image_size:tuple[int, int] = (self.cls_model.image_preprocessor.size['height'], self.cls_model.image_preprocessor.size['width'])
        self.example_input_array = torch.Tensor(1, self.cls_model.backbone.config.num_channels, *model_image_size)
        
        # 最后是训练策略
        # self.softmax = nn.Softmax(dim=1)    
        self.softmax = nn.Identity()
        self.loss = nn.CrossEntropyLoss(label_smoothing=config.label_smoothing)
        # nn.LogSoftmax(dim=1)
        # https://blog.csdn.net/qq_43391414/article/details/118421352 logsoftmax+nll的速度快，但是没有label smoothing
        
        # 评价策略
        self.evaluation_steps_outputs = dict()
        
        self.automatic_optimization = False
    
    def compute_model_logits(self, image_tensor:torch.Tensor)-> torch.Tensor:
        return self.cls_model(image_tensor)
    
    # @override
    def forward(self, image_tensor:torch.Tensor, *args, **kwargs)-> torch.Tensor:
        return self.softmax(self.compute_model_logits(image_tensor))

    def forward_loss(self, image_tensor: torch.Tensor, label_tensor:torch.Tensor)->torch.Tensor:
        probs = self(image_tensor)
        # return F.nll_loss(logits, label_tensor)
        return self.loss(probs, label_tensor)

    # @override
    def training_step(self, batch, batch_idx=None, *args, **kwargs)-> STEP_OUTPUT:
        # self.train() # 不必要
        # opt = self.optimizers(use_pl_optimizer=False)
        opt = self.optimizers(use_pl_optimizer=True)
        opt.zero_grad()
        
        loss = self.forward_loss(*batch)
        self.log("train_loss", loss, prog_bar=True)
        # print("Loss:", loss.item())
        # self.manual_backward(loss)
        loss.backward()
        self.log("grad_norm", self.see_grad_norm(), prog_bar=True)
        old_params_norm = self.see_params_norm()
        
        self.log("params_norm", old_params_norm, prog_bar=True)
        # print("Grad Norm:", self.see_grad_norm())
        # print("Params Norm before step:", self.see_params_norm())
        # print("Params of cls_model Norm before step:", self.cls_model.see_params_norm())
        opt.step()
        # print("Params Norm after step:", self.see_params_norm())
        # print("Params of cls_model Norm after step:", self.cls_model.see_params_norm())
        params_norm_delta = self.see_params_norm() - old_params_norm
        self.log("params_norm_delta", params_norm_delta, prog_bar=True)
        
        # print()
        # print(loss)
        return loss

    # @override    
    def configure_optimizers(self) -> OptimizerLRScheduler:
        # return torch.optim.SGD(self.parameters(), lr=self.hparams.learning_rate)
        # return torch.optim.SGD(self.cls_model.parameters(), lr=self.hparams.learning_rate)
        # print("Learning Rate:", self.hparams.learning_rate)
        # return torch.optim.AdamW(self.parameters(), lr=self.hparams.learning_rate)
        # return torch.optim.AdamW(self.cls_model.parameters(), lr=self.hparams.learning_rate)
        
        # optimizer = optim.SGD(self.cls_model.parameters(), lr=self.hparams.learning_rate)
        # print(len(list(self.parameters())))
        
        optimizer = optim.AdamW(self.parameters(), lr=self.hparams.learning_rate)
        scheduler = torch.optim.lr_scheduler.CyclicLR(optimizer, base_lr=self.hparams.learning_rate/10, 
                                                      max_lr=self.hparams.learning_rate)
        return ([optimizer], [scheduler])
        # return L.AdamW(self.parameters(), lr=self.learning_rate)

    # 现在我们已经定义好Training的逻辑了，已经可以跑训练了。然而，除了训练之外，我们需要评测模型的性能。
    # @override
    # def 
    def on_evaluation_epoch_start(self, stage:str=""):
        self.evaluation_steps_outputs = dict()
        self.evaluation_steps_outputs[f'{stage}_batch_probs'] = []
        self.evaluation_steps_outputs[f'{stage}_label_tensor'] = []
            
    def evaluation_step(self, batch, batch_idx=None, stage:str="", *args: Any, **kwargs: Any) -> STEP_OUTPUT:
        image_tensor, label_tensor = batch
        batch_probs = self(image_tensor)
        append_dict_list(self.evaluation_steps_outputs, f'{stage}_batch_probs', ensure_array(batch_probs))
        append_dict_list(self.evaluation_steps_outputs, f'{stage}_label_tensor', ensure_array(label_tensor))
        batch_loss = self.loss(batch_probs, label_tensor)
        self.log(f"{stage}_loss", batch_loss, prog_bar=True)
        return batch_loss
            
    def on_evaluation_epoch_end(self, stage:str=""):
        # https://github.com/Lightning-AI/pytorch-lightning/discussions/9845
        # labels = self.lit_data.classes
        labels = list(range(self.lit_data.num_of_classes))
        # labels = None
        # print(labels)
        # stack 是 new axis， concat是existing axis
        all_pred_probs = np.concatenate(self.evaluation_steps_outputs[f'{stage}_batch_probs'])
        all_label_tensor = np.concatenate(self.evaluation_steps_outputs[f'{stage}_label_tensor'])
        # logger.debug(self.evaluation_steps_outputs[f'{stage}_label_tensor'])
        # logger.debug(all_label_tensor)
        eval_dict = compute_classification_metrics(all_label_tensor, all_pred_probs, 
                                                #    logits_to_prob=False, 
                                                   logits_to_prob=True, 
                                                labels=labels)
        eval_dict = {f"{stage}_{k}": v for k,v in eval_dict.items()}
        self.log_dict(eval_dict)
        self.evaluation_steps_outputs.clear()

    def on_validation_epoch_start(self):
        return self.on_evaluation_epoch_start(stage="val")

    def on_test_epoch_start(self):
        return self.on_evaluation_epoch_start(stage="test")

    def on_validation_epoch_end(self):
        return self.on_evaluation_epoch_end(stage="val")

    def on_test_epoch_end(self):
        return self.on_evaluation_epoch_end(stage="test")

    def validation_step(self, batch, batch_idx=None):
        return self.evaluation_step(batch, batch_idx, stage="val")

    def test_step(self, batch, batch_idx=None):
        return self.evaluation_step(batch, batch_idx, stage="test")

