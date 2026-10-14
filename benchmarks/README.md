# Render benchmarks

35 deterministic scenes: 30 short workloads (~4 seconds) and five involved workloads (~15 seconds). Defaults are **854×480, 15 fps, one scene/process at a time**. Each scene renders exactly twice consecutively: a first run with a fresh scene disk cache, then a cached repeat in a new process. There is no repeat parameter. Every render includes movie encoding; individual movies, generated inputs and caches are temporary and automatically deleted.

Run these commands from the repository root with the `manimgl` Conda environment. Install the small runner dependency if needed:

```sh
conda run --no-capture-output -n manimgl python -m pip install -r benchmarks/requirements.txt
```

## Run

```sh
# All scenes; first run and cached repeat
conda run --no-capture-output -n manimgl python benchmarks/run.py --output benchmarks/results/baseline

# List scenes, or select a subset (quoted name globs also work)
conda run --no-capture-output -n manimgl python benchmarks/run.py --list
conda run --no-capture-output -n manimgl python benchmarks/run.py --only BreadthFirstSearchGraph HilbertSpaceFilling3D

# Quick development check; standard defaults are 480p/15fps
conda run --no-capture-output -n manimgl python benchmarks/run.py --only Solids3D --resolution 854x480 --fps 15
```

`--output` must name a **new** directory. Omit it to use `benchmarks/results/<UTC timestamp>/`. Add `--compile-video` to keep a joined `suite.mp4` inside that run's directory; each selected scene appears once, even with repetitions. `--timeout SECONDS` changes the 300-second per-render limit. `--scene-file example_scenes.py` selects scenes from another file (its original durations and asset requirements apply).

Each result directory contains only:

```text
results.json     Full measurements, settings, scene fingerprint, Git revision/status and environment
summary.csv      Separate first/cached measurements and statuses
logs/            One renderer/encoder log per invocation
suite.mp4        Only when --compile-video was requested and every scene succeeded
```

Interrupted runs retain completed measurements. Failed renders remain in the reports and logs and have unavailable summary timings; failures/timeouts exit nonzero, Ctrl+C exits 130. Temporary data is cleaned in all of those cases. There are no persistent benchmark input or compilation caches. Directly previewing a scene outside the runner can generate inputs in `benchmarks/_generated/`.

## Compare repository changes

Start a fresh baseline at 854×480 and 15 fps. Earlier 1080p/60fps results are historical references, not comparable baselines; the comparison tool rejects mismatched resolution, FPS or scene fingerprints. The reduced SpringMesh and BFS workloads also require a fresh baseline.

1. Run the baseline command above **before** changing the repository.
2. Make your changes. Keep benchmark sources and render settings fixed.
3. Run the same suite with a new output name, then compare:

```sh
conda run --no-capture-output -n manimgl python benchmarks/run.py --output benchmarks/results/candidate
conda run --no-capture-output -n manimgl python benchmarks/run.py --compare benchmarks/results/baseline benchmarks/results/candidate
```

The comparison reports scene execution and wall-time changes separately for each phase. **Negative percentages mean faster; positive mean slower.** It refuses mismatched scene fingerprints, resolution, FPS and encoding, omits percentages for failed/incomplete scenes, and warns about changed environment, configuration or GPU identity. Either directory paths or `results.json` paths are accepted. No rendering happens during comparison.

Use the same machine, power mode, background workload, dependency versions and scene selection/order. Each scene gets isolated Text/TeX/Matplotlib disk cache paths shared by its two invocations and deleted after the suite. OS and driver caches are not flushed, and process-local caches do not survive the restart. The cached repeat measures reuse of available disk caches, not a guaranteed fully warm GPU. Check another suite before treating a small change as a regression. Different Git revisions are expected; benchmark sources should stay unchanged.

The final output contains two tables: **First run** and **Cached repeat**. Both include status, wall time, render time, FPS, CPU usage, process-tree memory and GPU utilization. Results are never averaged across the two phases. GPU N/A means unavailable. The new report format rejects older combined-result reports.

## Reading the numbers

- **Render s / FPS**: `Scene.run()` time and emitted frames divided by that time, including setup, object creation, updates, GPU readback and encoder drain. Playback FPS is a separate setting. This is generally the best starting point for renderer changes.
- **Wall s**: startup/imports, device initialization, scene execution and process exit (up to ~50 ms of process-wait polling delay). Import and camera-init times are also recorded in JSON.
- **CPU %**: renderer plus waited-for encoder CPU time on Unix; 100% is one logical core. **Tree MiB**: peak sampled renderer-plus-descendant RSS at 100 ms intervals; shared pages may be double-counted and brief peaks missed. Worker-only OS peak RSS is also saved. Neither is GPU memory.
- **GPU utilization**: device-wide utilization is sampled through NVIDIA `nvidia-smi` or Apple IORegistry when available and includes other apps. Missing/invalid counters are shown as unavailable, not zero. No render-pass instrumentation or privileged monitoring is used.

## Layout and coverage

`run.py` is the entry point. `scenes/` contains one file per scene; `support/` holds asset generation, numerical algorithms, telemetry, the worker and reporting. `tests/` checks runner lifecycle and algorithm invariants. The root `.gitignore` ignores the entire `benchmarks/` directory as requested, including source and generated results; retain any baselines you need locally or copy them elsewhere.

The short scenes cover vector paths, boolean operations, Pango/LaTeX, changing numbers, graphs, vector fields, updaters, camera motion, backgrounds, transparency, clipping, textures, preloaded/streaming video, lighting, surfaces, shader fractals, 500–600 independent mobjects, a 500-building city, a 20,000-point cloud, sorting, connected meshes, object churn and recursive zoom. Use `--list` for individual descriptions. `TexMatching` needs a TeX installation.

The long workloads are:

| Scene | Workload |
| --- | --- |
| `BreadthFirstSearchGraph` | Real FIFO BFS over 336 nodes / 690 deforming edges, live queue and reconstructed shortest path |
| `HilbertSpaceFilling3D` | Orders 2–6, 262,144 face-adjacent sites, 4,096 colored stroke chunks, refinement transforms and camera orbit |
| `ClothWindSimulation3D` | 4,617 constrained particles, wind/gravity/contact, deforming texture, 138 wire paths and 513 shaded beads |
| `GalaxyMergerNBody3D` | 1,026 bodies, direct all-pairs gravity, 120 Hz velocity-Verlet integration and 32 history trails |
| `ReactionDiffusionLaboratory` | Two-species PDE, 10,240 simulation cells, 2,560 vector tiles and evolving concentration profiles |

The long scenes contain active computation, not wall-clock sleeps. Their playback duration does not promise any particular render time. Lower development FPS reduces drawing work while fixed-step simulations retain their simulation rates. The Hilbert helper implements the [Skilling transpose/Gray-code construction](https://github.com/galtay/hilbertcurve#references) without an extra dependency.

Add a file in `scenes/` with a top-level class directly inheriting `Scene`, `ThreeDScene` or `InteractiveScene` and a descriptive docstring; it is discovered automatically. Seed randomness. Regression checks:

```sh
conda run --no-capture-output -n manimgl python -B -m unittest discover -s benchmarks/tests -v
```
