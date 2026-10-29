**English | [Español](README.es.md)**

<div align="center">
  <img src="assets/nukify-logo.png" width="96" alt="Nukify logo">
  <h1>Nukify</h1>
  <p><strong>Open-source node-based compositing, powered by Blender.</strong></p>
  <p>A standalone Windows desktop compositor by <a href="https://github.com/maxsarlijagit">Max Sarlija</a>.</p>
  <p>
    <a href="https://github.com/maxsarlijagit/Nukify/releases"><img alt="Version" src="https://img.shields.io/badge/version-0.10.1-orange"></a>
    <a href="LICENSE"><img alt="GPL v3 or later" src="https://img.shields.io/badge/license-GPL--3.0--or--later-blue"></a>
    <img alt="Windows x64" src="https://img.shields.io/badge/platform-Windows_x64-0078D4">
    <img alt="Technical beta" src="https://img.shields.io/badge/status-technical_beta-yellow">
  </p>
</div>

![Nukify: viewer, properties and vertical node graph](docs/images/compositing.png)

Nukify combines a custom Qt interface with the compositor and 3D tools of **Blender 4.5.14 LTS**. The viewer sits above the vertical node graph, with properties on the right. The installer includes the engine: Python and Blender do not need to be installed separately.

This is a **technical beta** with working workflows and automated tests. It is not presented as a complete Nuke replacement or a production-certified tool.

The current source version starts in **English**. Use **Language / Idioma** in the top toolbar to select **English** or **Español**, save, then reopen Nukify. The preference is stored locally, independently of projects. Node identifiers, technical enum values, provider schemas and user content keep their original names. This interface setting is separate from the documentation links above and is **included starting with 0.10.1**. See [interface languages](docs/guides/interface-languages.md) for running and testing the updated source.

## Download and install

