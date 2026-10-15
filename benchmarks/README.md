# Render benchmarks

48 deterministic scenes: 36 short workloads (~4 seconds), six 8-second workloads, and six involved workloads (~15 seconds). Defaults are **854×480, 15 fps, one scene/process at a time**. Each scene renders exactly twice consecutively: a first run with a fresh scene disk cache, then a cached repeat in a new process. There is no repeat parameter. Every render includes movie encoding. Baseline movies are retained as references. Candidate movies and logs are deleted after successful visual validation; failed or unchecked runs retain their diagnostics. Generated inputs and caches are temporary.

Validation references use lossless RGB encoding (`libx264rgb`, `rgb24`, CRF 0), preserving rendered RGB pixels. These files live in `reference-videos/` and may display incorrectly in players without RGB H.264 support. Watch the conventional H.264 copies in `videos/` instead: one per baseline scene, plus copies of failing candidate phases. Review copies are made after timed rendering and never used for pixel comparisons. Older lossy baselines are incompatible: preserve the old baseline directory and generate a new one with `--baseline`.

Run these commands from the repository root with the `manimgl` Conda environment. Install the small runner dependency if needed:

```sh
conda run --no-capture-output -n manimgl python -m pip install -r benchmarks/requirements.txt
```

## Run

```sh
# Once: create the visual baseline (then watch its videos to approve the reference)
conda run --no-capture-output -n manimgl python benchmarks/run.py --baseline

# After a code change: benchmark and automatically validate against that baseline
conda run --no-capture-output -n manimgl python benchmarks/run.py

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
logs/            Logs for failed or unchecked invocations only
suite.mp4        Only when --compile-video was requested and every scene succeeded
reference-videos/ Lossless baseline movies, or failed/unchecked candidate movies
videos/          Compatible review copies for baseline scenes and failures
validation.json  Frame, duration and visual validation results
visual-diffs/    Failure details and worst-frame reference/candidate/amplified diff PNGs
```

Interrupted runs retain completed measurements. Failed renders remain in the reports and logs and have unavailable summary timings; failures/timeouts exit nonzero, Ctrl+C exits 130. Temporary data is cleaned in all of those cases. There are no persistent benchmark input or compilation caches. Directly previewing a scene outside the runner can generate inputs in `benchmarks/_generated/`.

## Compare repository changes

The visual baseline lives in `benchmarks/results/visual-baseline`. Existing timing-only results are preserved, but cannot validate images. The baseline command refuses to overwrite an existing visual baseline; move that directory aside to replace it deliberately.

1. Run the baseline command above **before** changing the repository.
2. Make your changes. Keep benchmark sources and render settings fixed.
3. Run the same suite with a new output name, then compare:

```sh
conda run --no-capture-output -n manimgl python benchmarks/run.py --output benchmarks/results/candidate
conda run --no-capture-output -n manimgl python benchmarks/run.py --compare benchmarks/results/visual-baseline benchmarks/results/candidate
```

The comparison reports scene execution and wall-time changes separately for each phase. **Negative percentages mean faster; positive mean slower.** It refuses mismatched scene fingerprints, resolution, FPS and encoding, omits percentages for failed/incomplete scenes, and warns about changed environment, configuration or GPU identity. Either directory paths or `results.json` paths are accepted. No rendering happens during comparison.

Use the same machine, power mode, background workload, dependency versions and scene selection/order. Each scene gets isolated Text/TeX/Matplotlib disk cache paths shared by its two invocations and deleted after the suite. OS and driver caches are not flushed, and process-local caches do not survive the restart. The cached repeat measures reuse of available disk caches, not a guaranteed fully warm GPU. Check another suite before treating a small change as a regression. Different Git revisions are expected; benchmark sources should stay unchanged.

The final output contains one table with first-run wall time, **Cached wall s**, first-run render time and FPS. CPU usage, GPU utilization and process-tree memory are arithmetic averages of the two runs (memory averages their sampled peaks). An average is unavailable if either run failed or lacks the measurement. Scene names are green only when both phases render and validate successfully, and red otherwise; there is no status column. FPS, CPU %, GPU % and Tree MiB display rounded integers. Saved JSON/CSV measurements remain separate by phase for timing comparisons and validation. GPU N/A means unavailable.

## Automatic visual correctness checks

Normal runs require a compatible visual baseline and validate both phases automatically. `--only` can validate a subset against the full reference. Resolution, FPS, encoder settings, configuration and selected scene fingerprints must match. Baseline video checksums detect changed or missing reference files. Render failures and visual failures both produce a nonzero exit status.

All decoding, comparison and tolerance calibration happens **after the complete timed render suite**. Timings include normal movie encoding, but exclude movie retention and validation. Every decoded frame is checked at the same frame index; frames are never resized or realigned to hide changes. Checks cover dimensions, exact frame counts, playback rate, timestamp cadence and duration. Candidate frame counts and durations must match their reference phase. Worker frame counts must also match decoded counts.

Tolerances are automatic, with no CLI tuning required. RGB differences up to 12 levels per channel are treated as small pixel noise. A frame initially allows at most 0.1% of pixels beyond that tolerance and a mean absolute RGB error of 0.5 on the 0–255 scale. The baseline's first/cached comparison calibrates those two limits per scene to 1.5 times observed variation, never below the defaults or above 0.5% changed pixels and 1.5 mean error. Larger variation rejects the baseline as insufficiently repeatable. Candidates cannot loosen the saved thresholds. Timestamp/duration tolerance is 1 ms; comparison with scene animation time allows one frame of rounding.

