<p align="center">
  <a href="https://github.com/brunonlinespace/brunonlinespace/blob/main/linspectacles/kernel-pressure.png">
    <img
      src="https://raw.githubusercontent.com/brunonlinespace/brunonlinespace/main/linspectacles/kernel-pressure.png"
      alt="Kernel Pressure screenshot"
      width="900"
    >
  </a>
</p>

# Kernel Pressure

**Expose. Explore. Explain.**

Kernel Pressure is a read-only Linux Pressure Stall Information (PSI) inspector for CPU, memory and I/O.

Current release: **0.0.7**

Repository: <https://github.com/linspectacles/kernel-pressure>

## What Kernel Pressure is

Kernel Pressure answers a focused question: **what CPU, memory and I/O pressure values is the running kernel reporting through PSI?**

It keeps acquisition and interpretation close to the Linux interfaces actually used by the applet. When a source is unavailable, restricted, or does not report a field, the README does not imply that the applet can manufacture the missing information.

## Highlights

- CPU pressure from `/proc/pressure/cpu`.
- Memory pressure from `/proc/pressure/memory`.
- I/O pressure from `/proc/pressure/io`.
- Preserves kernel-reported `some` / `full` scopes where exposed.
- Shows `avg10`, `avg60`, `avg300` and cumulative `total` stalled time as reported.

## Data sources and acquisition

- `/proc/pressure/cpu`.
- `/proc/pressure/memory`.
- `/proc/pressure/io`.

The applet uses those sources according to the acquisition paths implemented in this release. Optional tools or privileged helpers only affect the views/actions that explicitly use them; they are not treated as silent substitutes for unrelated sources.

## Interface

Kernel Pressure follows the LinSpectacles inventory + **Metadata Details** pattern where applicable: an acquired inventory remains separate from the details for the selected record, and search/filter controls operate on the data the applet has actually collected.

The applet's **Options** surface provides the presentation/source/about controls implemented by this release, together with export controls where present in the source. Applet-specific actions remain explicit rather than being folded into background collection.

## Read-only and scope boundaries

Kernel Pressure reports PSI values without assigning arbitrary good/bad thresholds or inferring overall system health. It only reads the three procfs PSI interfaces and does not alter scheduler, memory or I/O behaviour.

## Running from source

The supplied source is directly runnable on Linux. The Python-side requirements are:

- Python 3.
- PyQt6 for the graphical interface.

Create a local virtual environment if you do not already have the required Python packages in the environment you want to use:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install PyQt6
python3 linspectacles_kernel_pressure/standalone.py
```

Linux commands, procfs/sysfs interfaces, system services, or optional helpers mentioned in **Data sources and acquisition** are applet-specific runtime inputs. A missing optional source is handled by the applet's existing availability/error path; it is not replaced here with an invented dependency or capability.

No RPM installation instructions are included in this README.

## Source layout and LinSpectacles integration

The applet source is contained in:

```text
linspectacles_kernel_pressure/
├── __init__.py
├── standalone.py
├── LICENSE
├── applet.json
├── README.md
└── kernel_pressure/
    ├── __init__.py
    ├── applet.py
    ├── _support.py
    └── icon.png
```

`applet.json` supplies the LinSpectacles applet identity and entrypoint metadata. `standalone.py` launches the applet directly, while the package's applet factory provides the host-loadable LinSpectacles integration used by the source.

## Configuration

Presentation and inspection preferences are persisted only through the settings mechanisms already implemented by the applet. Persisted UI state does not grant the applet permission to modify the inspected Linux subsystem.

## Scope

Kernel Pressure is intentionally specialist. Related Linux information that belongs to another LinSpectacles subsystem remains outside this applet rather than being inferred or duplicated here.

## License

GNU General Public License v3.0 or later. See [`LICENSE`](LICENSE).

## Links

- LinSpectacles organisation: <https://github.com/linspectacles/>
- Repository: <https://github.com/linspectacles/kernel-pressure>
- Issues: <https://github.com/linspectacles/kernel-pressure/issues>

<p align="center">
  <a href="https://github.com/linspectacles/kernel-pressure">
    <img
      src="kernel_pressure/icon.png"
      alt="Kernel Pressure"
      width="256"
    >
  </a>
</p>
