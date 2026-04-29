.PHONY: install test test-unit test-integration test-music lint format arch-lint \
       new-project compose render setup-soundfonts all-checks

install:
	pip install -e ".[dev]"

test:
	pytest tests/

test-unit:
	pytest tests/unit/

test-integration:
	pytest tests/integration/ -m integration

test-music:
	pytest tests/music_constraints/ -m music_constraints

lint:
	ruff check src/ tests/
	mypy src/yao/

format:
	ruff format src/ tests/
	ruff check --fix src/ tests/

arch-lint:
	python tools/architecture_lint.py

all-checks: lint arch-lint test

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
