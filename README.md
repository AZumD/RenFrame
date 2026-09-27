# RenFrame

RenFrame is a small Linux utility that inspects desktop Ren'Py games and prepares them for native **Linux ARM64 / aarch64** play, especially on the **Steam Frame** headset.

It does **not** translate x86_64 machine code. Ren'Py games are mostly architecture-independent data (`game/`, `.rpa`, images, audio). RenFrame's model is:

```text
Original game data + ARM64 Ren'Py runtime = native ARM64 game
```

Bundled x86 binaries are treated as compatibility problems to detect and report.

## Status (MVP milestone 1)

Implemented:

- `renframe inspect <directory>`
- Ren'Py layout detection
- Modular Ren'Py version / generation detection (7.x vs 8.x)
- Native dependency scanning (`.so`, `.dll`, `.exe`, `.pyd`)
- ELF architecture identification in pure Python
- Human-readable and `--json` compatibility reports

Not yet implemented:

- `renframe build` (ARM runtime swap + launcher generation)
- Automatic runtime downloading

## Requirements

- Python 3.10+
- Linux recommended (Steam Frame / aarch64 target)

## Setup

```bash
python3 -m venv mistralvenv
source mistralvenv/bin/activate
pip install -e ".[dev]"
```

## Usage

```bash
renframe inspect "/path/to/game"
renframe inspect "/path/to/game" --json
```

Exit codes:

| Code | Meaning |
|------|---------|
| 0 | Success / likely compatible |
| 1 | Tool / runtime error |
| 2 | Not a Ren'Py game / invalid path |
| 3 | Compatibility concern (needs testing, unknown version, or native code) |

## Tests

```bash
source mistralvenv/bin/activate
pytest
```

## Project layout

```text
renframe/
  cli.py              CLI entrypoint
  inspect_service.py  Inspection orchestration
  detector.py         Ren'Py layout + version strategies
  scanner.py          Native deps + compatibility verdict
  elf.py              ELF header parsing
  models.py           Dataclasses / enums
  runtime.py          Runtime manager stub
  builder.py          Build stub (next milestone)
  utils.py            Path safety helpers
tests/
docs/README/
```

## License

MIT
