# User guide

[中文](zh-CN.md) · [Repository home](../README.en.md)

## Environment and first run

The full workflow's hardware-tested baseline is Windows / Python 3.13.9 / OriginPro 2026 (10.30018). Provide an installed, activated Origin/OriginPro. The repository supplies code, dependencies and MCP; users supply Origin. Bootstrap requires Python 3.13.9; pass `-Python` and the actual interpreter path to `bootstrap.ps1` when necessary.

Run from the complete repository root:

```powershell
pwsh -NoProfile -File scripts/bootstrap.ps1
.\.venv\Scripts\python.exe scripts/doctor.py
.\.venv\Scripts\python.exe scripts/reproduce.py --case synthetic --output runs/first
```

Read the doctor output first. Successful package installation establishes dependency readiness. Native figures, project reopening and readback require run evidence. Preserve existing output and choose a new directory for every run.

A full run includes conversion, an independent audit and native Origin validation. Add `--conversion-only` when you only need tables; record that validation level explicitly.

## Input and sample mass

Use MPMS3 summary measurement DAT files. The parser reads the actual `[Data]` header and checks temperature, field and moment columns. Raw voltage scan `.rw.dat` files need their corresponding scan-processing workflow.

Supply the actual sample mass confirmed by the user, in mg. Neither a filename nor the instrument header's `Mass (grams)` field substitutes for that confirmation.

```powershell
.\.venv\Scripts\python.exe scripts/reproduce.py --input "measurement.dat" --mass-mg 2.5 --output runs/measurement
.\.venv\Scripts\python.exe scripts/reproduce.py --input "measurement.dat" --raw --output runs/raw
```

Normalization is `magnetization_emu_g = moment_emu / mass_mg × 1000`. Raw emu and normalized emu/g remain available; `--raw` explicitly selects raw moment. Supply experimental evidence or user-provided labels for orientation, ZFC/FC and related conditions.

To inspect columns and segments, or select the DC source, call the skill's conversion entry point directly:

```powershell
.\.venv\Scripts\python.exe skills/origin-mpms-import/scripts/prepare_mpms.py inspect "measurement.dat"
.\.venv\Scripts\python.exe skills/origin-mpms-import/scripts/prepare_mpms.py convert "measurement.dat" --mass-mg 2.5 --dc-source fixed --output runs/table-only
```

VSM uses `Moment (emu)`. DC supports `fixed` and `free`, with `fixed` as the default. Each manifest records the selected source. Check the experiment when the method, available columns or moment interpretation disagree.

## Segmentation and review

The workflow segments continuous modes, MT warming/cooling, MH temperature plateaus and distinct sweeps in acquisition order. It retains the actual temperature and field of each segment and covers every record exactly once. Automatic segmentation uses the repository configuration. Pass `--segments segments.json` to the conversion entry point when explicit boundaries are needed.

```json
[
  {"first_record": 1, "last_record": 100, "category": "MT", "direction": "warming"},
  {"first_record": 101, "last_record": 200, "category": "MH_loop"}
]
```

Intervals use one-based valid record numbers with inclusive endpoints, covering the input completely in order. The example shows the format only; determine boundaries from the actual input. Categories are `MT`, `MH_loop`, `MH_initial` and `MH_partial`.

| Warning | Review |
|---|---|
| `short_segment_review` | Few points: check the acquisition boundary |
| `open_or_incomplete_cycle` | A loop may be incomplete: retain its measured start/end fields |
| `one_way_or_partial_sweep` | Review a one-way or partial sweep against the experiment program |
| `explicit_segment_boundary` | Explicit boundaries were used |

Warnings do not smooth, interpolate or change measurements. Assess data quality and physical interpretation against the experimental record.

## Outputs and Origin

Each conversion package includes `wide.xlsx`, `per_curve.xlsx`, `csv/`, `manifest.json`, `source_rows.csv` and `import_and_plot.ogs`. XLSX rows 1–3 contain names, units and conditions; numerical data begin at row 4. MT uses temperature for X; MH uses field.

A full run also creates an editable OPJU, individual plots, grouped overviews, PNG/PDF and validation summaries. It saves and reopens the project, then checks table values, curve counts and axis labels. Consult the current run summary for exact output paths.

For manual native import, start an empty Origin project, press Alt+3 to open the command window, run the following and select the converted package directory:

```text
run.section("C:\your-package\import_and_plot.ogs", Main);
```

Replace the placeholder path. If a protection message reports existing project contents or output, preserve them and use an empty project and a new location.

## Use in Codex

Keep the complete repository. `plugin.json` identifies the skill package, and `.agents/plugins/marketplace.json` points to the root plugin. Install the local repository plugin through your supported Codex plugin interface, then invoke it in a new chat:

```text
Use $origin-mpms-import to reproduce real-0p5mg through the Origin project and PNG/PDF outputs. Report numerical checks and the actual runtime.
```

The skill resolves the repository and scripts from its own location. The run adapter starts MCP; the manifest contains no machine-specific interpreter or shared Origin connection. On first use, check the skill files, Python and Origin, then collect task evidence. [Official packaging guide](https://developers.openai.com/plugins/build/plugins)

## Recovering from a failure

Read the failed stage in the summary and preserve the input and evidence. For conversion errors, check headers, mass, source columns and segment boundaries. For Origin connection errors, check installation, licensing, dependencies and session ownership. A failed dedicated connection must not fall back to changing an existing shared project. After a repair, rerun affected stages in a new directory and report the checks actually completed.

## Readback after moving a project

Place each complete case output package, including OPJU, manifest, CSV and OGS, at a new location. Replace the example paths and choose a new output directory:

```powershell
.\.venv\Scripts\python.exe scripts/verify_relocated_projects.py --packages "moved/synthetic" "moved/real-0p5mg" "moved/real-24mg" --output runs/relocation-check
```

The check opens and reads saved projects through a dedicated Origin instance while preserving the project files. Results go to `relocation-report.json`. The repository has passed same-machine copied-source relocation and moved-project readback using the same locked environment and installed Origin. Fresh Git-clone, clean-OS and second-machine checks have separate statuses.
