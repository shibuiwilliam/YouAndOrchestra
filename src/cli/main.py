"""YaO CLI — command-line interface for the music production environment.

The CLI is a consumer of the yao library, not part of it. It lives in
src/cli/ separate from src/yao/ to enforce clean separation.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import click
import structlog

# Import generators to trigger @register_generator decorators
import yao.generators.rule_based as _rb  # noqa: F401
import yao.generators.stochastic as _st  # noqa: F401
from yao.errors import RenderError, SpecValidationError, YaOError
from yao.generators.registry import get_generator
from yao.render.audio_renderer import render_midi_to_wav
from yao.render.iteration import next_iteration_dir
from yao.render.midi_writer import write_midi
from yao.render.stem_writer import write_stems
from yao.schema.loader import load_composition_spec, load_project_specs, load_trajectory_spec
from yao.verify.analyzer import analyze_score
from yao.verify.evaluator import evaluate_score

logger = structlog.get_logger()


@click.group()
@click.version_option(package_name="yao")
def cli() -> None:
    """YaO — Agentic Music Production Environment.

    Generate, analyze, and render music from YAML specifications.
    """


@cli.command()
@click.argument("spec_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Output directory. Default: auto-versioned iteration directory.",
)
@click.option(
    "--project",
    "-p",
    type=str,
    default=None,
    help="Project name (reads from specs/projects/<name>/).",
)
@click.option(
    "--trajectory",
    "-t",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to trajectory.yaml (optional).",
)
@click.option(
    "--render-audio/--no-render-audio",
    default=False,
    help="Render MIDI to WAV audio (requires fluidsynth).",
)
@click.option(
    "--soundfont",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to SoundFont file for audio rendering.",
)
@click.option(
    "--stems/--no-stems",
    default=True,
    help="Write per-instrument stem MIDI files (default: yes).",
)
def compose(
    spec_path: Path,
    output_dir: Path | None,
    project: str | None,
    trajectory: Path | None,
    render_audio: bool,
    soundfont: Path | None,
    stems: bool,
) -> None:
    """Generate a composition from a YAML spec."""
    try:
        # 1. Load spec
        click.echo(f"Loading spec: {spec_path}")
        spec = load_composition_spec(spec_path)

        traj = None
        if trajectory is not None:
            traj = load_trajectory_spec(trajectory)

        # 2. Determine output directory with auto-versioning
        if output_dir is None:
            if project:
                safe_name = project.lower().replace(" ", "-")
            else:
                safe_name = spec.title.lower().replace(" ", "-")
            project_dir = Path(f"outputs/projects/{safe_name}")
            output_dir = next_iteration_dir(project_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 3. Generate (use registry to select generator by spec config)
        strategy = spec.generation.strategy
        click.echo(
            f"Generating: {spec.title} ({spec.key}, {spec.tempo_bpm} BPM, strategy={strategy})"
        )
        generator = get_generator(strategy)
        score, provenance = generator.generate(spec, traj)

        # 4. Write MIDI
        midi_path = output_dir / "full.mid"
        write_midi(score, midi_path)
        click.echo(f"MIDI written: {midi_path}")

        # 5. Write stems
        if stems:
            stem_paths = write_stems(score, output_dir)
            click.echo(f"Stems written: {len(stem_paths)} instruments")

        # 6. Analyze and lint
        report = analyze_score(score)
        analysis_path = output_dir / "analysis.json"
        report.save(analysis_path)

        # 7. Evaluate
        eval_report = evaluate_score(score, spec, traj)
        eval_report.save(output_dir / "evaluation.json")

        # 8. Save provenance
        prov_path = output_dir / "provenance.json"
        provenance.save(prov_path)

        # 9. Optionally render audio
        if render_audio:
            wav_path = output_dir / "audio.wav"
            try:
                render_midi_to_wav(midi_path, wav_path, soundfont)
                click.echo(f"Audio rendered: {wav_path}")
            except RenderError as e:
                click.echo(f"Audio rendering skipped: {e}", err=True)

        # 10. Print summary
        click.echo("")
        click.echo(report.summary())
        click.echo("")
        click.echo(eval_report.summary())
        click.echo(f"\nOutput: {output_dir}")

    except SpecValidationError as e:
        raise click.ClickException(f"Spec validation error: {e}") from e
    except YaOError as e:
        raise click.ClickException(f"YaO error: {e}") from e


@cli.command()
@click.argument("midi_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Output WAV path. Default: same directory as MIDI file.",
)
@click.option(
    "--soundfont",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to SoundFont file.",
)
def render(midi_path: Path, output: Path | None, soundfont: Path | None) -> None:
    """Render a MIDI file to WAV audio."""
    if output is None:
        output = midi_path.with_suffix(".wav")

    try:
        render_midi_to_wav(midi_path, output, soundfont)
        click.echo(f"Audio rendered: {output}")
    except RenderError as e:
        raise click.ClickException(str(e)) from e


@cli.command("new-project")
@click.argument("name")
def new_project(name: str) -> None:
    """Create a new project skeleton."""
    safe_name = name.lower().replace(" ", "-")
    spec_dir = Path(f"specs/projects/{safe_name}")
    output_dir = Path(f"outputs/projects/{safe_name}/iterations")

    if spec_dir.exists():
        raise click.ClickException(f"Project '{safe_name}' already exists at {spec_dir}")

    spec_dir.mkdir(parents=True)
    output_dir.mkdir(parents=True)

    # Copy minimal template
    template = Path("specs/templates/bgm-90sec.yaml")
    target = spec_dir / "composition.yaml"
    if template.exists():
        shutil.copy(template, target)
    else:
        target.write_text(
            f'title: "{name}"\n'
            'genre: "general"\n'
            'key: "C major"\n'
            "tempo_bpm: 120\n"
            'time_signature: "4/4"\n'
            "total_bars: 8\n"
            "instruments:\n"
            "  - name: piano\n"
            "    role: melody\n"
            "sections:\n"
            "  - name: verse\n"
            "    bars: 8\n"
            '    dynamics: "mf"\n'
        )

    # Create intent.md placeholder
    (spec_dir / "intent.md").write_text(
        f"# {name}\n\nDescribe the intent of this composition here.\n"
    )

    click.echo(f"Project created: {safe_name}")
    click.echo(f"  Spec: {spec_dir}/composition.yaml")
    click.echo(f"  Output: {output_dir}/")
    click.echo(f"\nNext: edit {target}, then run: yao compose {target}")


@cli.command()
@click.argument("spec_path", type=click.Path(exists=True, path_type=Path))
def validate(spec_path: Path) -> None:
    """Validate a composition spec YAML file."""
    try:
        spec = load_composition_spec(spec_path)
        click.echo(f"Valid: {spec.title}")
        click.echo(f"  Key: {spec.key}")
        click.echo(f"  Tempo: {spec.tempo_bpm} BPM")
        click.echo(f"  Time: {spec.time_signature}")
        click.echo(f"  Bars: {spec.computed_total_bars()}")
        click.echo(f"  Instruments: {', '.join(i.name for i in spec.instruments)}")
        click.echo(f"  Sections: {', '.join(s.name for s in spec.sections)}")
    except SpecValidationError as e:
        raise click.ClickException(f"Validation failed: {e}") from e


@cli.command()
@click.argument("project_name")
def evaluate(project_name: str) -> None:
    """Evaluate the latest iteration of a project."""
    safe_name = project_name.lower().replace(" ", "-")
    project_dir = Path(f"specs/projects/{safe_name}")

    try:
        spec, traj = load_project_specs(project_dir)
    except SpecValidationError as e:
        raise click.ClickException(str(e)) from e

    from yao.render.iteration import current_iteration
    from yao.render.midi_reader import load_midi_to_score_ir

    output_dir = Path(f"outputs/projects/{safe_name}")
    latest = current_iteration(output_dir)
    if latest is None:
        raise click.ClickException(f"No iterations found for project '{safe_name}'")

    # Load the actual MIDI file from the latest iteration
    midi_path = latest / "full.mid"
    if midi_path.exists():
        score = load_midi_to_score_ir(midi_path, spec=spec)
        click.echo(f"Loaded: {midi_path}")
    else:
        # Fallback: re-generate if MIDI not found
        click.echo("No MIDI found, re-generating for evaluation...")
        generator = get_generator(spec.generation.strategy)
        score, _ = generator.generate(spec, traj)

    eval_report = evaluate_score(score, spec, traj)
    click.echo(eval_report.summary())


@cli.command("diff")
@click.argument("spec_path", type=click.Path(exists=True, path_type=Path))
@click.option("--seed-a", type=int, default=1, help="Seed for first generation.")
@click.option("--seed-b", type=int, default=2, help="Seed for second generation.")
def diff_cmd(spec_path: Path, seed_a: int, seed_b: int) -> None:
    """Compare two generations of the same spec with different seeds.

    Useful for understanding what the stochastic generator varies.
    """

    from yao.schema.composition import GenerationConfig
    from yao.verify.diff import diff_scores, format_diff

    try:
        spec = load_composition_spec(spec_path)

        # Generate two versions with different seeds
        gen_a = GenerationConfig(
            strategy="stochastic", seed=seed_a, temperature=spec.generation.temperature
        )
        gen_b = GenerationConfig(
            strategy="stochastic", seed=seed_b, temperature=spec.generation.temperature
        )
        title_a = f"{spec.title} (seed={seed_a})"
        title_b = f"{spec.title} (seed={seed_b})"
        spec_a = spec.model_copy(update={"generation": gen_a, "title": title_a})
        spec_b = spec.model_copy(update={"generation": gen_b, "title": title_b})

        generator = get_generator("stochastic")
        score_a, _ = generator.generate(spec_a)
        score_b, _ = generator.generate(spec_b)

        result = diff_scores(score_a, score_b)
        click.echo(format_diff(result))

    except YaOError as e:
        raise click.ClickException(str(e)) from e


@cli.command()
@click.argument("spec_path", type=click.Path(exists=True, path_type=Path))
@click.option("--query", "-q", type=str, default=None, help="Filter by operation name.")
def explain(spec_path: Path, query: str | None) -> None:
    """Explain the provenance of a composition's generation decisions."""
    try:
        spec = load_composition_spec(spec_path)
        generator = get_generator(spec.generation.strategy)
        _, provenance = generator.generate(spec)

        if query:
            records = provenance.query_by_operation(query)
            if not records:
                click.echo(f"No provenance records matching '{query}'.")
                return
            for r in records:
                click.echo(f"[{r.layer}] {r.operation}")
                click.echo(f"  Why: {r.rationale}")
                if r.parameters:
                    params = ", ".join(f"{k}={v}" for k, v in r.parameters.items())
                    click.echo(f"  With: {params}")
                click.echo("")
        else:
            click.echo(provenance.explain_chain())

    except YaOError as e:
        raise click.ClickException(str(e)) from e


