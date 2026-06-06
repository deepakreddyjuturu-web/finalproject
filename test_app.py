"""
tests/test_app.py

Unit and integration tests for SmartPantry.
Run with:  python -m pytest tests/ -v
       or: python -m unittest discover tests/
"""

import json
import sys
import os
import unittest

# Make sure the project root is on the path regardless of where tests run from.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app, initialize_database, calculate_expiry_status, suggest_recipes, get_statistics


class TestExpiryLogic(unittest.TestCase):
    """Unit tests for the expiry-status helper."""

    def test_expired_item(self):
        self.assertEqual(calculate_expiry_status("2020-01-01"), "Expired")

    def test_safe_item(self):
        self.assertEqual(calculate_expiry_status("2099-12-31"), "Safe")

    def test_expiring_soon_boundary(self):
        from datetime import date, timedelta
        three_days = (date.today() + timedelta(days=3)).strftime("%Y-%m-%d")
        self.assertEqual(calculate_expiry_status(three_days), "Expiring Soon")

    def test_expiring_today(self):
        from datetime import date
        today = date.today().strftime("%Y-%m-%d")
        self.assertEqual(calculate_expiry_status(today), "Expiring Soon")


class TestRecipeSuggestions(unittest.TestCase):
    """Unit tests for the recipe suggestion engine."""

    def test_egg_sandwich(self):
        recipes = suggest_recipes(["Egg", "Bread"])
        names = [r["name"] for r in recipes]
        self.assertIn("Egg Sandwich", names)

    def test_french_toast_requires_all_three(self):
        # Missing milk — French Toast should NOT appear.
        recipes = suggest_recipes(["Egg", "Bread"])
        names = [r["name"] for r in recipes]
        self.assertNotIn("French Toast", names)

    def test_french_toast_with_all_ingredients(self):
        recipes = suggest_recipes(["Egg", "Bread", "Milk"])
        names = [r["name"] for r in recipes]
        self.assertIn("French Toast", names)

    def test_empty_pantry_returns_no_recipes(self):
        self.assertEqual(suggest_recipes([]), [])

    def test_case_insensitive_matching(self):
        recipes = suggest_recipes(["EGG", "BREAD"])
        names = [r["name"] for r in recipes]
        self.assertIn("Egg Sandwich", names)


class TestStatistics(unittest.TestCase):
    """Unit tests for the statistics aggregation helper."""

    def test_empty_inventory(self):
        stats = get_statistics([])
        self.assertEqual(stats["total"], 0)
        self.assertEqual(stats["expired"], 0)

    def test_counts_are_correct(self):
        items = [
            {"status": "Safe"},
            {"status": "Safe"},
            {"status": "Expiring Soon"},
            {"status": "Expired"},
        ]
        stats = get_statistics(items)
        self.assertEqual(stats["total"], 4)
        self.assertEqual(stats["safe"], 2)
        self.assertEqual(stats["expiring_soon"], 1)
        self.assertEqual(stats["expired"], 1)


class TestRoutes(unittest.TestCase):
    """Integration tests for Flask routes using the test client."""

    def setUp(self):
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        self.client = app.test_client()
        initialize_database()

    # -- Home page --

    def test_home_returns_200(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_home_contains_pantry_heading(self):
        response = self.client.get("/")
        self.assertIn(b"Pantry", response.data)

    # -- Add item (GET) --

    def test_add_item_page_returns_200(self):
        response = self.client.get("/add-item")
        self.assertEqual(response.status_code, 200)

    # -- Add item (POST) valid --

    def test_add_item_valid_redirects_home(self):
        response = self.client.post("/add-item", data={
            "item_name": "Tomato",
            "purchase_date": "2026-06-01",
            "expiry_date": "2026-06-20",
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn("/", response.headers["Location"])

    # -- Add item (POST) invalid — expiry before purchase --

    def test_add_item_invalid_dates_stays_on_form(self):
        response = self.client.post("/add-item", data={
            "item_name": "Cheese",
            "purchase_date": "2026-06-15",
            "expiry_date": "2026-06-01",
        })
        self.assertEqual(response.status_code, 200)

    # -- Add item (POST) invalid — missing fields --

    def test_add_item_missing_fields_stays_on_form(self):
        response = self.client.post("/add-item", data={
            "item_name": "",
            "purchase_date": "",
            "expiry_date": "",
        })
        self.assertEqual(response.status_code, 200)

    # -- Recipes page --

    def test_recipes_page_returns_200(self):
        response = self.client.get("/recipes")
        self.assertEqual(response.status_code, 200)

    # -- API endpoint --

    def test_api_inventory_returns_200(self):
        response = self.client.get("/api/inventory")
        self.assertEqual(response.status_code, 200)

    def test_api_inventory_returns_json_list(self):
        response = self.client.get("/api/inventory")
        data = json.loads(response.data)
        self.assertIsInstance(data, list)

    def test_api_inventory_json_has_expected_keys(self):
        # Add one item first so the list is non-empty.
        self.client.post("/add-item", data={
            "item_name": "Rice",
            "purchase_date": "2026-06-01",
            "expiry_date": "2026-12-01",
        })
        response = self.client.get("/api/inventory")
        data = json.loads(response.data)
        if data:
            self.assertIn("id", data[0])
            self.assertIn("item_name", data[0])
            self.assertIn("expiry_date", data[0])

    # -- Delete route --

    def test_delete_nonexistent_item_redirects(self):
        response = self.client.post("/delete/999999")
        self.assertEqual(response.status_code, 302)


if __name__ == "__main__":
    unittest.main()
