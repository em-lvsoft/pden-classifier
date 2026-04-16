from __future__ import annotations

from dataclasses import dataclass, field
import io
import math
from typing import Any, Dict, List, Optional, Tuple

CATEGORY_ORDER = {
    "Not subject to PED": -1,
    "Category 0": 0,
    "Category I": 1,
    "Category II": 2,
    "Category III": 3,
    "Category IV": 4,
    "Unknown Category": 99,
}

CATEGORY_MODULES = {
    "Category 0": ["Art. 4(3) good engineering practice"],
    "Category I": ["A"],
    "Category II": ["A2", "D1", "E1"],
    "Category III": ["B + C2", "B + D", "B + E", "B + F", "H"],
    "Category IV": ["B + D", "B + F", "G", "H1"],
}

CONFORMITY_PROCEDURES = {
    "Category IV": "Module B (production type) or B (design type) with D or F; or Module G; or Module H1",
    "Category III": "Module B (production type) or B (design type) with C2, D, E or F; or Module H",
    "Category II": "Module A2, D1 or E1",
    "Category I": "Module A (internal production control)",
    "Category 0": "Art. 4(3) sound engineering practice; no notified body involvement",
    "Not subject to PED": "Not applicable",
}

TABLE_POLYGONS = {
    "table_1": {
        "cat_0": {"x": [0.1, 100000, 100000, 50, 1, 1, 0.1], "y": [0.1, 0.1, 0.5, 0.5, 25, 200, 200]},
        "cat_i": {"x": [1, 50, 100, 1], "y": [25, 0.5, 0.5, 50]},
        "cat_ii": {"x": [1, 100, 400, 1], "y": [50, 0.5, 0.5, 200]},
        "cat_iii": {"x": [0.1, 1, 400, 2000, 1, 0.1], "y": [200, 200, 0.5, 0.5, 1000, 1000]},
        "cat_iv": {"x": [0.1, 1, 2000, 100000, 100000, 0.1], "y": [1000, 1000, 0.5, 0.5, 10000, 10000]},
    },
    "table_2": {
        "cat_0": {"x": [0.1, 100000, 100000, 100, 1, 1, 0.1], "y": [0.1, 0.1, 0.5, 0.5, 50, 1000, 1000]},
        "cat_i": {"x": [1, 100, 400, 1], "y": [50, 0.5, 0.5, 200]},
        "cat_ii": {"x": [1, 400, 2000, 1], "y": [200, 0.5, 0.5, 1000]},
        "cat_iii": {"x": [0.1, 1, 2000, 100000, 100000, 1000, 1, 0.1], "y": [1000, 1000, 0.5, 0.5, 4, 4, 3000, 3000]},
        "cat_iv": {"x": [0.1, 1, 1000, 100000, 100000, 0.1], "y": [3000, 3000, 4, 4, 10000, 10000]},
    },
    "table_3": {
        "cat_0": {"x": [0.1, 100000, 100000, 400, 1, 1, 0.1], "y": [0.1, 0.1, 0.5, 0.5, 200, 500, 500]},
        "cat_i": {"x": [20, 400, 100000, 100000], "y": [10, 0.5, 0.5, 10]},
        "cat_ii": {"x": [1, 1, 20, 100000, 100000], "y": [500, 200, 10, 10, 500]},
        "cat_iib": {"x": [0.1, 1, 1, 0.1], "y": [500, 500, 10000, 10000]},
        "cat_iii": {"x": [1, 100000, 100000, 1], "y": [500, 500, 10000, 10000]},
    },
    "table_4": {
        "cat_0": {"x": [0.1, 0.1, 100000, 100000, 1000, 10], "y": [1000, 0.1, 0.1, 10, 10, 1000]},
        "cat_i": {"x": [0.1, 10, 10, 0.1], "y": [1000, 1000, 10000, 10000]},
        "cat_ib": {"x": [20, 1000, 100000, 100000], "y": [500, 10, 10, 500]},
        "cat_ii": {"x": [10, 10, 20, 100000, 100000], "y": [10000, 1000, 500, 500, 10000]},
    },
    # This dedicated path makes steam generators explicit in the engine.
    # The table_5 envelope currently reuses the project's PS/V risk model
    # until the original Annex II table is transcribed point-by-point.
    "table_5": {
        "cat_0": {"x": [0.1, 100000, 100000, 100, 1, 1, 0.1], "y": [0.1, 0.1, 0.5, 0.5, 50, 1000, 1000]},
        "cat_i": {"x": [1, 100, 400, 1], "y": [50, 0.5, 0.5, 200]},
        "cat_ii": {"x": [1, 400, 2000, 1], "y": [200, 0.5, 0.5, 1000]},
        "cat_iii": {"x": [0.1, 1, 2000, 100000, 100000, 1000, 1, 0.1], "y": [1000, 1000, 0.5, 0.5, 4, 4, 3000, 3000]},
        "cat_iv": {"x": [0.1, 1, 1000, 100000, 100000, 0.1], "y": [3000, 3000, 4, 4, 10000, 10000]},
    },
}

