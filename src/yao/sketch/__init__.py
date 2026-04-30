"""Sketch-to-Spec dialogue — interactive NL→spec compilation.

Houses the SpecCompiler which extracts musical knowledge from natural
language descriptions. The Conductor delegates NL parsing here instead
of containing music theory logic (CLAUDE.md anti-pattern #7).
"""

from __future__ import annotations
