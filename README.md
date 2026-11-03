# Doom on FHIR

![Doom on FHIR logo](./Doom%20on%20FHIR%20Logo.png)

SmartDoom is a proof-of-concept SMART on FHIR application that embeds the classic Doom engine inside a FHIR Questionnaire. The app uses a custom SDC item control to render a playable Doom session as part of a clinical assessment workflow, with game outcome data written back as a QuestionnaireResponse.

This repository combines:

- a browser-based SMART app (`smartdoom.html`)
- a Doom engine wrapper (`smartdoom-engine.js`)
- a Freedoom WAD (`freedoom1.wad`)
- a pure-FHIRPath questionnaire variant (`doom-fhirpath-questionnaire.json`)
- build scripts for the native/WebAssembly engine path in `build/`

## What this project does

The application demonstrates how a FHIR Questionnaire can host a game-like assessment item. A custom `doom` item control loads a WAD and mounts the Doom engine in-browser, while the Questionnaire captures gameplay data such as:

- map progress
- completion status
- kills
- items collected
- secrets found
- time spent
- health at last check

The result is a lightweight example of embedding a rich interactive experience into a standards-based FHIR workflow.

## Repository layout

- `smartdoom.html` — main SMART app and embedded Questionnaire definition
- `smartdoom-engine.js` — engine bootstrap and runtime glue for the Doom instance
- `freedoom1.wad` — Freedoom Phase 1 game data
- `doom-fhirpath-questionnaire.json` — alternate Questionnaire implemented in pure FHIRPath
- `build/` — engine build scripts and platform layer sources
- `FREEDOOM-COPYING.txt` — licensing information for Freedoom assets

## Quick start

### Offline demo

From the repository root, serve the project with a static web server:

```bash
python -m http.server 8000
```

Then open:

```text
http://localhost:8000/smartdoom.html
```

This runs the app in offline mode and shows the QuestionnaireResponse JSON instead of submitting to a real EHR.

### SMART launch

The app supports a standard SMART launch flow:

- EHR launch: `smartdoom.html?launch=...&iss=...`
- Standalone launch: `smartdoom.html?iss=https://your-fhir-server/r4`
- Optional Questionnaire override: `&questionnaire=Questionnaire/<id>`

## How it works

The app loads a FHIR R4 Questionnaire resource with an attachment item that carries the WAD file. A custom item control (`doom`) tells the renderer to mount the real Doom engine for that item. While the player completes the level, the app updates the outcome items in the Questionnaire and can submit a QuestionnaireResponse back to the host FHIR server.

This repo is primarily an experiment and reference implementation for integrating a game-like assessment into a SMART-on-FHIR workflow.

## License and attribution

- The project code and scripts in this repository are provided for demonstration and experimentation.
- The game data (`freedoom1.wad`) is derived from Freedoom and retains the original Freedoom licensing terms.
- See `FREEDOOM-COPYING.txt` for the full asset licensing details.

## Notes

This is a demo project intended for educational and experimental use. It may require a modern browser and a properly configured SMART-enabled FHIR environment for full EHR integration.