# Piping classification rules per PED 2014/68/EU Annex II, Tables 6-9.
# Each rule set defines:
#   - scope_entry: combined conditions from Article 4(1)(c) to enter PED scope
#   - categories:  checked highest-first; first match wins
# Internal category boundaries are approximations read from the Annex II
# charts and should be verified point-by-point for production use.
PIPING_RULES = {
    # Table 6: Gas / vapour, Group 1 (dangerous)
    # Scope entry (Art. 4(1)(c)): DN > 25
    # Internal boundaries per Annex II Table 6 isopleths PS·DN = 25, 350, 1000.
    ("gaseous", "Group 1 - dangerous"): {
        "table": "table_6",
        "scope_entry": {"dn_gt": 25, "ps_dn_gt": 25},
        "categories": [
            {"category": "Category III", "ps_dn_gt": 1000},
            {"category": "Category II", "ps_dn_gt": 350},
            {"category": "Category I"},
        ],
    },
    # Table 7: Gas / vapour, Group 2
    # Scope entry (Art. 4(1)(c)): DN > 32 AND PS·DN > 1000
    # Internal boundaries per Annex II Table 7: PS·DN = 3500 (Cat I/II),
    # PS·DN = 5000 with DN > 250 (Cat II/III).
    ("gaseous", "Group 2 - all others"): {
        "table": "table_7",
        "scope_entry": {"dn_gt": 32, "ps_dn_gt": 1000},
        "categories": [
            {"category": "Category III", "dn_gt": 250, "ps_dn_gt": 5000},
            {"category": "Category II", "dn_gt": 100, "ps_dn_gt": 3500},
            {"category": "Category I"},
        ],
    },
    # Table 8: Liquid (VP ≤ 0.5 bar), Group 1 (dangerous)
    # Scope entry (Art. 4(1)(c)): DN > 25 AND PS·DN > 2000
    # TODO: Internal Cat II/III boundaries still need line-by-line verification
    # against the official Annex II Table 8 graphic.
    ("liquid_low", "Group 1 - dangerous"): {
        "table": "table_8",
        "scope_entry": {"dn_gt": 25, "ps_dn_gt": 2000},
        "categories": [
            {"category": "Category III", "dn_gt": 200, "ps_dn_gt": 10000},
            {"category": "Category II", "dn_gt": 100, "ps_dn_gt": 5000},
            {"category": "Category I"},
        ],
    },
    # Table 9: Liquid (VP ≤ 0.5 bar), Group 2
    # Scope entry (Art. 4(1)(c)): PS > 10 AND DN > 200 AND PS·DN > 5000
    # Only Category I exists in this table per PED.
    ("liquid_low", "Group 2 - all others"): {
        "table": "table_9",
        "scope_entry": {"ps_gt": 10, "dn_gt": 200, "ps_dn_gt": 5000},
        "categories": [
            {"category": "Category I"},
        ],
    },
}

POLYGON_ORDER = [
    ("cat_iv", "Category IV"),
    ("cat_iii", "Category III"),
    ("cat_iib", "Category II"),
    ("cat_ii", "Category II"),
    ("cat_ib", "Category I"),
    ("cat_i", "Category I"),
    ("cat_0", "Category 0"),
]

