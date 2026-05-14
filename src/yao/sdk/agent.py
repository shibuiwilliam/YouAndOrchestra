"""YaoAgent — high-level façade for the Claude Agent SDK.

``YaoAgent`` is the Lane A entry point: a single class that pre-configures
the Claude Agent SDK for music production and exposes one async-generator
method per slash command.

Example::

    async with YaoAgent(project="my-song") as agent:
        async for event in agent.conduct("a calm piano piece in D minor"):
            print(event)
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, Literal

from claude_agent_sdk import ClaudeAgentOptions, query

from yao.sdk._options import default_yao_options
from yao.sdk.events import (
    ConductorFinishedEvent,
    YaoEvent,
)
from yao.sdk.streaming import translate_message


class YaoAgent:
    """High-level façade over Claude Agent SDK pre-configured for YaO.

    A YaoAgent represents one indefinite music-production session anchored
    to a single project directory. Methods correspond 1-to-1 with the slash
    commands available inside Claude Code, so any user familiar with the
    interactive experience can drive YaO programmatically without learning
    a new vocabulary.
    """

    def __init__(
        self,
        project: str,
        *,
        cwd: str | Path | None = None,
        model: str | None = None,
        permission_mode: Literal[
            "default", "acceptEdits", "plan", "bypassPermissions", "dontAsk", "auto"
        ] = "acceptEdits",
        extra_options: ClaudeAgentOptions | None = None,
    ) -> None:
        self.project = project
        self._cwd = cwd
        self._model = model
        self._permission_mode = permission_mode
        self._extra_options = extra_options
        self._options: ClaudeAgentOptions | None = None
        self._iteration = 0
        self._interrupted = False

    async def __aenter__(self) -> YaoAgent:
        """Initialize the agent options."""
        extra = self._extra_options or ClaudeAgentOptions()
        if self._model:
            extra = ClaudeAgentOptions(
                **{
                    **{k: getattr(extra, k) for k in ClaudeAgentOptions.__annotations__},
                    "model": self._model,
                }
            )
        if self._permission_mode != "acceptEdits":
            extra = ClaudeAgentOptions(
                **{
                    **{k: getattr(extra, k) for k in ClaudeAgentOptions.__annotations__},
                    "permission_mode": self._permission_mode,
                }
            )

        self._options = default_yao_options(
            self.project,
            cwd=self._cwd,
            extra_options=extra,
        )
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        """Clean up."""
        self._options = None

    def _get_options(self) -> ClaudeAgentOptions:
        if self._options is None:
            raise RuntimeError("YaoAgent must be used as an async context manager")
        return self._options

    async def _run_prompt(self, prompt: str) -> AsyncIterator[YaoEvent]:
        """Run a prompt through the SDK and yield YaoEvents."""
        opts = self._get_options()
        async for msg in query(prompt=prompt, options=opts):
            for event in translate_message(msg, self._iteration):
                yield event

    async def sketch(self, description: str) -> AsyncIterator[YaoEvent]:
        """Interactive spec creation from a natural-language description.

        Args:
            description: What the music should sound like.

        Yields:
            YaoEvent subclasses as the sketch progresses.
        """
        async for event in self._run_prompt(f"/sketch {description}"):
            yield event

    async def compose(self, spec_or_desc: str | Path) -> AsyncIterator[YaoEvent]:
        """Generate one iteration via the Conductor loop.

        Args:
            spec_or_desc: Path to composition.yaml or natural-language description.

        Yields:
            YaoEvent subclasses as composition progresses.
        """
        self._iteration += 1
        prompt = f"/compose {spec_or_desc}"
        async for event in self._run_prompt(prompt):
            yield event

    async def conduct(
        self,
        spec_or_desc: str | Path,
        max_iterations: int = 3,
    ) -> AsyncIterator[YaoEvent]:
        """Generate, evaluate, adapt, regenerate until quality passes.

        Args:
            spec_or_desc: Path to composition.yaml or natural-language description.
            max_iterations: Maximum number of generation rounds.

        Yields:
            YaoEvent subclasses as the conductor loop progresses.
        """
        prompt = f"/conduct {spec_or_desc}"
        async for event in self._run_prompt(prompt):
            if isinstance(event, ConductorFinishedEvent):
                event.total_iterations = self._iteration
            yield event

    async def critique(self, iteration: str | None = None) -> AsyncIterator[YaoEvent]:
        """Run the Adversarial Critic on an iteration.

        Args:
            iteration: Optional iteration path. Uses latest if not specified.

        Yields:
            YaoEvent subclasses including CritiqueAvailableEvent.
        """
        prompt = f"/critique {iteration}" if iteration else "/critique"
        async for event in self._run_prompt(prompt):
            yield event

    async def regenerate_section(
        self,
        section: str,
        *,
        seed: int | None = None,
    ) -> AsyncIterator[YaoEvent]:
        """Regenerate a specific section while preserving the rest.

        Args:
            section: Section name to regenerate.
            seed: Optional random seed for reproducibility.

        Yields:
            YaoEvent subclasses.
        """
        self._iteration += 1
        prompt = f"/regenerate-section {section}"
        if seed is not None:
            prompt += f" --seed {seed}"
        async for event in self._run_prompt(prompt):
            yield event

    async def render(self, iteration: str | None = None) -> AsyncIterator[YaoEvent]:
        """Render MIDI to WAV audio.

        Args:
            iteration: Optional iteration path. Uses latest if not specified.

        Yields:
            YaoEvent subclasses including AudioReadyEvent.
        """
        prompt = f"/render {iteration}" if iteration else "/render"
        async for event in self._run_prompt(prompt):
            yield event

    async def diff(self, iter_a: str, iter_b: str) -> AsyncIterator[YaoEvent]:
        """Compare two iterations.

        Args:
            iter_a: Path to the first iteration.
            iter_b: Path to the second iteration.

        Yields:
            YaoEvent subclasses.
        """
        async for event in self._run_prompt(f"/diff {iter_a} {iter_b}"):
            yield event

    async def evaluate(self, iteration: str | None = None) -> AsyncIterator[YaoEvent]:
        """Re-run quality scoring on an iteration.

        Args:
            iteration: Optional iteration path.

        Yields:
            YaoEvent subclasses including EvaluationReportEvent.
        """
        prompt = f"/evaluate {iteration}" if iteration else "/evaluate"
        async for event in self._run_prompt(prompt):
            yield event

    async def explain(self, query_str: str) -> AsyncIterator[YaoEvent]:
        """Trace a decision back to its rationale.

        Args:
            query_str: Natural-language query about a decision.

        Yields:
            YaoEvent subclasses.
        """
        async for event in self._run_prompt(f"/explain {query_str}"):
            yield event

    async def chat(self, prompt: str) -> AsyncIterator[YaoEvent]:
        """Send a free-form prompt to the orchestra.

        Args:
            prompt: Any natural-language instruction.

        Yields:
            YaoEvent subclasses.
        """
        async for event in self._run_prompt(prompt):
            yield event

    async def interrupt(self) -> None:
        """Abort the current conductor run.

        Signals the agent loop to stop at the next turn boundary.
        A final ``ConductorFinishedEvent(status="interrupted")`` will be
        emitted by the stream.
        """
        self._interrupted = True

    async def set_permission_mode(
        self,
        mode: Literal["default", "acceptEdits", "plan", "bypassPermissions", "dontAsk", "auto"],
    ) -> None:
        """Change the permission mode for subsequent operations.

        Takes effect on the next ``_run_prompt`` call — does not affect
        an already-running stream.

        Args:
            mode: The new permission mode.
        """
        self._permission_mode = mode
        # Re-build options with the new mode if context is active
        if self._options is not None:
            self._options = ClaudeAgentOptions(
                **{
                    **{k: getattr(self._options, k) for k in ClaudeAgentOptions.__annotations__},
                    "permission_mode": mode,
                }
            )
