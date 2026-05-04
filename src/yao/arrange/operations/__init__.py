"""Arrangement operations — pluggable transformations.

Import all operations here to trigger ``@register_arrangement`` decorators.
"""

from __future__ import annotations

from yao.arrange.operations.regroove import RegrooveOperation as RegrooveOperation
from yao.arrange.operations.reharmonize import ReharmonizeOperation as ReharmonizeOperation
from yao.arrange.operations.reorchestrate import ReorchestrateOperation as ReorchestrateOperation
from yao.arrange.operations.retempo import RetempoOperation as RetempoOperation
from yao.arrange.operations.transpose import TransposeOperation as TransposeOperation
