# Copyright The PyTorch Lightning team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import Optional
from warnings import warn

import torch
from torch import Tensor

from torchmetrics.functional.classification.jaccard import jaccard_index


def iou(
    preds: Tensor,
    target: Tensor,
    ignore_index: Optional[int] = None,
    absent_score: float = 0.0,
    threshold: float = 0.5,
    num_classes: Optional[int] = None,
    reduction: str = "elementwise_mean",
) -> Tensor:
    r"""
     Computes `Jaccard index`_

    .. deprecated:: v0.7
         Use :func:`torchmetrics.functional.jaccard_index`. Will be removed in v0.8.

     Example:
         >>> from torchmetrics.functional import iou
         >>> target = torch.randint(0, 2, (10, 25, 25))
         >>> pred = torch.tensor(target)
         >>> pred[2:5, 7:13, 9:15] = 1 - pred[2:5, 7:13, 9:15]
         >>> iou(pred, target)
         tensor(0.9660)
    """
    warn(
        "Function `iou` is renamed in v0.7 and will be removed in v0.8."
        " Use `functional.functional.jaccard_index` instead.",
        DeprecationWarning,
    )
    return jaccard_index(preds, target, ignore_index, absent_score, threshold, num_classes, reduction)
