# PED Classification Tool

Overhauled classification project for pressure equipment according to **Directive 2014/68/EU (PED)**.

The project now separates classification logic by equipment type and exposes:

- `Vessel` classification via dedicated PS/V table paths
- `Piping` classification via dedicated PS/DN rule paths
- `Steam/Hot water generators` via a dedicated Table 5 path
- `Pressure accessories` via the higher category of the applicable vessel and/or piping basis
- special-case flags for unstable gases, breathing apparatus / portable extinguishers, high-temperature piping, pressure cookers, and warm-water assemblies

## Project Structure

- [app.py](./app.py): Flask UI and JSON API
- [ped_engine.py](./ped_engine.py): standalone PED rule engine
- [templates/index.html](./templates/index.html): browser UI
- [tests/test_ped_engine.py](./tests/test_ped_engine.py): regression and rule tests

## Quick Start

```bash
pip install -r requirements.txt
python app.py
```

The application starts on `http://localhost:5050`.

## API

### `POST /api/pden/classify`

Example body:

```json
{
  "equipment_type": "Pressure accessories",
  "medium_state": "gaseous",
  "pressure": 20,
  "volume": 100,
  "diameter": 100,
  "medium_group": "Group 1 - dangerous",
  "unstable_gas": false,
  "portable_extinguisher_or_breathing_apparatus": false,
  "fluid_temperature_c": 25,
  "pressure_cooker": false,
  "warm_water_assembly": false
}
```

Example response:

```json
{
  "category": "Category IV",
  "procedure": "Module B (production type) or B (design type) with D or F; or Module G; or Module H1",
  "modules": ["B + D", "B + F", "G", "H1"],
  "table": "table_6",
  "basis": "Highest category from applicable vessel/piping basis",
  "scope": "PED Article 4 / Annex II",
  "notes": [
    "Pressure accessory evaluated against vessel table because volume is available.",
    "Pressure accessory evaluated against piping table because nominal size is available.",
    "Both vessel and piping bases were considered; the higher category was selected."
  ]
}
```

### `POST /api/pden/diagram`

Returns a PNG for PS/V-based equipment paths currently supported by the UI:

- `Vessel`
- `Steam/Hot water generators`
- `Pressure accessories` when volume is used

## Classification Notes

- `Pressure-bearing parts` is accepted as a legacy alias and normalized to `Pressure accessories`.
- `Pressure accessories` select the higher category when both volume and nominal size are provided.
- `Unstable gas` uplifts are applied for the Table 1 and Table 6 paths.
- `Portable extinguisher / breathing apparatus` uplift is applied for the Table 2 path.
- `Fluid temperature > 350 C` uplifts Category II to III for the Table 7 piping path.
- `Pressure cooker` forces at least a Category III-equivalent route in the dedicated steam-generator path.

## Verification

Run the regression tests with:

```bash
python -m unittest discover -s tests -v
```

## Compliance Boundary

This overhaul makes the project structurally much closer to a maintainable PED classifier, but it is still software and not a legal conformity decision on its own.

Two especially important boundaries remain:

- The project rule paths for piping and steam generators should still be verified point-by-point against the official Annex II graphics and the exact intended product scope.
- The result should be treated as engineering support output unless your compliance process formally validates the implemented demarcation data.
