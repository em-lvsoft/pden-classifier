import unittest

from ped_engine import ClassificationInput, classify_ped


class PedEngineTests(unittest.TestCase):
    def test_not_subject_below_half_bar(self):
        result = classify_ped(
            ClassificationInput(
                equipment_type="Vessel",
                medium_state="gaseous",
                pressure=0.5,
                volume=100,
                medium_group="Group 1 - dangerous",
            )
        )
        self.assertEqual(result.category, "Not subject to PED")

    def test_vessel_uses_table_1(self):
        result = classify_ped(
            ClassificationInput(
                equipment_type="Vessel",
                medium_state="gaseous",
                pressure=2,
                volume=20,
                medium_group="Group 1 - dangerous",
            )
        )
        self.assertEqual(result.table, "table_1")
        self.assertEqual(result.category, "Category I")

    def test_unstable_gas_uplifts_table_1(self):
        result = classify_ped(
            ClassificationInput(
                equipment_type="Vessel",
                medium_state="gaseous",
                pressure=2,
                volume=20,
                medium_group="Group 1 - dangerous",
                unstable_gas=True,
            )
        )
        self.assertEqual(result.category, "Category III")

    def test_portable_equipment_uplifts_table_2(self):
        result = classify_ped(
            ClassificationInput(
                equipment_type="Vessel",
                medium_state="gaseous",
                pressure=10,
                volume=50,
                medium_group="Group 2 - all others",
                portable_extinguisher_or_breathing_apparatus=True,
            )
        )
        self.assertEqual(result.category, "Category III")

    def test_piping_requires_dn(self):
        with self.assertRaises(ValueError):
            classify_ped(
                ClassificationInput(
                    equipment_type="Piping",
                    medium_state="gaseous",
                    pressure=20,
                    medium_group="Group 1 - dangerous",
                )
            )

    def test_table_7_high_temperature_uplift(self):
        cool = classify_ped(
            ClassificationInput(
                equipment_type="Piping",
                medium_state="gaseous",
                pressure=2,
                diameter=60,
                medium_group="Group 2 - all others",
                fluid_temperature_c=200,
            )
        )
        hot = classify_ped(
            ClassificationInput(
                equipment_type="Piping",
                medium_state="gaseous",
                pressure=2,
                diameter=60,
                medium_group="Group 2 - all others",
                fluid_temperature_c=400,
            )
        )
        self.assertEqual(cool.category, "Category II")
        self.assertEqual(hot.category, "Category III")

    def test_pressure_accessory_takes_higher_of_v_and_dn_paths(self):
        result = classify_ped(
            ClassificationInput(
                equipment_type="Pressure accessories",
                medium_state="gaseous",
                pressure=20,
                volume=100,
                diameter=100,
                medium_group="Group 1 - dangerous",
            )
        )
        self.assertEqual(result.category, "Category IV")
        self.assertTrue(any("higher category" in note.lower() for note in result.notes))

    def test_legacy_alias_is_supported(self):
        result = classify_ped(
            ClassificationInput(
                equipment_type="Pressure-bearing parts",
                medium_state="liquid_low",
                pressure=15,
                volume=100,
                diameter=40,
                medium_group="Group 2 - all others",
            )
        )
        self.assertIn(result.table, {"table_4", "table_9"})

    def test_pressure_cooker_is_at_least_category_iii(self):
        result = classify_ped(
            ClassificationInput(
                equipment_type="Steam/Hot water generators",
                medium_state="gaseous",
                pressure=5,
                volume=5,
                medium_group="Group 2 - all others",
                pressure_cooker=True,
            )
        )
        self.assertEqual(result.category, "Category III")


if __name__ == "__main__":
    unittest.main()