# --- Diagram styling ---------------------------------------------------------
# Risk-semantic palette (neutral → green → amber → orange → red).
CATEGORY_COLORS = {
    "Category 0":   "#B0BEC5",
    "Category I":   "#66BB6A",
    "Category II":  "#FFCA28",
    "Category III": "#FB8C00",
    "Category IV":  "#E53935",
}

POLYGON_CATEGORY_KEY = {
    "cat_0": "Category 0",
    "cat_i": "Category I",
    "cat_ib": "Category I",
    "cat_ii": "Category II",
    "cat_iib": "Category II",
    "cat_iii": "Category III",
    "cat_iv": "Category IV",
}

TABLE_DESCRIPTIONS = {
    "table_1": "Vessels \u2014 Gases / Group 1 (dangerous)",
    "table_2": "Vessels \u2014 Gases / Group 2",
    "table_3": "Vessels \u2014 Liquids / Group 1 (dangerous)",
    "table_4": "Vessels \u2014 Liquids / Group 2",
    "table_5": "Steam / Hot-water generators",
    "table_6": "Piping \u2014 Gases / Group 1 (dangerous)",
    "table_7": "Piping \u2014 Gases / Group 2",
    "table_8": "Piping \u2014 Liquids / Group 1 (dangerous)",
    "table_9": "Piping \u2014 Liquids / Group 2",
}

# PS·V (vessels) or PS·DN (piping) isopleths annotated on each diagram.
# These are the Annex II demarcation lines; drawing them as guide lines
# lets an engineer read off the exact threshold they are crossing.
TABLE_ISOPLETHS = {
    "table_1": [25, 50, 200, 1000],
    "table_2": [50, 200, 1000, 3000],
    "table_3": [200, 500, 10000],
    "table_4": [1000, 10000],
    "table_5": [50, 200, 1000, 3000],
    "table_6": [25, 350, 1000],
    "table_7": [1000, 3500, 5000],
    "table_8": [2000, 5000, 10000],
    "table_9": [5000],
}


@dataclass
class ClassificationInput:
    equipment_type: str
    medium_state: str
    pressure: float
    medium_group: str
    volume: Optional[float] = None
    diameter: Optional[float] = None
    unstable_gas: bool = False
    portable_extinguisher_or_breathing_apparatus: bool = False
    fluid_temperature_c: Optional[float] = None
    pressure_cooker: bool = False
    warm_water_assembly: bool = False


@dataclass
class ClassificationResult:
    category: str
    procedure: str
    modules: List[str]
    table: Optional[str]
    basis: str
    scope: str
    notes: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "procedure": self.procedure,
            "modules": self.modules,
            "table": self.table,
            "basis": self.basis,
            "scope": self.scope,
            "notes": self.notes,
        }


def is_inside(x: float, y: float, poly_x: List[float], poly_y: List[float]) -> bool:
    log_x = math.log10(x)
    log_y = math.log10(y)
    polygon = [(math.log10(px), math.log10(py)) for px, py in zip(poly_x, poly_y)]
    inside = False
    point_count = len(polygon)
    epsilon = 1e-9

    for index in range(point_count):
        x1, y1 = polygon[index]
        x2, y2 = polygon[(index + 1) % point_count]

        cross = (log_x - x1) * (y2 - y1) - (log_y - y1) * (x2 - x1)
        if abs(cross) < epsilon:
            min_x = min(x1, x2) - epsilon
            max_x = max(x1, x2) + epsilon
            min_y = min(y1, y2) - epsilon
            max_y = max(y1, y2) + epsilon
            if min_x <= log_x <= max_x and min_y <= log_y <= max_y:
                # Point lies on polygon edge — treat as inside so that
                # the higher-category-first check order assigns the
                # stricter category per PED directive.
                return True

        if (y1 > log_y) != (y2 > log_y):
            x_intersection = (x2 - x1) * (log_y - y1) / (y2 - y1) + x1
            if log_x < x_intersection:
                inside = not inside

    return inside


