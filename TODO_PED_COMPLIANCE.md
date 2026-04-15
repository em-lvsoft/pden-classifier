# PED Compliance — Offene Punkte

Offene fachliche Punkte zur vollstaendigen Umsetzung der Druckgeraeterichtlinie 2014/68/EU, Anhang II.

---

## 1. Piping-Klassifizierung: Diagramm-basierte Logik fehlt

**Status:** Offen
**Prioritaet:** Hoch
**Betrifft:** `classify_ped()` — Zeilen 96-106

**Problem:**
Die aktuelle Piping-Klassifizierung nutzt nur einfache P x DN Schwellwerte:
- P x DN >= 1000 (Gruppe 1) → Kat IV
- P x DN >= 100 → Kat III
- P x DN >= 50 → Kat II
- Sonst → Kat I

Die DGRL Anhang II definiert fuer Rohrleitungen jedoch eigene grafische Diagramme (Tabellen 6-9) mit logarithmischen Achsen (DN auf X-Achse, PS auf Y-Achse) und Polygon-Grenzen — analog zu den Behaelter-Tabellen.

**Loesung:**
Eigene Polygon-Koordinaten fuer Tabellen 6-9 erfassen und in `POLYGON_COORDINATES` ergaenzen. Die Piping-Logik in `classify_ped()` muss dann `determine_category()` mit DN statt Volume aufrufen.

**Referenz:** DGRL 2014/68/EU, Anhang II, Tabelle 6 (Gas/Gr.1), Tabelle 7 (Gas/Gr.2), Tabelle 8 (Fluessigkeit/Gr.1), Tabelle 9 (Fluessigkeit/Gr.2)

---

## 2. Dampferzeuger: Eigene Klassifizierungstabelle fehlt

**Status:** Offen
**Prioritaet:** Hoch
**Betrifft:** `classify_ped()` und `determine_category()`

**Problem:**
Der Equipment-Typ "Steam/Hot water generators" nutzt aktuell die gleiche Polygon-Logik wie Behaelter (Vessels). Die DGRL sieht fuer Dampferzeuger jedoch eine eigene Tabelle vor (Tabelle 5, Anhang II) mit V (Volumen) auf der X-Achse und PS (Druck) auf der Y-Achse, aber mit anderen Grenzwerten.

**Loesung:**
- Neue Polygon-Koordinaten gemaess Tabelle 5 erfassen
- In `classify_ped()` bei Equipment-Typ "Steam/Hot water generators" separaten Lookup ausfuehren

**Referenz:** DGRL 2014/68/EU, Anhang II, Tabelle 5

---

## 3. Druckzubehoer: Klassifizierung nach hoechstem Risiko fehlt

**Status:** Offen
**Prioritaet:** Mittel
**Betrifft:** `classify_ped()`

**Problem:**
Der Equipment-Typ "Pressure-bearing parts" (Druckzubehoer / Ausruestungsteile mit Druckfunktion) nutzt aktuell die gleiche Logik wie Behaelter. Gemaess Art. 13 Abs. 2 der DGRL werden Ausruestungsteile jedoch nach der hoechsten Kategorie der angeschlossenen Ausruestung klassifiziert, nicht nach eigenen Diagrammen.

**Loesung:**
- Entweder: Hinweis im Frontend anzeigen, dass der Nutzer die Kategorie des angeschlossenen Geraets ermitteln und uebernehmen soll
- Oder: Zusaetzliches Eingabefeld fuer die Kategorie des uebergeordneten Systems

**Referenz:** DGRL 2014/68/EU, Art. 13 Abs. 2

---

## 4. Fluessigkeiten Gruppe 1 (Tabelle 3): Grenzwerte pruefen

**Status:** Offen
**Prioritaet:** Mittel
**Betrifft:** `POLYGON_COORDINATES["liquid_low_group1-dangerous"]`

**Problem:**
Die Polygon-Koordinaten fuer Fluessigkeiten Gruppe 1 (Tabelle 3) muessen gegen die originalen Diagrammgrenzen der DGRL verifiziert werden. Insbesondere:
- Die Schwelle PS = 10 bar fuer den Uebergang Art. 4(3) → Kat I
- Die Schwelle PS x V = 200 fuer Kat I → Kat II
- Ob die Koordinaten fuer `cat_i` (y=[10, 0.5, 0.5, 10]) korrekt den unteren Bereich von Kat I abbilden

**Loesung:**
Polygon-Koordinaten mit dem originalen Diagramm in Anhang II Tabelle 3 abgleichen und ggf. korrigieren.

**Referenz:** DGRL 2014/68/EU, Anhang II, Tabelle 3

---

## 5. Fluessigkeiten Gruppe 2 (Tabelle 4): Grenzwerte pruefen

**Status:** Offen
**Prioritaet:** Mittel
**Betrifft:** `POLYGON_COORDINATES["liquid_low_group2-allothers"]`

**Problem:**
Analog zu Punkt 4 muessen die Polygon-Koordinaten fuer Tabelle 4 verifiziert werden. Die aktuelle `cat_0` Polygon-Form weicht von der typischen Struktur der anderen Tabellen ab.

**Referenz:** DGRL 2014/68/EU, Anhang II, Tabelle 4
