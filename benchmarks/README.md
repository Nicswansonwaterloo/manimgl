# Render benchmarks

35 deterministic scenes: 30 short workloads (~4 seconds) and five involved workloads (~15 seconds). Defaults are **1920×1080, 60 fps, one scene/process at a time**. Every render includes movie encoding; individual movies, generated inputs and caches are temporary and automatically deleted.

Run these commands from the repository root with the `manimgl` Conda environment. Install the small runner dependency if needed:

```sh
conda run --no-capture-output -n manimgl python -m pip install -r benchmarks/requirements.txt
```

## Run

```sh
# All scenes; medians over three repetitions
conda run --no-capture-output -n manimgl python benchmarks/run.py --repeat 3 --output benchmarks/results/baseline

# List scenes, or select a subset (quoted name globs also work)
conda run --no-capture-output -n manimgl python benchmarks/run.py --list
conda run --no-capture-output -n manimgl python benchmarks/run.py --only BreadthFirstSearchGraph HilbertSpaceFilling3D

# Quick development check; official defaults stay 1080p/60fps
conda run --no-capture-output -n manimgl python benchmarks/run.py --only Solids3D --resolution 640x360 --fps 15
```

`--output` must name a **new** directory. Omit it to use `benchmarks/results/<UTC timestamp>/`. Add `--compile-video` to keep a joined `suite.mp4` inside that run's directory; each selected scene appears once, even with repetitions. `--timeout SECONDS` changes the 300-second per-render limit. `--scene-file example_scenes.py` selects scenes from another file (its original durations and asset requirements apply). `--gpu-timing` enables optional GPU timestamp profiling, which adds overhead and may be unsupported by the driver.

Each result directory contains only:

```text
results.json     Full measurements, settings, scene fingerprint, Git revision/status and environment
summary.csv      Per-scene medians and pass/fail counts
logs/            One renderer/encoder log per invocation
suite.mp4        Only when --compile-video was requested and every scene succeeded
```

Interrupted runs retain completed measurements. Failed renders remain in the reports and logs and are excluded from performance medians; failures/timeouts exit nonzero, Ctrl+C exits 130. Temporary data is cleaned in all of those cases. There are no persistent benchmark input or compilation caches. Directly previewing a scene outside the runner can generate inputs in `benchmarks/_generated/`.

## Compare repository changes

1. Run the baseline command above **before** changing the repository.
2. Make your changes. Keep benchmark sources and render settings fixed.
3. Run the same suite with a new output name, then compare:

```sh
conda run --no-capture-output -n manimgl python benchmarks/run.py --repeat 3 --output benchmarks/results/candidate
conda run --no-capture-output -n manimgl python benchmarks/run.py --compare benchmarks/results/baseline benchmarks/results/candidate
```

The comparison reports median scene execution and wall-time changes. **Negative percentages mean faster; positive mean slower.** It refuses mismatched scene fingerprints, resolution, FPS, encoding or GPU-profiling mode, omits percentages for failed/incomplete scenes, and warns about changed environment, configuration or GPU identity. Either directory paths or `results.json` paths are accepted. No rendering happens during comparison.

Use the same machine, power mode, background workload, dependency versions, scene selection/order and repetition count. Check several repetitions before treating a small change as a regression. Text/TeX/Matplotlib disk caches are shared within a suite and deleted afterwards; first and subsequent invocations can differ. OS and driver caches are not flushed. Different Git revisions are expected; benchmark sources should stay unchanged. There is no noisy automatic performance pass/fail threshold.

## Reading the numbers

- **Render s / FPS**: `Scene.run()` time and emitted frames divided by that time, including setup, object creation, updates, GPU readback and encoder drain. Playback FPS is a separate setting. This is generally the best starting point for renderer changes.
- **Wall s**: startup/imports, device initialization, scene execution and process exit (up to ~50 ms of process-wait polling delay). Import and camera-init times are also recorded in JSON.
- **CPU %**: renderer plus waited-for encoder CPU time on Unix; 100% is one logical core. **Tree MiB**: peak sampled renderer-plus-descendant RSS at 100 ms intervals; shared pages may be double-counted and brief peaks missed. Worker-only OS peak RSS is also saved. Neither is GPU memory.
- **GPU**: actual adapter/backend and completed draw/pass evidence; optional per-pass timestamps measure GPU execution, excluding Python, readback and encoding. NVIDIA `nvidia-smi` or Apple IORegistry utilization is sampled when available. Utilization is device-wide and includes other apps. Missing/invalid counters remain unavailable, not zero. No privileged monitoring is used.

## Layout and coverage

`run.py` is the entry point. `scenes/` contains one file per scene; `support/` holds asset generation, numerical algorithms, telemetry, GPU instrumentation, the worker and reporting. `tests/` checks runner lifecycle and algorithm invariants. The root `.gitignore` ignores the entire `benchmarks/` directory as requested, including source and generated results; retain any baselines you need locally or copy them elsewhere.

The short scenes cover vector paths, boolean operations, Pango/LaTeX, changing numbers, graphs, vector fields, updaters, camera motion, backgrounds, transparency, clipping, textures, preloaded/streaming video, lighting, surfaces, shader fractals, 500–600 independent mobjects, a 500-building city, a 20,000-point cloud, sorting, connected meshes, object churn and recursive zoom. Use `--list` for individual descriptions. `TexMatching` needs a TeX installation.

The long workloads are:

| Scene | Workload |
| --- | --- |
| `BreadthFirstSearchGraph` | Real FIFO BFS over 512 nodes / 1,064 deforming edges, live queue and reconstructed shortest path |
| `HilbertSpaceFilling3D` | Orders 2–6, 262,144 face-adjacent sites, 4,096 colored stroke chunks, refinement transforms and camera orbit |
| `ClothWindSimulation3D` | 4,617 constrained particles, wind/gravity/contact, deforming texture, 138 wire paths and 513 shaded beads |
| `GalaxyMergerNBody3D` | 1,026 bodies, direct all-pairs gravity, 120 Hz velocity-Verlet integration and 32 history trails |
| `ReactionDiffusionLaboratory` | Two-species PDE, 10,240 simulation cells, 2,560 vector tiles and evolving concentration profiles |

The long scenes contain active computation, not wall-clock sleeps. Their playback duration does not promise any particular render time. Lower development FPS reduces drawing work while fixed-step simulations retain their simulation rates. The Hilbert helper implements the [Skilling transpose/Gray-code construction](https://github.com/galtay/hilbertcurve#references) without an extra dependency.

Add a file in `scenes/` with a top-level class directly inheriting `Scene`, `ThreeDScene` or `InteractiveScene` and a descriptive docstring; it is discovered automatically. Seed randomness. Regression checks:

```sh
conda run --no-capture-output -n manimgl python -B -m unittest discover -s benchmarks/tests -v
```