def higher_category(category_a: str, category_b: str) -> str:
    rank_a = CATEGORY_ORDER.get(category_a, -999)
    rank_b = CATEGORY_ORDER.get(category_b, -999)
    return category_a if rank_a >= rank_b else category_b


def normalize_equipment_type(equipment_type: str) -> str:
    aliases = {
        "Pressure-bearing parts": "Pressure accessories",
    }
    return aliases.get(equipment_type, equipment_type)


def ensure_positive(name: str, value: Optional[float]) -> float:
    if value is None:
        raise ValueError(f"{name} is required.")
    if value <= 0:
        raise ValueError(f"{name} must be greater than 0.")
    return value


def determine_polygon_category(table_name: str, x_value: float, pressure: float) -> str:
    coordinates = TABLE_POLYGONS.get(table_name)
    if not coordinates:
        return "Unknown Category"

    for poly_key, category in POLYGON_ORDER:
        if poly_key in coordinates and is_inside(x_value, pressure, coordinates[poly_key]["x"], coordinates[poly_key]["y"]):
            return category
    return "Unknown Category"


def vessel_table_for_input(data: ClassificationInput) -> str:
    if data.medium_state == "gaseous" and data.medium_group == "Group 1 - dangerous":
        return "table_1"
    if data.medium_state == "gaseous" and data.medium_group == "Group 2 - all others":
        return "table_2"
    if data.medium_state == "liquid_low" and data.medium_group == "Group 1 - dangerous":
        return "table_3"
    if data.medium_state == "liquid_low" and data.medium_group == "Group 2 - all others":
        return "table_4"
    raise ValueError("Unsupported combination of medium state and medium group.")


def classify_vessel(data: ClassificationInput) -> Tuple[str, str, List[str]]:
    volume = ensure_positive("Volume", data.volume)
    table_name = vessel_table_for_input(data)
    category = determine_polygon_category(table_name, volume, data.pressure)
    notes: List[str] = []

    if data.unstable_gas and table_name == "table_1" and category in {"Category I", "Category II"}:
        category = "Category III"
        notes.append("Unstable gas uplift applied: vessels from Table 1 in Category I/II move to Category III.")

    if data.portable_extinguisher_or_breathing_apparatus and table_name == "table_2" and CATEGORY_ORDER.get(category, -1) < CATEGORY_ORDER["Category III"]:
        category = "Category III"
        notes.append("Portable extinguisher / breathing apparatus uplift applied: minimum Category III.")

    if data.warm_water_assembly and table_name == "table_4":
        notes.append("Warm-water assembly note: Module B (design type) or Module H is required for Annex I points listed in PED Annex II Table 4 note.")

    return category, table_name, notes


def classify_steam_generator(data: ClassificationInput) -> Tuple[str, str, List[str]]:
    volume = ensure_positive("Volume", data.volume)
    category = determine_polygon_category("table_5", volume, data.pressure)
    notes = [
        "Steam/hot-water generator classification is routed through a dedicated Table 5 path.",
        "The project still needs line-by-line verification of the Table 5 demarcation coordinates against the official Annex II graphic.",
    ]

    if data.pressure_cooker and CATEGORY_ORDER.get(category, -1) < CATEGORY_ORDER["Category III"]:
        category = "Category III"
        notes.append("Pressure cooker design uplift applied: at least one Category III equivalent conformity route is required.")

    return category, "table_5", notes


def _piping_scope_check(entry: Dict, ps: float, dn: float, ps_dn: float) -> bool:
    """Return True if the equipment meets ALL scope-entry conditions."""
    if "ps_gt" in entry and ps <= entry["ps_gt"]:
        return False
    if "dn_gt" in entry and dn <= entry["dn_gt"]:
        return False
    if "ps_dn_gt" in entry and ps_dn <= entry["ps_dn_gt"]:
        return False
    return True


def _piping_rule_matches(rule: Dict[str, Any], ps: float, dn: float, ps_dn: float) -> bool:
    if "ps_gt" in rule and ps <= rule["ps_gt"]:
        return False
    if "dn_gt" in rule and dn <= rule["dn_gt"]:
        return False
    if "ps_dn_gt" in rule and ps_dn <= rule["ps_dn_gt"]:
        return False
    return True


