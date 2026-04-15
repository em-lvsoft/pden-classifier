# PED Classification Tool

Classification of pressure equipment according to **Pressure Equipment Directive 2014/68/EU**.

Determines the PED category (0 – IV), the applicable conformity assessment procedure, and the available modules based on equipment parameters. Includes a visual classification diagram.

---

## Quick Start

```bash
git clone https://github.com/em-lvsoft/pden-classifier.git
cd pden-classifier
pip install -r requirements.txt
python app.py
```

The application starts on **http://localhost:5000**.

- **Web UI:** Open http://localhost:5000 in a browser.
- **REST API:** Use the endpoints documented below.

---

## REST API Documentation

Base URL: `http://<host>:5000`

### 1. Classify Equipment

Determines the PED category, conformity procedure, and available modules.

**Endpoint:** `POST /api/pden/classify`

**Content-Type:** `application/json`

#### Request Body

| Field            | Type   | Required | Description                                                             |
|------------------|--------|----------|-------------------------------------------------------------------------|
| `equipment_type` | string | Yes      | One of: `Vessel`, `Piping`, `Pressure-bearing parts`, `Steam/Hot water generators` |
| `medium_state`   | string | Yes      | One of: `gaseous`, `liquid_low`                                         |
| `pressure`       | number | Yes      | Maximum allowable pressure PS in **bar**                                |
| `volume`         | number | Yes      | Volume in **liters**                                                    |
| `diameter`       | number | Piping only | Nominal diameter DN (required when `equipment_type` is `Piping`)     |
| `medium_group`   | string | Yes      | One of: `Group 1 - dangerous`, `Group 2 - all others`                   |

#### Example Request

```bash
curl -X POST http://localhost:5000/api/pden/classify \
  -H "Content-Type: application/json" \
  -d '{
    "equipment_type": "Vessel",
    "medium_state": "gaseous",
    "pressure": 10,
    "volume": 100,
    "medium_group": "Group 1 - dangerous"
  }'
```

#### Example Response

```json
{
  "category": "Category II",
  "procedure": "A - Internal production control",
  "modules": ["A2", "D1", "E1"],
  "pressure": 10.0,
  "volume": 100.0
}
```

#### Response Fields

| Field       | Type     | Description                                           |
|-------------|----------|-------------------------------------------------------|
| `category`  | string   | PED category: `Category 0` through `Category IV`, `Not subject to PED`, or `Unknown Category` |
| `procedure` | string   | Applicable conformity assessment procedure            |
| `modules`   | string[] | List of available conformity modules                  |
| `pressure`  | number   | Echo of input pressure (bar)                          |
| `volume`    | number   | Echo of input volume (L)                              |

---

### 2. Generate Classification Diagram

Returns a PNG image showing the classification boundaries with the equipment point plotted.

**Endpoint:** `POST /api/pden/diagram`

**Content-Type:** `application/json`

**Response Content-Type:** `image/png`

#### Request Body

| Field            | Type   | Required | Description                                                             |
|------------------|--------|----------|-------------------------------------------------------------------------|
| `equipment_type` | string | Yes      | One of: `Vessel`, `Piping`, `Pressure-bearing parts`, `Steam/Hot water generators` |
| `medium_state`   | string | Yes      | One of: `gaseous`, `liquid_low`                                         |
| `pressure`       | number | Yes      | Maximum allowable pressure PS in **bar**                                |
| `volume`         | number | Yes      | Volume in **liters**                                                    |
| `medium_group`   | string | Yes      | One of: `Group 1 - dangerous`, `Group 2 - all others`                   |

#### Example Request

```bash
curl -X POST http://localhost:5000/api/pden/diagram \
  -H "Content-Type: application/json" \
  -d '{
    "equipment_type": "Vessel",
    "medium_state": "gaseous",
    "pressure": 10,
    "volume": 100,
    "medium_group": "Group 1 - dangerous"
  }' \
  --output diagram.png
```

#### Response

Binary PNG image (log-log diagram with color-coded category regions).

---

### 3. Piping Example (with Diameter)

