from flask import Flask, jsonify, render_template, request, send_file
import logging
import matplotlib

from ped_engine import ClassificationInput, classify_ped, generate_ped_diagram

matplotlib.use("Agg")

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def parse_bool(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def parse_optional_float(value):
    if value in (None, ""):
        return None
    return float(value)


def build_input(payload, source):
    equipment_type = payload.get("equipment_type")
    medium_state = payload.get("medium_state")
    pressure = float(payload.get("pressure"))
    medium_group = payload.get("medium_group")

    data = ClassificationInput(
        equipment_type=equipment_type,
        medium_state=medium_state,
        pressure=pressure,
        medium_group=medium_group,
        volume=parse_optional_float(payload.get("volume")),
        diameter=parse_optional_float(payload.get("diameter")),
        unstable_gas=parse_bool(payload.get("unstable_gas")),
        portable_extinguisher_or_breathing_apparatus=parse_bool(payload.get("portable_extinguisher_or_breathing_apparatus")),
        fluid_temperature_c=parse_optional_float(payload.get("fluid_temperature_c")),
        pressure_cooker=parse_bool(payload.get("pressure_cooker")),
        warm_water_assembly=parse_bool(payload.get("warm_water_assembly")),
    )

    logging.info("Built classification input from %s: %s", source, data)
    return data


def render_result(template_data, result, data):
    return render_template(
        "index.html",
        category=result.category,
        procedure=result.procedure,
        modules=result.modules,
        table=result.table,
        basis=result.basis,
        scope=result.scope,
        notes=result.notes,
        equipment_type=data.equipment_type,
        medium_state=data.medium_state,
        medium_group=data.medium_group,
        pressure=data.pressure,
        volume=data.volume if data.volume is not None else "",
        diameter=data.diameter if data.diameter is not None else "",
        unstable_gas=data.unstable_gas,
        portable_extinguisher_or_breathing_apparatus=data.portable_extinguisher_or_breathing_apparatus,
        fluid_temperature_c=data.fluid_temperature_c if data.fluid_temperature_c is not None else "",
        pressure_cooker=data.pressure_cooker,
        warm_water_assembly=data.warm_water_assembly,
        show_diagram=True,
        **template_data,
    )


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/classify", methods=["POST"])
def classify():
    try:
        data = build_input(request.form, "form")
        result = classify_ped(data)
        return render_result({}, result, data)
    except Exception as exc:
        logging.error("Classification error: %s", exc)
        return render_template("index.html", error=str(exc))


@app.route("/diagram")
def diagram():
    try:
        data = build_input(request.args, "query")
        img = generate_ped_diagram(data)
        return send_file(img, mimetype="image/png")
    except Exception as exc:
        logging.error("Diagram error: %s", exc)
        return "Error generating diagram", 500


@app.route("/api/pden/classify", methods=["POST"])
def api_classify():
    try:
        data = build_input(request.json or {}, "json")
        result = classify_ped(data)
        response = result.as_dict()
        response.update(
            {
                "equipment_type": data.equipment_type,
                "medium_state": data.medium_state,
                "medium_group": data.medium_group,
                "pressure": data.pressure,
                "volume": data.volume,
                "diameter": data.diameter,
                "unstable_gas": data.unstable_gas,
                "portable_extinguisher_or_breathing_apparatus": data.portable_extinguisher_or_breathing_apparatus,
                "fluid_temperature_c": data.fluid_temperature_c,
                "pressure_cooker": data.pressure_cooker,
                "warm_water_assembly": data.warm_water_assembly,
            }
        )
        return jsonify(response)
    except Exception as exc:
        logging.error("API classification error: %s", exc)
        return jsonify({"error": str(exc)}), 500


@app.route("/api/pden/diagram", methods=["POST"])
def api_diagram():
    try:
        data = build_input(request.json or {}, "json")
        img = generate_ped_diagram(data)
        return send_file(img, mimetype="image/png")
    except Exception as exc:
        logging.error("API diagram error: %s", exc)
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5050)