@cli.command()
@click.argument("description", required=False)
@click.option(
    "--spec",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to existing composition.yaml (alternative to description).",
)
@click.option(
    "--project",
    "-p",
    type=str,
    default=None,
    help="Project name for output directory.",
)
@click.option(
    "--iterations",
    "-n",
    type=int,
    default=3,
    help="Maximum feedback-loop iterations (default: 3).",
)
def conduct(
    description: str | None,
    spec: Path | None,
    project: str | None,
    iterations: int,
) -> None:
    """Compose music with automatic feedback-driven iteration.

    The Conductor orchestrates the full workflow: generate → evaluate →
    adapt → regenerate, until all quality metrics pass or max iterations
    are reached.

    \b
    Two modes:
      yao conduct "a calm piano piece in D minor for studying"
      yao conduct --spec specs/projects/my-song/composition.yaml
    """
    from yao.conductor.conductor import Conductor

    conductor = Conductor()

    try:
        if spec is not None:
            # Spec mode: load existing spec and iterate
            loaded_spec = load_composition_spec(spec)
            trajectory_path = spec.parent / "trajectory.yaml"
            traj = None
            if trajectory_path.exists():
                traj = load_trajectory_spec(trajectory_path)

            click.echo(
                f"Conducting: {loaded_spec.title} "
                f"({loaded_spec.key}, {loaded_spec.tempo_bpm} BPM, "
                f"max {iterations} iterations)"
            )
            result = conductor.compose_from_spec(
                spec=loaded_spec,
                trajectory=traj,
                project_name=project,
                max_iterations=iterations,
            )
        elif description:
            # Description mode: natural language → full pipeline
            click.echo(f'Conducting from description: "{description}"')
            result = conductor.compose_from_description(
                description=description,
                project_name=project,
                max_iterations=iterations,
            )
        else:
            raise click.ClickException(
                "Provide a description or --spec. Example:\n"
                '  yao conduct "a calm piano piece in D minor"\n'
                "  yao conduct --spec my-spec.yaml"
            )

        click.echo("")
        click.echo(result.summary())
        click.echo("")
        click.echo(result.analysis.summary())
        click.echo("")
        click.echo(result.evaluation.summary())

    except YaOError as e:
        raise click.ClickException(str(e)) from e