```bash
curl -X POST http://localhost:5000/api/pden/classify \
  -H "Content-Type: application/json" \
  -d '{
    "equipment_type": "Piping",
    "medium_state": "gaseous",
    "pressure": 20,
    "volume": 50,
    "diameter": 100,
    "medium_group": "Group 1 - dangerous"
  }'
```

For piping, the classification uses `P x DN` instead of polygon lookup:

| P x DN       | Medium Group            | Category     |
|--------------|-------------------------|--------------|
| >= 1000      | Group 1 - dangerous     | Category IV  |
| >= 100       | any                     | Category III |
| >= 50        | any                     | Category II  |
| < 50         | any                     | Category I   |

---

## Error Handling

All API errors return JSON with HTTP status 500:

```json
{
  "error": "Description of the error"
}
```

Common error cases:
- Missing required fields
- `diameter` not provided for `Piping` equipment type
- `pressure` <= 0.5 bar results in `"Not subject to PED"` (not an error)

---

## Allowed Values Reference

### equipment_type
| Value                        | Description                     |
|------------------------------|---------------------------------|
| `Vessel`                     | Pressure vessels                |
| `Piping`                     | Piping systems (requires DN)   |
| `Pressure-bearing parts`     | Pressure-bearing accessories    |
| `Steam/Hot water generators` | Steam boilers, hot water gen.   |

### medium_state
| Value        | Description                                   |
|--------------|-----------------------------------------------|
| `gaseous`    | Gaseous or liquid with vapor pressure > 0.5 bar above normal atmospheric pressure |
| `liquid_low` | Liquid with vapor pressure <= 0.5 bar above normal atmospheric pressure           |

### medium_group
| Value                    | Description                                      |
|--------------------------|--------------------------------------------------|
| `Group 1 - dangerous`    | Dangerous fluids (explosive, flammable, toxic, oxidising) acc. Art. 13 |
| `Group 2 - all others`   | All other fluids                                 |

### Possible Categories
| Category              | Conformity Procedure                | Modules                                                    |
|-----------------------|-------------------------------------|------------------------------------------------------------|
| `Not subject to PED`  | Not applicable                      | —                                                          |
| `Category 0`          | A - Self certification              | acc. Art. 4 para. (3) good engineering practice            |
| `Category I`          | A - Self certification              | A                                                          |
| `Category II`         | A - Internal production control     | A2, D1, E1                                                 |
| `Category III`        | B - Design type + C                 | B + D, B + F, B + E, B + C2, H                             |
| `Category IV`         | B - Design type + F                 | B + D, B + F, G, H1                                        |

---

## Integration Examples

### Python

```python
import requests

response = requests.post("http://localhost:5000/api/pden/classify", json={
    "equipment_type": "Vessel",
    "medium_state": "gaseous",
    "pressure": 10,
    "volume": 100,
    "medium_group": "Group 1 - dangerous"
})

result = response.json()
print(f"Category: {result['category']}")
print(f"Procedure: {result['procedure']}")
print(f"Modules: {', '.join(result['modules'])}")
```

### JavaScript / Node.js

```javascript
const response = await fetch("http://localhost:5000/api/pden/classify", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    equipment_type: "Vessel",
    medium_state: "gaseous",
    pressure: 10,
    volume: 100,
    medium_group: "Group 1 - dangerous"
  })
});

const result = await response.json();
console.log(`Category: ${result.category}`);
```

### C# / .NET

```csharp
using var client = new HttpClient();
var payload = new {
    equipment_type = "Vessel",
    medium_state = "gaseous",
    pressure = 10,
    volume = 100,
    medium_group = "Group 1 - dangerous"
};

var response = await client.PostAsJsonAsync(
    "http://localhost:5000/api/pden/classify", payload);
var result = await response.Content.ReadFromJsonAsync<JsonElement>();
Console.WriteLine($"Category: {result.GetProperty("category")}");
```

### PowerShell

```powershell
$body = @{
    equipment_type = "Vessel"
    medium_state   = "gaseous"
    pressure       = 10
    volume         = 100
    medium_group   = "Group 1 - dangerous"
} | ConvertTo-Json

$result = Invoke-RestMethod -Uri "http://localhost:5000/api/pden/classify" `
    -Method POST -Body $body -ContentType "application/json"

Write-Host "Category: $($result.category)"
```
