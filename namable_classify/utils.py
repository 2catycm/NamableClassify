"""通用工具函数和路径设置"""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/00_utils.ipynb.

# %% auto 0
__all__ = ['lib_init_path', 'lib_directory_path', 'lib_repo_path', 'runs_path', 'runs_figs_path', 'data_path', 'roc_auc_score',
           'ensure_array', 'default_on_exception', 'compute_classification_metrics', 'append_dict_list',
           'partial_with_self']

# %% ../nbs/00_utils.ipynb 5
from pathlib import Path
import inspect
import namable_classify
lib_init_path = Path(inspect.getfile(namable_classify))
lib_directory_path = lib_init_path.parent
lib_repo_path = lib_directory_path.parent
runs_path = lib_repo_path/'runs'
runs_path.mkdir(exist_ok=True, parents=True)
runs_figs_path = runs_path/'figs'
runs_figs_path.mkdir(exist_ok=True, parents=True)
data_path = lib_repo_path/'data'
data_path.mkdir(exist_ok=True, parents=True)

# %% ../nbs/00_utils.ipynb 6
from fastcore.basics import patch
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
@patch
def print_trainable_parameters(model:nn.Module):
    """
    Prints the number of trainable parameters in the model.
    """
    trainable_params = 0
    all_param = 0
    for _, param in model.named_parameters():
        all_param += param.numel()
        if param.requires_grad:
            trainable_params += param.numel()
    print(
        f"trainable params: {trainable_params} || all params: {all_param} || trainable%: {100 * trainable_params / all_param:.2f}"
    )

# %% ../nbs/00_utils.ipynb 7
from bigmodelvis import Visualization
@patch
def print_model_pretty(self:nn.Module):
    Visualization(self).structure_graph()

# %% ../nbs/00_utils.ipynb 8
import torch
import numpy as np
def ensure_array(x: torch.TensorType | np.ndarray | list):
    if isinstance(x, torch.Tensor):
        return x.detach().cpu().numpy()
    elif isinstance(x, np.ndarray):
        return x
    else: # list
        return np.array(x)

# %% ../nbs/00_utils.ipynb 9
from sklearn.metrics import *

# from scipy.special import softmax
import torch.nn.functional as F
import numpy as np
import torch
from loguru import logger
def default_on_exception(default_value=None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                logger.warning(f"An exception occurred: {e}")
                return default_value
        return wrapper
    return decorator

roc_auc_score = default_on_exception(-1)(roc_auc_score)

def compute_classification_metrics(
    y_true: np.ndarray,  # 1d array-like, or label indicator array / sparse matrix
    y_pred_logits: np.ndarray,  # label indicator array / sparse matrix
    logits_to_prob: bool = False,  # function to convert logits to probabilities
    labels:list[int|str]|None = None,  # list of labels
):
    y_true = ensure_array(y_true)
    y_pred_logits = ensure_array(y_pred_logits)
    # print(type(y_pred_logits)) # <class 'numpy.ndarray'>
    # y_pred_probs = softmax(y_pred_logits)# label indicator array / sparse matrix
    y_pred_probs = (
        np.array(F.softmax(torch.Tensor(y_pred_logits), dim=1))
        if logits_to_prob
        else y_pred_logits
    )  # label indicator array / sparse matrix
    y_pred = np.argmax(y_pred_logits, axis=1)
    # target_names = labels # dataset['train'].features[label_column_name].names
    # report_dict = classification_report(y_true, y_pred_probs, target_names=target_names, output_dict=True)
    top_k_res = {
        f"acc{k}": top_k_accuracy_score(y_true, y_pred_probs, k=k, labels=labels)
        for k in [1, 2, 3, 5, 10, 20]
    }
    balance_res = dict(
        roc_auc=roc_auc_score(
            y_true, y_pred_probs, average="macro", multi_class="ovr", labels=labels
        ),  # ovr更难一些，会不平衡
        matthews_corrcoef=matthews_corrcoef(y_true, y_pred),
        f1=f1_score(y_true, y_pred, average="macro", labels=labels),
        precision=precision_score(y_true, y_pred, average="macro", labels=labels),
        recall=recall_score(y_true, y_pred, average="macro", labels=labels),
        log_loss=log_loss(
            y_true,
            y_pred_probs,
            labels=labels
        ),
        balanced_accuracy=balanced_accuracy_score(y_true, y_pred),
        cohen_kappa=cohen_kappa_score(y_true, y_pred, labels=labels),
        hinge_loss=hinge_loss(y_true, y_pred_probs, labels=labels),
    )

    # return top_k_res| balance_res| report_dict
    return top_k_res | balance_res

# %% ../nbs/00_utils.ipynb 11
def append_dict_list(dict, name, value):
    dict[name] = dict.get(name, []) + [value]

# %% ../nbs/00_utils.ipynb 12
def partial_with_self(method, *args, **kwargs):
    def wrapped(self, *additional_args, **additional_kwargs):
        # Combine provided args and kwargs with additional ones
        all_args = args + additional_args
        all_kwargs = kwargs | additional_kwargs
        return method(self, *all_args, **all_kwargs)
    return wrapped