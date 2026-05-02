.PHONY: install setup-hooks test test-unit test-integration test-music test-golden test-subagent \
       lint format arch-lint matrix-check feature-status validate-spec new-project compose render \
       setup-soundfonts all-checks

install:
	pip install -e ".[dev]"

setup-hooks:
	pre-commit install
	pre-commit install --hook-type pre-push
	@echo "Pre-commit hooks installed (commit: lint+format+arch, push: tests)"

test:
	pytest tests/

test-unit:
	pytest tests/unit/

test-integration:
	pytest tests/integration/ -m integration

test-music:
	pytest tests/music_constraints/ -m music_constraints

test-golden:
	pytest tests/golden/ -v -m golden

test-subagent:
	pytest tests/subagent_evals/ -v -m subagent

test-subjective:
	pytest tests/subjective/ -v -m subjective

lint:
	ruff check src/ tests/
	mypy src/yao/

format:
	ruff format src/ tests/
	ruff check --fix src/ tests/

arch-lint:
	python tools/architecture_lint.py

matrix-check: feature-status

feature-status:
	python tools/feature_status_check.py

validate-spec:
	@test -n "$(SPEC)" || (echo "Usage: make validate-spec SPEC=specs/templates/v2/bgm-90sec-pop.yaml" && exit 1)
	python -c "from yao.schema.loader import load_composition_spec_auto; s = load_composition_spec_auto(__import__('pathlib').Path('$(SPEC)')); print(f'OK: {type(s).__name__} loaded — {s.identity.title if hasattr(s, \"identity\") else s.title}')"

sync-skills:
	python tools/skill_yaml_sync.py

sync-docs:
	python tools/sync_docs.py

all-checks: lint arch-lint matrix-check feature-status sync-docs test test-golden

new-project:
	@test -n "$(NAME)" || (echo "Usage: make new-project NAME=my-song" && exit 1)
	yao new-project $(NAME)

compose:
	@test -n "$(SPEC)" || (echo "Usage: make compose SPEC=specs/projects/my-song/composition.yaml" && exit 1)
	yao compose $(SPEC)

render:
	@test -n "$(MIDI)" || (echo "Usage: make render MIDI=outputs/projects/my-song/iterations/v001/full.mid" && exit 1)
	yao render $(MIDI)

setup-soundfonts:
	@echo "=== SoundFont Setup ==="
	@echo "Download FluidR3_GM.sf2 from:"
	@echo "  https://member.keymusician.com/Member/FluidR3_GM/index.html"
	@echo "Place it in: soundfonts/FluidR3_GM.sf2"
	@echo ""
	@echo "Or on macOS with Homebrew:"
	@echo "  brew install fluid-synth"
	@echo "  ln -s /usr/local/share/soundfonts/default.sf2 soundfonts/default.sf2"
