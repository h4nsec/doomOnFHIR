# Doom on FHIR

![Doom on FHIR logo](./Doom%20on%20FHIR%20Logo.png)

This repository contains two versions of the same concept:

1. An attachment-based SMART app that runs Doom inside a FHIR Questionnaire in the browser.
2. A pure FHIRPath version of the same Doom questionnaire that works in FHIRPath-capable SDC renderers without JavaScript.

Both versions are experiments in using FHIR Questionnaire mechanics as a vehicle for game-like clinical assessment logic.

## Repository contents

- `smartdoom.html` — browser-based SMART app using an attachment item and a custom `doom` item control
- `smartdoom-engine.js` — Doom engine bootstrap and runtime glue for the browser app
- `freedoom1.wad` — Freedoom Phase 1 game data used by the attachment version
- `doom-fhirpath-questionnaire.json` — the pure-FHIRPath version of the questionnaire
- `build/` — build scripts and platform-layer sources for the engine
- `FREEDOOM-COPYING.txt` — licensing details for the Freedoom assets

## Version 1: Attachment-based SMART app

The main app is `smartdoom.html`. It loads a standard FHIR Questionnaire with a custom item control named `doom` and an initial `valueAttachment` pointing at the Freedoom WAD. The browser mounts the actual Doom engine and updates QuestionnaireResponse data such as level status, kills, items, secrets, and time.

### How to run the attachment version

From the repo root:

```bash
python -m http.server 8000
```

Then open:

```text
http://localhost:8000/smartdoom.html
```

This runs in offline/demo mode by default. The resulting QuestionnaireResponse is shown in JSON instead of being posted to a live FHIR server.

For SMART launch flows, use:

- EHR launch: `smartdoom.html?launch=...&iss=...`
- Standalone launch: `smartdoom.html?iss=https://your-fhir-server/r4`
- Optional questionnaire override: `&questionnaire=Questionnaire/<id>`

This version is intended for a renderer or app that can understand the custom item control and handle attachment-based input data.

## Version 2: Pure FHIRPath questionnaire

The file `doom-fhirpath-questionnaire.json` is a different approach: it implements the Doom interaction entirely in FHIRPath expressions. There is no embedded JavaScript engine required in the host renderer. Instead, the questionnaire uses calculated expressions, variables, and repeat/aggregate logic to recreate the map, movement, ray-casting logic, and outcome values directly in FHIRPath.

This variant is meant for SDC renderers that support FHIRPath and SDC features, such as:

- NLM LHC-Forms
- CSIRO Smart Forms
- other FHIRPath-capable questionnaire renderers

### How to use the FHIRPath version

Load `doom-fhirpath-questionnaire.json` into a compatible FHIRPath-capable SDC renderer. It is not meant to be launched through `smartdoom.html`.

If you want the browser demo experience, use the attachment version. If you want a standards-only, renderer-agnostic Questionnaire implementation, use the FHIRPath version.

## Which version should I use?

Use the attachment version when you want:

- a playable browser-based Doom experience
- the real engine running in the page
- output captured as a QuestionnaireResponse from a SMART app

Use the FHIRPath version when you want:

- a pure data-driven Questionnaire
- compatibility with FHIRPath-capable renderers
- no JavaScript engine dependency in the host environment

## How the project works

The attachment-based app is a pragmatic demo of embedding a custom item control in a SMART Questionnaire. The FHIRPath-only version explores a more declarative approach: all the game logic lives in the Questionnaire as expressions, making it portable across SDC renderers.

## License and attribution

- The code in this repository is provided for demonstration and experimentation.
- `freedoom1.wad` is derived from Freedoom and remains subject to Freedoom licensing terms.
- See `FREEDOOM-COPYING.txt` for the full asset licensing information.

## Notes

This is a demo project intended for exploration, education, and experimental clinical workflow use. A full SMART EHR integration requires a properly configured FHIR server and a compatible renderer.
