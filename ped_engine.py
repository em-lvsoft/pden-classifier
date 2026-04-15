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

PIPELINE_THRESHOLDS = {
    ("gaseous", "Group 1 - dangerous"): [
        (1000, "Category IV"),
        (100, "Category III"),
        (50, "Category II"),
        (0, "Category I"),
    ],
    ("gaseous", "Group 2 - all others"): [
        (1000, "Category III"),
        (100, "Category II"),
        (50, "Category I"),
        (0, "Category 0"),
    ],
    ("liquid_low", "Group 1 - dangerous"): [
        (1000, "Category III"),
        (200, "Category II"),
        (50, "Category I"),
        (0, "Category 0"),
    ],
    ("liquid_low", "Group 2 - all others"): [
        (1000, "Category II"),
        (50, "Category I"),
        (0, "Category 0"),
    ],
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


def classify_piping(data: ClassificationInput) -> Tuple[str, str, List[str]]:
    diameter = ensure_positive("Diameter DN", data.diameter)
    thresholds = PIPELINE_THRESHOLDS.get((data.medium_state, data.medium_group))
    if thresholds is None:
        raise ValueError("Unsupported combination of medium state and medium group for piping.")

    notes = [
        "Piping is evaluated on a PS x DN basis in the current project rule set.",
        "For legally sensitive use, verify the project thresholds against PED Annex II Tables 6-9."
    ]
    ps_dn = data.pressure * diameter
    category = "Unknown Category"
    for threshold, candidate in thresholds:
        if ps_dn >= threshold:
            category = candidate
            break

    table_name = {
        ("gaseous", "Group 1 - dangerous"): "table_6",
        ("gaseous", "Group 2 - all others"): "table_7",
        ("liquid_low", "Group 1 - dangerous"): "table_8",
        ("liquid_low", "Group 2 - all others"): "table_9",
    }[(data.medium_state, data.medium_group)]

    if data.unstable_gas and table_name == "table_6" and category in {"Category I", "Category II"}:
        category = "Category III"
        notes.append("Unstable gas uplift applied: Table 6 piping in Category I/II moves to Category III.")

    if table_name == "table_7" and data.fluid_temperature_c is not None and data.fluid_temperature_c > 350 and category == "Category II":
        category = "Category III"
        notes.append("High-temperature uplift applied: Table 7 piping above 350 C in Category II moves to Category III.")

    return category, table_name, notes


def classify_pressure_accessory(data: ClassificationInput) -> Tuple[str, str, List[str]]:
    candidates: List[Tuple[str, str]] = []
    notes: List[str] = []

    if data.volume and data.volume > 0:
        vessel_category, vessel_table, vessel_notes = classify_vessel(data)
        candidates.append((vessel_category, vessel_table))
        notes.extend(vessel_notes)
        notes.append("Pressure accessory evaluated against vessel table because volume is available.")

    if data.diameter and data.diameter > 0:
        piping_category, piping_table, piping_notes = classify_piping(data)
        candidates.append((piping_category, piping_table))
        notes.extend(piping_notes)
        notes.append("Pressure accessory evaluated against piping table because nominal size is available.")

    if not candidates:
        raise ValueError("Pressure accessories require at least volume or diameter to determine the applicable table.")

    category, table_name = candidates[0]
    for candidate_category, candidate_table in candidates[1:]:
        if CATEGORY_ORDER.get(candidate_category, -1) > CATEGORY_ORDER.get(category, -1):
            category = candidate_category
            table_name = candidate_table

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


def diagram_table_for_input(data: ClassificationInput) -> Tuple[Optional[str], Optional[float], str]:
    data.equipment_type = normalize_equipment_type(data.equipment_type)
    if data.equipment_type == "Vessel":
        return vessel_table_for_input(data), ensure_positive("Volume", data.volume), "Volume (L)"
    if data.equipment_type == "Steam/Hot water generators":
        return "table_5", ensure_positive("Volume", data.volume), "Volume (L)"
    if data.equipment_type == "Pressure accessories" and data.volume and data.volume > 0:
        return vessel_table_for_input(data), data.volume, "Volume (L)"
    return None, None, "N/A"


def generate_ped_diagram(data: ClassificationInput) -> io.BytesIO:
    from matplotlib import pyplot as plt

    table_name, x_value, x_label = diagram_table_for_input(data)
    if table_name is None or x_value is None:
        raise ValueError("Diagram generation is available only for PS/V-based equipment in this project version.")

    coordinates = TABLE_POLYGONS[table_name]
    fig, ax = plt.subplots(figsize=(10, 7))

    colors = {
        "cat_0": ("#B0E0E6", 0.4, "Category 0"),
        "cat_i": ("#90EE90", 0.7, "Category I"),
        "cat_ib": ("#90EE90", 0.7, "Category I"),
        "cat_ii": ("#FFFF99", 0.7, "Category II"),
        "cat_iib": ("#FFFF99", 0.7, "Category II"),
        "cat_iii": ("#FFDAB9", 0.7, "Category III"),
        "cat_iv": ("#FFB6C1", 0.7, "Category IV"),
    }

    for poly_key, (color, alpha, label) in colors.items():
        if poly_key in coordinates:
            ax.fill(coordinates[poly_key]["x"], coordinates[poly_key]["y"], color=color, alpha=alpha, label=label)

    ax.plot(x_value, data.pressure, "bo", markersize=8, label=f"Equipment (PS={data.pressure} bar)")
    ax.set_xlabel(x_label)
    ax.set_ylabel("Pressure (bar)")
    ax.set_title(f"PED Classification: {data.equipment_type} - {table_name.replace('_', ' ').title()}")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(0.1, 100000)
    ax.set_ylim(0.1, 10000)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=3)
    plt.tight_layout(rect=[0, 0, 1, 0.95])

    img = io.BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    plt.close(fig)
    return img