def determine_piping_base_category(rule_set: Dict[str, Any], ps: float, dn: float) -> str:
    ps_dn = ps * dn
    if not _piping_scope_check(rule_set["scope_entry"], ps, dn, ps_dn):
        return "Category 0"

    for rule in rule_set["categories"]:
        if _piping_rule_matches(rule, ps, dn, ps_dn):
            return rule["category"]

    return "Category I"


def classify_piping(data: ClassificationInput) -> Tuple[str, str, List[str]]:
    diameter = ensure_positive("Diameter DN", data.diameter)
    rule_set = PIPING_RULES.get((data.medium_state, data.medium_group))
    if rule_set is None:
        raise ValueError("Unsupported combination of medium state and medium group for piping.")

    table_name = rule_set["table"]
    ps_dn = data.pressure * diameter
    notes = [
        "Piping classification uses combined PS, DN, and PS\u00d7DN conditions per Annex II.",
        "Internal category boundaries are approximate — verify against official Annex II charts for production use.",
    ]

    base_category = determine_piping_base_category(rule_set, data.pressure, diameter)

    # Check scope entry (Article 4(1)(c))
    if base_category == "Category 0":
        return "Category 0", table_name, notes + [
            f"Below PED scope for {table_name.replace('_', ' ').title()}: "
            f"PS={data.pressure} bar, DN={diameter}, PS\u00d7DN={ps_dn:.0f}."
        ]

    category = base_category

    # Special-case uplifts
    if data.unstable_gas and table_name == "table_6" and category in {"Category I", "Category II"}:
        category = "Category III"
        notes.append("Unstable gas uplift applied: Table 6 piping in Category I/II moves to Category III.")

    if table_name == "table_7" and data.fluid_temperature_c is not None and data.fluid_temperature_c > 350 and category == "Category II":
        category = "Category III"
        notes.append("High-temperature uplift applied: Table 7 piping above 350\u00b0C in Category II moves to Category III.")

    return category, table_name, notes


def _pressure_accessory_candidates(data: ClassificationInput) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []

    if data.volume and data.volume > 0:
        vessel_category, vessel_table, vessel_notes = classify_vessel(data)
        candidates.append(
            {
                "basis": "vessel",
                "category": vessel_category,
                "table": vessel_table,
                "x_value": data.volume,
                "x_label": "Volume (L)",
                "notes": vessel_notes,
            }
        )

    if data.diameter and data.diameter > 0:
        piping_category, piping_table, piping_notes = classify_piping(data)
        candidates.append(
            {
                "basis": "piping",
                "category": piping_category,
                "table": piping_table,
                "x_value": data.diameter,
                "x_label": "DN",
                "notes": piping_notes,
            }
        )

    return candidates


def classify_pressure_accessory(data: ClassificationInput) -> Tuple[str, str, List[str]]:
    candidates = _pressure_accessory_candidates(data)
    notes: List[str] = []

    for candidate in candidates:
        notes.extend(candidate["notes"])
        if candidate["basis"] == "vessel":
            notes.append("Pressure accessory evaluated against vessel table because volume is available.")
        else:
            notes.append("Pressure accessory evaluated against piping table because nominal size is available.")

    if not candidates:
        raise ValueError("Pressure accessories require at least volume or diameter to determine the applicable table.")

    category = candidates[0]["category"]
    table_name = candidates[0]["table"]
    for candidate in candidates[1:]:
        if CATEGORY_ORDER.get(candidate["category"], -1) > CATEGORY_ORDER.get(category, -1):
            category = candidate["category"]
            table_name = candidate["table"]

    if len(candidates) > 1:
        notes.append("Both vessel and piping bases were considered; the higher category was selected.")

    return category, table_name, notes


