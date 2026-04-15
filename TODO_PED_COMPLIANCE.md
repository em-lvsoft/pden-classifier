# PED Compliance - Current Status After Overhaul

This repository now has a dedicated PED engine with explicit rule paths for:

- vessels
- piping
- steam / hot-water generators
- pressure accessories
- special-case uplifts and notes

That is a substantial step forward from the previous mixed logic, but a few compliance-oriented follow-ups still matter if the project is meant to support production conformity decisions.

## 1. Verify Annex II demarcation data line-by-line

**Priority:** High

The project now has explicit table routing, but the exact geometric demarcation data still needs formal verification against the official Annex II tables, especially for:

- Table 5
- Tables 6 to 9

## 2. Confirm intended scope for pressure accessories

**Priority:** High

The engine now evaluates pressure accessories on both vessel and piping bases and selects the higher category when both inputs are present. That matches the directive's general logic, but the product team should still confirm which accessory families are intended to be supported by the UI and API.

## 3. Decide whether provisional piping thresholds should be replaced by explicit polygons

**Priority:** High

The current overhaul gives piping its own rule path and special-case handling. If the goal is a diagram-faithful implementation of Annex II Tables 6 to 9, the next step is to replace the project threshold bands with formally reviewed line definitions or polygons.

## 4. Expand regression cases from legal source material

**Priority:** Medium

The repository now includes automated tests. The next improvement is to add authoritative reference cases derived from:

- internal compliance examples
- approved engineering calculations
- officially interpreted boundary cases, if available

## 5. Clarify "engineering support" versus "formal conformity decision"

**Priority:** Medium

The README now calls out the boundary, but if this is exposed to end users, the UI and API responses should also state whether the result is:

- an engineering pre-classification
- an internal compliance aid
- a formally validated classification output