1. Open [Releases](https://github.com/maxsarlijagit/Nukify/releases).
2. Download **Nukify-Setup-0.10.1.exe** and run it on Windows x64.
3. Launch Nukify and try **Proyecto → Ejemplos → Composición** or **Curvas y roto**.
4. Open **GENAI** in the main toolbar to configure your fal.ai account.

The installer is not commercially code-signed. Check its SHA256 against `SHA256SUMS.txt` in the same release. Validation was performed on Windows; a full installation test on a second clean PC is still pending.

Sources and notices for the main bundled components are included under `sources/` and `licenses/`. This repository contains Nukify's source; large executables and dependencies are distributed as release assets. Local builds produce `releases/0.10.1/Nukify-Setup-0.10.1.exe`. Check the release page for published downloads.

## GENAI Studio · fal.ai provider

**[fal.ai](https://fal.ai) is the inference provider for GENAI Studio.** Bring your own API key and billing account. The key stays in memory for the session or is read from `FAL_KEY`; it is not stored in composition projects or job history.

![Actual GENAI Studio interface: model settings and version library](docs/images/genai.png)

The screenshot shows the real application interface. It is not evidence of a paid generation.

- **Generate and edit images and videos**, including image-to-video workflows.
- **Model-specific controls:** resolution, quality, duration, format, output count, seed and reference inputs, where supported by the model.
- **11 featured endpoints:** Nano Banana 2.1/Pro, GPT Image 2, MiniMax H3 Max and Kling 4/O3 Pro. Search fal's current catalog and refresh model schemas from the UI. The featured selection is not an objective quality ranking.
- **Process tracking:** preparation, upload, queue, execution, download and local proxy creation, with resumable tracking by request ID.
- **Versioned media library:** retain originals, hashes, parameters and revisions; reuse a version's settings to create a new revision.
- **Send and receive proxies:** select a maximum long edge of 512, 1024 or 1920 pixels. Received proxies are created locally after downloading the original.
- **Use in the graph:** import a result as a `Read` node; videos are converted into PNG sequences. Video preview uses local frames at 12 fps without audio; open the original in the system player for full playback.

**Costs are estimates based on manually entered billing units.** Nukify queries fal's unit-price and estimation APIs, but does not automatically apply every resolution, duration, audio, token or quality multiplier. Check the model's pricing page and adjust the units before confirming. The estimate is neither the final charge nor a provider-enforced spending cap. Each submission asks you to confirm the media transfer and paid job.

**FFmpeg is required for video proxies and sequence extraction.** Configure an existing installation in GENAI → Conexión or put it on PATH. FFmpeg is not bundled or downloaded automatically. Paid inference has not yet been validated against a real account; catalog and schema queries have been checked live.

See the [GENAI guide (Spanish)](docs/guides/genai.md) for setup, recovery, supported inputs and limitations. GENAI is included in **0.10.1**; the earlier **0.9.2 installer does not contain it**.

## Features

| Area | Available features |
| --- | --- |
| Interface | Compact theme, vector icons, searchable inspector, node/project tabs, workspace presets and adaptive toolbars. |
| Node graph | Vertical connections, categories, node search, multi-selection, copy/paste, bypass, undo/redo and configurable shortcuts. |
| Viewer | Automatic updates, A/B comparison, wipe/difference, display exposure/gamma, pixel sampling, OCIO and frame caching. |
| Sequences | Timeline, playback and A/B prefetch. Smooth playback depends on cache availability and graph cost. |
| Compositing | Color, filters, masks, merge, transforms, time, keying, channels, reading and writing. |
| Animation | Keyframes, Bézier curves, tangents, retiming and restricted mathematical expressions with node references. |
| Roto | Bézier shapes, hierarchical groups, opacity, transforms and sampled mask motion blur. |
| Tracking | 2D and planar tracking, per-frame manual corrections, exclusion areas and loss/confidence reports. |
| 3D | Camera, Card, Geometry, Light, Scene, Project3D and RenderLayers. |
| Delivery | EXR/Cryptomatte, resumable render queue and project/media collection. |
| GENAI | fal.ai image/video generation and editing, process tracking, cost estimates, proxies and versioned results. |

## Screenshots

These are **actual application screenshots**. Compositing examples use synthetic fixtures included in the project, not client footage.

![Roto groups and compositing](docs/images/roto.png)

![Keyframe and tangent editor](docs/images/curve-editor.png)

## Neon Horizon · demo project

![Neon Horizon · actual Nukify composite](examples/neon-horizon/preview.png)

Try a **22-node, 1920 × 804 cinematic composition** with two GPT-generated source images: a cyberpunk character on chroma and a futuristic panoramic city. Explore key/despill, light matching, contact shadows, merge, film balance and grain. No API key is required.

**[Open the demo and instructions](examples/neon-horizon/README.md)** · [Español](examples/neon-horizon/README.es.md). Clone the repository or download its ZIP to get the project **and** media. This is a single-frame demo; limitations are documented in its guide.

## First steps

- **Tab:** search for and create a node.
- **1 / 2:** assign the selected node to viewer A / B.
- **F:** frame the graph; use the wheel to zoom and the middle mouse button to pan.
- **Space** over the graph: maximize/restore the editor.
- **Espacio → Composición / Viewer amplio / Nodos amplios:** change the workspace layout.
- **Live ON:** update the viewer when parameters change. **Cache range:** prepare frames for playback.
- **fx** in properties edits expressions; the **diamond** opens animation controls.

Customize shortcuts under Proyecto → Shortcuts. See the [interface guide](docs/guides/desktop-0.9.md) and [compositing, roto and tracking guide](docs/guides/desktop-0.8.md), currently in Spanish.

## Development and builds

Development uses Python 3.12, PySide6 and Blender 4.5.14 LTS. Dependencies are pinned in `requirements-build.txt` and `requirements-worker.txt`.

```powershell
git clone https://github.com/maxsarlijagit/Nukify.git
cd Nukify
```

Follow [BUILDING.md](BUILDING.md) to prepare worker dependencies, configure Blender, run tests and compile the installer. Builds record the source commit and application/engine hashes.

## Agent-assisted contributions

The **[/agents](agents/README.md)** folder contains shared instructions, responsibilities, validation criteria and a task/delivery template. Start with [First Agentic Contribution](agents/FIRST_AGENTIC_CONTRIBUTION.md): choose a small task, prepare your fork, give the agent a concrete assignment, review the evidence and open a PR.

[AGENTS.md](AGENTS.md) is the entry point for compatible tools. Ask other tools to read it explicitly. These contributor guides are currently in Spanish.

## Validation and limitations

- 67 local logic and Qt interaction tests passed with Blender configured.
- Packaged checks cover offline GENAI, expressions/roto, A/B caching, render queue/media and compositing/tracking/EXR regression.
- GENAI UI reviewed at 1024/1440 px and 150% scaling; the compositor also has earlier 1280 px checks.
- A synthetic 48-frame video was converted to proxies and imported as a sequence. Two frames were rendered in Blender with a maximum 8-bit pixel difference of 1 against the input PNGs.
- Release-specific results are in `VALIDATION.json` alongside the installer. CI unit tests are distinct from Blender-backed or installed-binary checks.

Still pending: real-shot/artist acceptance, extended HD/4K use, physical monitor/DPI changes, a second clean PC, intermediate-node caching, ROI, automatic occlusion recovery and paid GENAI inference. Planar tracking is not a 3D camera solve. Roto motion blur is not general image motion blur. Pausing GENAI tracking does not stop a remote charge; cancellation is subject to the provider's job state.

## Documentation and contributions

- [Documentation index](docs/README.md) · [Repository structure](docs/structure.md) · [Demo projects](examples/README.md)

- [Spanish README](README.es.md)
- [Build and development guide](BUILDING.md)
- [GENAI guide](docs/guides/genai.md)
- [Contributing](CONTRIBUTING.md)
- [Agent collaboration](agents/README.md)
- [Design system](docs/development/design-system.md)
- [Original roadmap](docs/planning/roadmap-produccion.md)
- [S15–S17 progress](docs/planning/sprints-0.8.md)
- [Release notes: English and Spanish](docs/releases/README.md)
- [Report an issue](https://github.com/maxsarlijagit/Nukify/issues)

## Author and license

**Max Sarlija** · [@maxsarlijagit](https://github.com/maxsarlijagit)

Copyright © 2026 Max Sarlija and contributors. Nukify's own code is licensed under **GPL-3.0-or-later**. See [LICENSE](LICENSE), [AUTHORS.md](AUTHORS.md) and [THIRD_PARTY.md](THIRD_PARTY.md).

Nukify is independent and is not affiliated with Blender Foundation, Foundry or fal.ai. Blender and Nuke are trademarks of their respective owners. External libraries retain their original licenses and notices. Use of fal.ai models is governed by the provider's terms; the app's open-source license does not license model weights or provider services.