def classify_ped(data: ClassificationInput) -> ClassificationResult:
    data.equipment_type = normalize_equipment_type(data.equipment_type)
    if data.pressure <= 0.5:
        return ClassificationResult(
            category="Not subject to PED",
            procedure=CONFORMITY_PROCEDURES["Not subject to PED"],
            modules=[],
            table=None,
            basis="Pressure at or below 0.5 bar",
            scope="Outside PED scope",
            notes=["Pressure equipment with PS <= 0.5 bar is outside PED scope."],
        )

    if data.equipment_type == "Vessel":
        category, table_name, notes = classify_vessel(data)
        basis = "PS and volume"
    elif data.equipment_type == "Piping":
        category, table_name, notes = classify_piping(data)
        basis = "PS and nominal size"
    elif data.equipment_type == "Steam/Hot water generators":
        category, table_name, notes = classify_steam_generator(data)
        basis = "PS and volume"
    elif data.equipment_type == "Pressure accessories":
        category, table_name, notes = classify_pressure_accessory(data)
        basis = "Highest category from applicable vessel/piping basis"
    else:
        raise ValueError(f"Unsupported equipment type: {data.equipment_type}")

    return ClassificationResult(
        category=category,
        procedure=CONFORMITY_PROCEDURES.get(category, "Not applicable"),
        modules=CATEGORY_MODULES.get(category, []),
        table=table_name,
        basis=basis,
        scope="PED Article 4 / Annex II",
        notes=notes,
    )


def resolve_diagram_target(data: ClassificationInput) -> Tuple[Optional[str], Optional[float], str]:
    data.equipment_type = normalize_equipment_type(data.equipment_type)
    if data.equipment_type == "Vessel":
        return vessel_table_for_input(data), ensure_positive("Volume", data.volume), "Volume (L)"
    if data.equipment_type == "Steam/Hot water generators":
        return "table_5", ensure_positive("Volume", data.volume), "Volume (L)"
    if data.equipment_type == "Pressure accessories":
        candidates = _pressure_accessory_candidates(data)
        if not candidates:
            return None, None, "N/A"
        selected = candidates[0]
        for candidate in candidates[1:]:
            if CATEGORY_ORDER.get(candidate["category"], -1) > CATEGORY_ORDER.get(selected["category"], -1):
                selected = candidate
        return selected["table"], selected["x_value"], selected["x_label"]
    if data.equipment_type == "Piping":
        table_name = {
            ("gaseous", "Group 1 - dangerous"): "table_6",
            ("gaseous", "Group 2 - all others"): "table_7",
            ("liquid_low", "Group 1 - dangerous"): "table_8",
            ("liquid_low", "Group 2 - all others"): "table_9",
        }.get((data.medium_state, data.medium_group))
        if table_name and data.diameter and data.diameter > 0:
            return table_name, data.diameter, "DN"
    return None, None, "N/A"


def diagram_table_for_input(data: ClassificationInput) -> Tuple[Optional[str], Optional[float], str]:
    return resolve_diagram_target(data)


def classify_piping_for_diagram(rule_set: Dict[str, Any], ps_grid: Any, dn_grid: Any) -> Any:
    import numpy as np

    result = np.full(ps_grid.shape, "Category 0", dtype=object)
    flat_ps = ps_grid.ravel()
    flat_dn = dn_grid.ravel()
    flat_result = result.ravel()

    for index, (ps, dn) in enumerate(zip(flat_ps, flat_dn)):
        flat_result[index] = determine_piping_base_category(rule_set, float(ps), float(dn))

    return result


def _style_axes(ax, x_label: str, y_label: str, title: str,
                x_lim: Tuple[float, float], y_lim: Tuple[float, float]) -> None:
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(*x_lim)
    ax.set_ylim(*y_lim)
    ax.set_xlabel(x_label, fontsize=11, color="#263238")
    ax.set_ylabel(y_label, fontsize=11, color="#263238")
    ax.set_title(title, fontsize=12.5, pad=12, loc="left", fontweight="semibold", color="#1A237E")
    ax.grid(which="major", linestyle="-", linewidth=0.5, alpha=0.35, color="#546E7A")
    ax.grid(which="minor", linestyle=":", linewidth=0.3, alpha=0.25, color="#78909C")
    ax.tick_params(colors="#37474F", labelsize=9)
    for spine in ax.spines.values():
        spine.set_color("#37474F")
        spine.set_linewidth(1.0)


