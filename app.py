from flask import Flask, render_template, request, jsonify, send_file
import numpy as np
import math
import io
import logging
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from matplotlib.path import Path

app = Flask(__name__)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# ── PED Category Modules ──────────────────────────────────────────────
CATEGORY_MODULES = {
    "Category 0": ["acc. Art. 4 para. (3) good engineering practice"],
    "Category I": ["A"],
    "Category II": ["A2", "D1", "E1"],
    "Category III": ["B + D", "B + F", "B + E", "B + C2", "H"],
    "Category IV": ["B + D", "B + F", "G", "H1"],
}

# ── Polygon Coordinates (log-log space) ───────────────────────────────
POLYGON_COORDINATES = {
    "gaseous_group1-dangerous": {
        "cat_0":   {"x": [0.1, 100000, 100000, 50, 1, 1, 0.1],       "y": [0.1, 0.1, 0.5, 0.5, 25, 200, 200]},
        "cat_i":   {"x": [1, 50, 100, 1],                             "y": [25, 0.5, 0.5, 50]},
        "cat_ii":  {"x": [1, 100, 400, 1],                            "y": [50, 0.5, 0.5, 200]},
        "cat_iii": {"x": [0.1, 1, 400, 2000, 1, 0.1],                "y": [200, 200, 0.5, 0.5, 1000, 1000]},
        "cat_iv":  {"x": [0.1, 1, 2000, 100000, 100000, 0.1],        "y": [1000, 1000, 0.5, 0.5, 10000, 10000]},
    },
    "gaseous_group2-allothers": {
        "cat_0":   {"x": [0.1, 100000, 100000, 100, 1, 1, 0.1],      "y": [0.1, 0.1, 0.5, 0.5, 50, 1000, 1000]},
        "cat_i":   {"x": [1, 100, 400, 1],                            "y": [50, 0.5, 0.5, 200]},
        "cat_ii":  {"x": [1, 400, 2000, 1],                           "y": [200, 0.5, 0.5, 1000]},
        "cat_iii": {"x": [0.1, 1, 2000, 100000, 100000, 1000, 1, 0.1], "y": [1000, 1000, 0.5, 0.5, 4, 4, 3000, 3000]},
        "cat_iv":  {"x": [0.1, 1, 1000, 100000, 100000, 0.1],        "y": [3000, 3000, 4, 4, 10000, 10000]},
    },
    "liquid_low_group1-dangerous": {
        "cat_0":   {"x": [0.1, 100000, 100000, 400, 1, 1, 0.1],      "y": [0.1, 0.1, 0.5, 0.5, 200, 500, 500]},
        "cat_i":   {"x": [20, 400, 100000, 100000],                   "y": [10, 0.5, 0.5, 10]},
        "cat_ii":  {"x": [1, 1, 20, 100000, 100000],                  "y": [500, 200, 10, 10, 500]},
        "cat_iib": {"x": [0.1, 1, 1, 0.1],                           "y": [500, 500, 10000, 10000]},
        "cat_iii": {"x": [1, 100000, 100000, 1],                      "y": [500, 500, 10000, 10000]},
    },
    "liquid_low_group2-allothers": {
        "cat_0":   {"x": [0.1, 0.1, 100000, 100000, 1000, 10],       "y": [1000, 0.1, 0.1, 10, 10, 1000]},
        "cat_i":   {"x": [0.1, 10, 10, 0.1],                         "y": [1000, 1000, 10000, 10000]},
        "cat_ib":  {"x": [20, 1000, 100000, 100000],                  "y": [500, 10, 10, 500]},
        "cat_ii":  {"x": [10, 10, 20, 100000, 100000],                "y": [10000, 1000, 500, 500, 10000]},
    },
}

# ── Helper: point-in-polygon (log-log space) ─────────────────────────
def is_inside(x, y, poly_x, poly_y):
    log_x = math.log10(x)
    log_y = math.log10(y)
    log_poly_points = [(math.log10(px), math.log10(py)) for px, py in zip(poly_x, poly_y)]
    polygon = Path(log_poly_points)
    return polygon.contains_point((log_x, log_y))


# ── Determine category from polygon lookup ───────────────────────────
def determine_category(pressure, volume, equipment_type, medium_state, medium_group):
    key = f"{medium_state}_{medium_group.replace(' ', '').lower()}"
    coordinates = POLYGON_COORDINATES.get(key)
    if not coordinates:
        return "Unknown Category"

    checks = [
        ("cat_0",   "Category 0"),
        ("cat_i",   "Category I"),
        ("cat_ib",  "Category I"),
        ("cat_ii",  "Category II"),
        ("cat_iib", "Category II"),
        ("cat_iii", "Category III"),
        ("cat_iv",  "Category IV"),
    ]
    for poly_key, cat_name in checks:
        if poly_key in coordinates and is_inside(volume, pressure, coordinates[poly_key]["x"], coordinates[poly_key]["y"]):
            return cat_name

    return "Unknown Category"


# ── PED classification ────────────────────────────────────────────────
def classify_ped(equipment_type, medium_state, pressure, volume, diameter, medium_group):
    if pressure <= 0.5:
        return "Not subject to PED"

    category = determine_category(pressure, volume, equipment_type, medium_state, medium_group)

    if equipment_type == "Piping":
        if diameter is None:
            raise ValueError("Diameter DN is required for Piping.")
        if pressure * diameter >= 1000 and medium_group == "Group 1 - dangerous":
            category = "Category IV"
        elif pressure * diameter >= 100:
            category = "Category III"
        elif pressure * diameter >= 50:
            category = "Category II"
        else:
            category = "Category I"

    return category