@cli.command("regenerate-section")
@click.argument("project_name")
@click.argument("section_name")
@click.option("--seed", type=int, default=None, help="Seed override for regeneration.")
@click.option(
    "--iterations",
    "-n",
    type=int,
    default=3,
    help="Maximum feedback-loop iterations (default: 3).",
)
def regenerate_section(
    project_name: str, section_name: str, seed: int | None, iterations: int
) -> None:
    """Regenerate a specific section while preserving the rest.

    \b
    Example:
      yao regenerate-section my-song chorus
      yao regenerate-section my-song bridge --seed 99
    """
    from yao.conductor.conductor import Conductor
    from yao.render.midi_reader import load_midi_to_score_ir

    safe_name = project_name.lower().replace(" ", "-")
    project_dir = Path(f"specs/projects/{safe_name}")

    try:
        spec, traj = load_project_specs(project_dir)
    except SpecValidationError as e:
        raise click.ClickException(str(e)) from e

    from yao.render.iteration import current_iteration

    output_dir = Path(f"outputs/projects/{safe_name}")
    latest = current_iteration(output_dir)
    if latest is None:
        raise click.ClickException(
            f"No iterations found for project '{safe_name}'. Run compose first."
        )

    # Load existing MIDI
    midi_path = latest / "full.mid"
    if not midi_path.exists():
        raise click.ClickException(f"No MIDI found at {midi_path}. Run compose first.")

    try:
        current_score = load_midi_to_score_ir(midi_path, spec=spec)
        click.echo(f"Loaded: {midi_path}")
        click.echo(f"Regenerating section: {section_name}")

        conductor = Conductor()
        result = conductor.regenerate_section(
            current_score=current_score,
            spec=spec,
            section_name=section_name,
            trajectory=traj,
            project_name=safe_name,
            seed_override=seed,
        )

        click.echo("")
        click.echo(result.summary())
        click.echo("")
        click.echo(result.analysis.summary())
        click.echo("")
        click.echo(result.evaluation.summary())

    except YaOError as e:
        raise click.ClickException(str(e)) from e


if __name__ == "__main__":
    cli()