def _draw_isopleths(ax, table_name: str, x_lim: Tuple[float, float],
                    y_lim: Tuple[float, float], product_axis: str) -> None:
    """Draw PS·x = const diagonals (slope -1 in log-log) as guide lines."""
    label_prefix = "PS\u00b7DN" if product_axis == "dn" else "PS\u00b7V"
    for const in TABLE_ISOPLETHS.get(table_name, []):
        x_from_y_max = const / y_lim[1]
        x_from_y_min = const / y_lim[0]
        x_start = max(x_lim[0], x_from_y_max)
        x_end = min(x_lim[1], x_from_y_min)
        if x_start >= x_end:
            continue
        y_start = const / x_start
        y_end = const / x_end
        ax.plot([x_start, x_end], [y_start, y_end],
                linestyle="--", linewidth=0.7, color="#37474F",
                alpha=0.55, zorder=2.5)
        ax.text(x_start * 1.15, y_start * 0.82,
                f"{label_prefix} = {const}",
                fontsize=7.5, color="#263238", alpha=0.9, zorder=3,
                bbox=dict(boxstyle="round,pad=0.18", fc="white",
                          ec="#CFD8DC", lw=0.4, alpha=0.85))


def _annotate_equipment_point(ax, x: float, y: float, x_label_short: str,
                              x_lim: Tuple[float, float],
                              y_lim: Tuple[float, float]) -> None:
    ax.plot(x, y, marker="o", markersize=11,
            markeredgecolor="#0D47A1", markerfacecolor="#1E88E5",
            markeredgewidth=1.6, zorder=10)
    label = f"Equipment\nPS = {y:g} bar\n{x_label_short} = {x:g}"
    log_x = math.log10(x)
    log_y = math.log10(y)
    x_offset = 55 if (log_x - math.log10(x_lim[0])) < (math.log10(x_lim[1]) - log_x) else -55
    y_offset = 35 if (log_y - math.log10(y_lim[0])) < (math.log10(y_lim[1]) - log_y) else -35
    ax.annotate(
        label,
        xy=(x, y),
        xytext=(x_offset, y_offset),
        textcoords="offset points",
        arrowprops=dict(arrowstyle="->", color="#0D47A1", lw=1.2,
                        connectionstyle="arc3,rad=0.12"),
        bbox=dict(boxstyle="round,pad=0.4", fc="white",
                  ec="#0D47A1", lw=1.0, alpha=0.95),
        fontsize=9, color="#0D47A1", zorder=11,
    )


def _log_centroid(xs: List[float], ys: List[float]) -> Tuple[float, float]:
    log_xs = [math.log10(v) for v in xs]
    log_ys = [math.log10(v) for v in ys]
    return 10 ** (sum(log_xs) / len(log_xs)), 10 ** (sum(log_ys) / len(log_ys))


def _label_region(ax, x: float, y: float, text: str, category: str) -> None:
    ax.text(x, y, text, fontsize=11, fontweight="bold",
            color="#1A237E", ha="center", va="center", zorder=4,
            bbox=dict(boxstyle="round,pad=0.28",
                      fc=CATEGORY_COLORS.get(category, "#FFFFFF"),
                      ec="#37474F", lw=0.6, alpha=0.85))


def _build_figure():
    from matplotlib import pyplot as plt
    fig, ax = plt.subplots(figsize=(10.5, 7.2), dpi=110)
    fig.patch.set_facecolor("#FAFAFA")
    ax.set_facecolor("#FFFFFF")
    return fig, ax


def _save_figure(fig) -> io.BytesIO:
    from matplotlib import pyplot as plt
    fig.tight_layout()
    img = io.BytesIO()
    fig.savefig(img, format="png", bbox_inches="tight", facecolor=fig.get_facecolor())
    img.seek(0)
    plt.close(fig)
    return img


def _build_title(table_name: str) -> str:
    description = TABLE_DESCRIPTIONS.get(table_name, table_name.replace("_", " ").title())
    table_label = table_name.replace("_", " ").title()
    return f"PED Annex II {table_label}  \u2014  {description}"