# ── Conformity procedure ─────────────────────────────────────────────
def conformity_procedure(category):
    modules = CATEGORY_MODULES.get(category, [])
    if category == "Category IV":
        return "B - Design type + F", modules
    elif category == "Category III":
        return "B - Design type + C", modules
    elif category == "Category II":
        return "A - Internal production control", modules
    elif category == "Not subject to PED":
        return "Not applicable", []
    else:
        return "A - Self certification", modules


# ── Diagram generation ───────────────────────────────────────────────
def generate_ped_diagram(pressure, volume, equipment_type, medium_state, medium_group):
    fig, ax = plt.subplots(figsize=(10, 7))

    key = f"{medium_state}_{medium_group.replace(' ', '').lower()}"
    coordinates = POLYGON_COORDINATES.get(key)

    colors = {
        "cat_0":   ('#B0E0E6', 0.4, "Category 0"),
        "cat_i":   ('#90EE90', 0.7, "Category I"),
        "cat_ii":  ('#FFFF99', 0.7, "Category II"),
        "cat_iii": ('#FFDAB9', 0.7, "Category III"),
        "cat_iv":  ('#FFB6C1', 0.7, "Category IV"),
        "cat_ib":  ('#90EE90', 0.7, "Category I"),
        "cat_iib": ('#FFFF99', 0.7, "Category II"),
    }

    if coordinates:
        for poly_key, (color, alpha, label) in colors.items():
            if poly_key in coordinates:
                ax.fill(coordinates[poly_key]["x"], coordinates[poly_key]["y"],
                        color=color, alpha=alpha, label=label)

    ax.plot(volume, pressure, 'bo', markersize=8,
            label=f"Equipment (P={pressure} bar, V={volume} L)")

    ax.set_xlabel("Volume (L)")
    ax.set_ylabel("Pressure (bar)")
    ax.set_title(f"PED Classification: {equipment_type} — {medium_state} ({medium_group})")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(0.1, 100000)
    ax.set_ylim(0.1, 10000)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3)
    plt.tight_layout(rect=[0, 0, 1, 0.95])

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close(fig)
    return img


# ══════════════════════════════════════════════════════════════════════
#  ROUTES
# ══════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/classify', methods=['POST'])
def classify():
    try:
        equipment_type = request.form.get('equipment_type')
        medium_state = request.form.get('medium_state')
        pressure = float(request.form.get('pressure'))
        volume = float(request.form.get('volume'))
        diameter = float(request.form.get('diameter')) if equipment_type == "Piping" and request.form.get('diameter') else None
        medium_group = request.form.get('medium_group')

        category = classify_ped(equipment_type, medium_state, pressure, volume, diameter, medium_group)
        procedure, modules = conformity_procedure(category)

        return render_template('index.html',
                               category=category,
                               procedure=procedure,
                               modules=modules,
                               equipment_type=equipment_type,
                               medium_state=medium_state,
                               medium_group=medium_group,
                               pressure=pressure,
                               volume=volume,
                               diameter=diameter or '',
                               show_diagram=True)
    except Exception as e:
        logging.error(f"Classification error: {e}")
        return render_template('index.html', error=str(e))


@app.route('/diagram')
def diagram():
    try:
        equipment_type = request.args.get('equipment_type')
        medium_state = request.args.get('medium_state')
        pressure = float(request.args.get('pressure'))
        volume = float(request.args.get('volume'))
        medium_group = request.args.get('medium_group')

        img = generate_ped_diagram(pressure, volume, equipment_type, medium_state, medium_group)
        return send_file(img, mimetype='image/png')
    except Exception as e:
        logging.error(f"Diagram error: {e}")
        return "Error generating diagram", 500


# ══════════════════════════════════════════════════════════════════════
#  JSON API (curl / Postman / externe Systeme)
# ══════════════════════════════════════════════════════════════════════

@app.route('/api/pden/classify', methods=['POST'])
def api_classify():
    try:
        data = request.json
        equipment_type = data.get('equipment_type')
        medium_state = data.get('medium_state')
        pressure = float(data.get('pressure'))
        volume = float(data.get('volume'))
        diameter = float(data.get('diameter')) if equipment_type == "Piping" and data.get('diameter') else None
        medium_group = data.get('medium_group')

        category = classify_ped(equipment_type, medium_state, pressure, volume, diameter, medium_group)
        procedure, modules = conformity_procedure(category)

        return jsonify({
            "category": category,
            "procedure": procedure,
            "modules": modules,
            "pressure": pressure,
            "volume": volume
        })
    except Exception as e:
        logging.error(f"API classification error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/pden/diagram', methods=['POST'])
def api_diagram():
    try:
        data = request.json
        equipment_type = data.get('equipment_type')
        medium_state = data.get('medium_state')
        pressure = float(data.get('pressure'))
        volume = float(data.get('volume'))
        medium_group = data.get('medium_group')

        img = generate_ped_diagram(pressure, volume, equipment_type, medium_state, medium_group)
        return send_file(img, mimetype='image/png')
    except Exception as e:
        logging.error(f"API diagram error: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)
