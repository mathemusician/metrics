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

from typing import Any, Callable, Optional, Sequence, Union, List

from torch import Tensor, tensor
from typing_extensions import Literal

from torchmetrics.functional.text.eed import _eed_compute, _eed_update
from torchmetrics.metric import Metric


class EED(Metric):
    """Computes extended edit distance score (`EED`_) [1] for strings or list of strings. The metric utilises the
    Levenshtein distance and extends it by adding an additional jump operation.

    Args:
        language:
            Language used in sentences. Only supports English (en) and Japanese (ja) for now. Defaults to en
        return_sentence_level_score:
            An indication of whether sentence-level EED is to be returned
        alpha:
            optimal jump penalty, penalty for jumps between characters
        rho:
            coverage cost, penalty for repetition of characters
        deletion:
            penalty for deletion of character
        insertion:
            penalty for insertion or substitution of character
        compute_on_step:
            Forward only calls ``update()`` and return None if this is set to False.
        dist_sync_on_step:
            Synchronize metric state across processes at each ``forward()``
            before returning the value at the step.
        process_group:
            Specify the process group on which synchronization is called. default: None (which selects the entire world)
        dist_sync_fn:
            Callback that performs the allgather operation on the metric state. When ``None``, DDP
            will be used to perform the allgather

    Returns:
        Extended edit distance score as a tensor

    Example:
        >>> from torchmetrics.text import EED
        >>> reference_corpus = ["this is the reference", "here is another one"]
        >>> hypothesis_corpus = ["this is the prediction", "here is an other sample"]
        >>> metric = EED()
        >>> metric(reference_corpus=reference_corpus, hypothesis_corpus=hypothesis_corpus)
        tensor(0.3204)

    References:
        [1] P. Stanchev, W. Wang, and H. Ney, “EED: Extended Edit Distance Measure for Machine Translation”, submitted
        to WMT 2019. `EED`_
    """

    scores: Tensor
    total_num_sentences: Tensor
    sentence_eed: Optional[List[Tensor]] = None
    higher_is_better: False
    is_differentiable: False

    def __init__(
        self,
        language: Literal["en", "ja"] = "en",
        return_sentence_level_score: bool = False,
        alpha: float = 2.0,
        rho: float = 0.3,
        deletion: float = 0.2,
        insertion: float = 1.0,
        compute_on_step: bool = True,
        dist_sync_on_step: bool = False,
        process_group: Optional[Any] = None,
        dist_sync_fn: Callable = None,
    ):
        super().__init__(
            compute_on_step=compute_on_step,
            dist_sync_on_step=dist_sync_on_step,
            process_group=process_group,
            dist_sync_fn=dist_sync_fn,
        )

        if language not in ("en", "ja"):
            raise ValueError(f"Expected argument `language` to either be `en` or `ja` but got {language}")
        self.language: Literal["en", "ja"] = language
        self.return_sentence_level_score = return_sentence_level_score

        self.alpha = alpha
        self.rho = rho
        self.deletion = deletion
        self.insertion = insertion

        self.add_state("scores", tensor(0.0), dist_reduce_fx="sum")
        self.add_state("total_num_sentences", tensor(0.0), dist_reduce_fx="sum")
        if self.return_sentence_level_score:
            self.add_state("sentence_eed", [], dist_reduce_fx="cat")

    def update(  # type: ignore
        self,
        reference_corpus: Sequence[Union[str, Sequence[str]]],
        hypothesis_corpus: Union[str, Sequence[str]],
    ) -> None:
        """Update EED statistics.

        Args:
            reference_corpus: An iterable of iterables of reference corpus
            hypothesis_corpus: An iterable of hypothesis corpus
        """
        scores, total_num_sentences, sentence_eed = _eed_update(
            reference_corpus,
            hypothesis_corpus,
            self.language,
            self.return_sentence_level_score,
            self.alpha,
            self.rho,
            self.deletion,
            self.insertion,
        )

        self.scores += scores
        self.total_num_sentences += total_num_sentences
        if self.return_sentence_level_score is True:
            self.sentence_eed.extend(sentence_eed)

    def compute(self) -> Tensor:
        """Calculate extended edit distance score.

        Returns:
            Extended edit distance score as tensor
        """
        if self.return_sentence_level_score is True:
            return self.sentence_eed
        return _eed_compute(self.scores, self.total_num_sentences)