def _generate_piping_diagram(data: ClassificationInput, table_name: str, dn_value: float) -> io.BytesIO:
    import numpy as np

    rule_set = PIPING_RULES.get((data.medium_state, data.medium_group))
    if rule_set is None:
        raise ValueError("No piping rules for this medium combination.")

    fig, ax = _build_figure()

    dn_min, dn_max = 1, 2000
    ps_min, ps_max = 0.5, 1000
    dn_range = np.logspace(np.log10(dn_min), np.log10(dn_max), 360)
    ps_range = np.logspace(np.log10(ps_min), np.log10(ps_max), 360)
    dn_grid, ps_grid = np.meshgrid(dn_range, ps_range)
    category_grid = classify_piping_for_diagram(rule_set, ps_grid, dn_grid)

    category_order = ["Category 0", "Category I", "Category II", "Category III"]
    for category in category_order:
        mask = category_grid == category
        if not mask.any():
            continue
        alpha = 0.38 if category == "Category 0" else 0.52
        ax.contourf(
            dn_grid, ps_grid, mask.astype(float),
            levels=[0.5, 1.5],
            colors=[CATEGORY_COLORS[category]],
            alpha=alpha, zorder=1,
        )
        log_dn = np.log10(dn_grid[mask])
        log_ps = np.log10(ps_grid[mask])
        label_x = 10 ** log_dn.mean()
        label_y = 10 ** log_ps.mean()
        text = "SEP / Art. 4(3)" if category == "Category 0" else category
        _label_region(ax, label_x, label_y, text, category)

    _draw_isopleths(ax, table_name, (dn_min, dn_max), (ps_min, ps_max), product_axis="dn")
    _annotate_equipment_point(ax, dn_value, data.pressure, "DN",
                              (dn_min, dn_max), (ps_min, ps_max))
    _style_axes(ax, "DN (nominal diameter)", "PS (bar)",
                _build_title(table_name),
                (dn_min, dn_max), (ps_min, ps_max))
    return _save_figure(fig)


def generate_ped_diagram(data: ClassificationInput) -> io.BytesIO:
    table_name, x_value, x_label = diagram_table_for_input(data)
    if table_name is None or x_value is None:
        raise ValueError("Diagram generation is not available for this equipment configuration.")

    if data.equipment_type == "Piping" or (
        data.equipment_type == "Pressure accessories"
        and table_name.startswith("table_")
        and int(table_name.split("_")[1]) >= 6
    ):
        return _generate_piping_diagram(data, table_name, x_value)

    coordinates = TABLE_POLYGONS[table_name]
    fig, ax = _build_figure()

    x_lim = (0.1, 100000)
    y_lim = (0.1, 10000)

    # Fill polygons from lowest risk to highest so higher categories
    # paint on top; use a consistent palette and mid alpha.
    fill_order = ["cat_0", "cat_i", "cat_ib", "cat_ii", "cat_iib", "cat_iii", "cat_iv"]
    for poly_key in fill_order:
        if poly_key not in coordinates:
            continue
        category = POLYGON_CATEGORY_KEY[poly_key]
        color = CATEGORY_COLORS[category]
        alpha = 0.38 if category == "Category 0" else 0.55
        xs = coordinates[poly_key]["x"]
        ys = coordinates[poly_key]["y"]
        ax.fill(xs, ys, color=color, alpha=alpha, zorder=1,
                edgecolor="#37474F", linewidth=0.5)
        label_x, label_y = _log_centroid(xs, ys)
        text = "SEP / Art. 4(3)" if category == "Category 0" else category
        _label_region(ax, label_x, label_y, text, category)

    _draw_isopleths(ax, table_name, x_lim, y_lim, product_axis="v")
    _annotate_equipment_point(ax, x_value, data.pressure,
                              "V" if "Volume" in x_label else x_label,
                              x_lim, y_lim)
    _style_axes(ax, x_label, "PS (bar)", _build_title(table_name), x_lim, y_lim)
    return _save_figure(fig)
