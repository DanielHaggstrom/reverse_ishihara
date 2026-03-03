# Reverse Ishihara

Reverse Ishihara is a small Python project that generates reverse Ishihara-style dot plates and shows them side by side for normal vision and simulated color-vision deficiency. The current version keeps the original scope narrow: it generates a random two-digit plate each run and opens the result with the default image viewer.

## What changed in this cleanup

- Removed import-time side effects so the module is safe to import.
- Fixed the plate rendering logic so foreground and background dots are not drawn from the same palette.
- Made the reverse effect more consistent by coloring a shared dot field from a number mask instead of relying on placement artifacts.
- Added safe clipping around the color-space conversion to avoid invalid image data.
- Added font fallbacks so the script works without a hard dependency on `arial.ttf`.
- Added packaging metadata, tests, and basic repository hygiene files.

## Requirements

- Python 3.10 or newer

## Install

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## Run

```powershell
python main.py
```

Each run picks:

- A random two-digit number
- A random supported simulation type: `deuteranopia` or `protanopia`

The script opens a combined image with a "Normal Vision" plate on the left and the simulated plate on the right.

## Test

```powershell
pytest
```

## Notes

- This project is for illustration and experimentation. It is not medically validated and should not be treated as a diagnostic tool.
- The reverse effect depends on the simulation model from `colorspacious`, so the generated palettes are tuned for this project rather than for clinical use.

## License

MIT. See `LICENSE`.
