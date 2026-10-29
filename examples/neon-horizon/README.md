# Neon Horizon · editable demo

[English](README.md) · [Español](README.es.md)

![Final composite rendered in Nukify](preview.png)

A panoramic cyberpunk composition by **Max Sarlija**, built in Nukify 0.10.1 with two GPT-generated images and 22 editable nodes. The preview is an actual render from the bundled Blender 4.5.14 engine.

## Try it

1. Install [Nukify 0.10.1 or later](https://github.com/maxsarlijagit/Nukify/releases).
2. Clone this repository or use **Code → Download ZIP** and extract it. Keep this whole folder, including `media/`; downloading only the project is not enough.
3. Open Nukify, press **Ctrl+O**, and open `examples/neon-horizon/Neon_Horizon.nukify`.
4. Enable **Live** and change a node parameter. Viewer A uses `Fine_Film_Grain`; Viewer B uses `City_Density` for comparison with the background.
5. Choose a writable output folder before rendering. Media paths are relative and no machine-specific Blender or output path is saved.

## Explore the graph

- `Green_Key` and `Matte_Check`: chroma key, despill and alpha inspection.
- `Unpremult_Edges`, `Hero_Light_Match`, `Premult_Edges`: edge handling and light matching.
- `Hero_Placement`: foreground position and scale.
- `Contact_Shadow_Mask`, `Right_Boot_Shadow`, `Boot_Contact_Masks`: separate contact shadows under both boots.
- `Hero_Over_City`, `Final_Film_Balance`, `Fine_Film_Grain`: merge, final balance and subtle grain.

`Hero_Saturation` and `Film_Contrast` are optional ColorCorrect nodes intentionally disabled to retain shadow detail. Enabling them changes the delivered look.

## Contents and limits

The project is a **1920 × 804 single frame**, not a video, tracking test or sequence demo. The wet floor does not have a physically computed character reflection; contact shadows are artistic approximations. Cinematic hyperrealism is the visual direction, not studio certification. No affiliation with ILM or DNEG.

Both source PNGs and the preview are included. No API key or paid request is required to open and render this project. Exactly two images were generated with GPT in Codex; no fal.ai requests were made. `provenance.json` records source hashes; `SHA256SUMS.txt` verifies the project and images. EXR/Blender outputs, caches and application binaries are not tracked: render locally to produce your own outputs.

The installed app and live viewer were tested during demo creation. Repository packaging validates graph dependencies, media resolution and file hashes; it does not imply testing on a second clean PC.

This example is distributed with Nukify under [GPL-3.0-or-later](../../LICENSE), to the extent rights apply to its AI-generated imagery. Author and composition: Max Sarlija. AI-generated source media is identified explicitly above.