These are bounded pixel-error checks, not a semantic proof of correctness. Review the reference videos before treating them as authoritative. An intentional appearance change requires review and a new baseline. Video compression and driver differences can cause flagged changes, which should be reviewed rather than automatically accepted.

On a visual mismatch, all failing frame indices and scores are recorded, and the worst failing frame per scene/phase gets reference, candidate and 4× amplified difference PNGs. Missing frames retain the available image; decode/render failures may have only `failure.json` because no valid image exists. Failed/unchecked candidate videos remain available for inspection; successful candidate videos and logs are removed after validation. Baseline videos are always retained, but successful baseline logs are removed. The timing table remains separate from the final visual PASS/FAIL line; saved timing comparisons suppress improvement percentages for phases that failed visual checks.

## Reading the numbers

- **Final timing totals**: video-generation time sums the measured wall times of both renders per scene (including process startup and encoding). Validation time measures the post-render checks, calibration/comparison, saved visual diffs and compatible review-copy generation. Both display minutes and seconds and are saved separately in `results.json`. Setup, lossless file copying, optional suite-video joining and reference preflight checks are outside these totals.
- **Render s / FPS**: `Scene.run()` time and emitted frames divided by that time, including setup, object creation, updates, GPU readback and encoder drain. Playback FPS is a separate setting. This is generally the best starting point for renderer changes.
- **Wall s**: startup/imports, device initialization, scene execution and process exit (up to ~50 ms of process-wait polling delay). Import and camera-init times are also recorded in JSON.
- **CPU %**: renderer plus waited-for encoder CPU time on Unix; 100% is one logical core. **Tree MiB**: peak sampled renderer-plus-descendant RSS at 100 ms intervals; shared pages may be double-counted and brief peaks missed. Worker-only OS peak RSS is also saved. Neither is GPU memory.
- **GPU utilization**: device-wide utilization is sampled through NVIDIA `nvidia-smi` or Apple IORegistry when available and includes other apps. Missing/invalid counters are shown as unavailable, not zero. No render-pass instrumentation or privileged monitoring is used.

## Layout and coverage

`run.py` is the entry point. `scenes/` contains one file per scene; `support/` holds asset generation, numerical algorithms, telemetry, the worker and reporting. `tests/` checks runner lifecycle and algorithm invariants. The root `.gitignore` ignores generated `benchmarks/results/`; benchmark sources are tracked. Retain any baselines you need locally or copy them elsewhere.

The short scenes cover vector paths, boolean operations, Pango/LaTeX, changing numbers, graphs, vector fields, updaters, camera motion, backgrounds, transparency, clipping, textures, preloaded/streaming video, lighting, surfaces, shader fractals, 500–600 independent mobjects, a 500-building city, a 20,000-point cloud, sorting, connected meshes, object churn and recursive zoom. Use `--list` for individual descriptions. `TexMatching` needs a TeX installation.

The long workloads are:

| Scene | Workload |
| --- | --- |
| `BreadthFirstSearchGraph` | Real FIFO BFS over 336 nodes / 690 deforming edges, live queue and reconstructed shortest path |
| `HilbertSpaceFilling3D` | Orders 1–4, 4,096 face-adjacent sites, 32 rainbow paths with shared refinement knots, progressive drawing, curved transforms, 32 local tracers and continuous camera orbit |
| `ClothWindSimulation3D` | 4,617 constrained particles, wind/gravity/contact, deforming texture, 138 wire paths and 513 shaded beads |
| `GalaxyMergerNBody3D` | 718 bodies, direct all-pairs gravity, 120 Hz velocity-Verlet integration and 32 history trails |
| `ReactionDiffusionLaboratory` | Two-species PDE, 10,240 simulation cells, 2,560 vector tiles and evolving concentration profiles |
| `TernaryFormCloud` | All n=1–51 concentration stages, e=1–5 dense clouds, six halo/point layers, prime highlights, reduction shell, axes and camera orbit |
| `TernaryTetrahedronWalk` | All 70 Cholesky tetrahedron morphs, n=8–17 convergence, e=1–3 destination clouds, six live edge labels and shaded vertices |

The five additional short scenes are `HilbertRefinement2D`, `DistinctTextureGallery`, `DualTextureLighting3D`, `TextureFilteringZoom` and `HomotopyRibbons`; none loads imported 3D models.

The long scenes contain active computation, not wall-clock sleeps. Their playback duration does not promise any particular render time. Lower development FPS reduces drawing work while fixed-step simulations retain their simulation rates. The Hilbert helper implements the [Skilling transpose/Gray-code construction](https://github.com/galtay/hilbertcurve#references) without an extra dependency. Its common sampling retains every corner of every order, so refinement transforms preserve point correspondence. The ternary scenes retain the concentration, convergence and growing-e stages of their source films; translucent point halos are composited without obscuring their bright centers.

Add a file in `scenes/` with a top-level class directly inheriting `Scene`, `ThreeDScene` or `InteractiveScene` and a descriptive docstring; it is discovered automatically. Seed randomness. Regression checks:

```sh
conda run --no-capture-output -n manimgl python -B -m unittest discover -s benchmarks/tests -v
```
