import sqlite3
# Used for database operations (SQLite)

import json
# Used for JSON handling (API responses if needed)

from datetime import date, datetime, timedelta
# Used for date calculations and expiry logic

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
# Flask framework imports for routing, templates, forms, and API responses


app = Flask(__name__)
# Initialize Flask application

app.secret_key = "smartpantry-dev-secret-2024"
# Secret key used for session management and flash messages

DB_PATH = "inventory.db"
# Database file path


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db_connection() -> sqlite3.Connection:
    # Creates and returns a database connection
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database() -> None:
    # Creates inventory table if it does not exist
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                purchase_date TEXT NOT NULL,
                expiry_date TEXT NOT NULL
            )
            """
        )
        conn.commit()


# ---------------------------------------------------------------------------
# Business logic
# ---------------------------------------------------------------------------

def calculate_expiry_status(expiry_date_str: str) -> str:
    # Determines whether an item is Safe, Expiring Soon, or Expired
    today = date.today()
    expiry = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()

    if expiry < today:
        return "Expired"
    if expiry <= today + timedelta(days=3):
        return "Expiring Soon"
    return "Safe"


def get_inventory_items() -> list[dict]:
    # Fetches all items and adds expiry status
    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT id, item_name, purchase_date, expiry_date FROM inventory ORDER BY expiry_date ASC"
        ).fetchall()

    items = []
    for row in rows:
        item = dict(row)
        item["status"] = calculate_expiry_status(item["expiry_date"])
        items.append(item)

    return items


def suggest_recipes(item_names: list[str]) -> list[dict]:
    # Suggests recipes based on available pantry items

    pantry = {name.lower() for name in item_names}
    # Normalize ingredient names for matching

    recipe_rules = [
        # Predefined recipe combinations
        {
            "name": "Egg Sandwich",
            "required": {"egg", "bread"},
            "description": "A quick protein-rich sandwich.",
        },
        {
            "name": "French Toast",
            "required": {"egg", "milk", "bread"},
            "description": "Classic breakfast recipe.",
        },
        {
            "name": "Fried Rice",
            "required": {"rice", "vegetables"},
            "description": "Simple leftover rice dish.",
        },
        {
            "name": "Tomato Salad",
            "required": {"tomato", "onion"},
            "description": "Fresh vegetable salad.",
        },
        {
            "name": "Omelette",
            "required": {"egg", "milk"},
            "description": "Soft and fluffy eggs.",
        },
        {
            "name": "Pasta with Tomato Sauce",
            "required": {"pasta", "tomato"},
            "description": "Simple pasta recipe.",
        },
        {
            "name": "Vegetable Soup",
            "required": {"vegetables", "onion"},
            "description": "Healthy homemade soup.",
        },
    ]

    matched = []
    for recipe in recipe_rules:
        if recipe["required"].issubset(pantry):
            matched.append({
                "name": recipe["name"],
                "description": recipe["description"],
                "ingredients": sorted(recipe["required"]),
            })

    return matched


def get_statistics(items: list[dict]) -> dict:
    # Calculates dashboard summary statistics
    total = len(items)
    expired = sum(1 for i in items if i["status"] == "Expired")
    expiring_soon = sum(1 for i in items if i["status"] == "Expiring Soon")
    safe = total - expired - expiring_soon

    return {
        "total": total,
        "expired": expired,
        "expiring_soon": expiring_soon,
        "safe": safe
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    # Homepage showing inventory and stats
    items = get_inventory_items()
    stats = get_statistics(items)
    return render_template("home.html", items=items, stats=stats)


@app.route("/add-item", methods=["GET", "POST"])
def add_item():
    # Handles adding new pantry items
    if request.method == "POST":

        item_name = request.form.get("item_name", "").strip()
        purchase_date = request.form.get("purchase_date", "").strip()
        expiry_date = request.form.get("expiry_date", "").strip()

        # Validate input fields
        if not item_name or not purchase_date or not expiry_date:
            flash("All fields are required.", "danger")
            return render_template("add_item.html")

        try:
            p_date = datetime.strptime(purchase_date, "%Y-%m-%d").date()
            e_date = datetime.strptime(expiry_date, "%Y-%m-%d").date()
        except ValueError:
            flash("Invalid date format.", "danger")
            return render_template("add_item.html")

        # Ensure expiry is after purchase
        if e_date < p_date:
            flash("Expiry date cannot be earlier than purchase date.", "danger")
            return render_template("add_item.html")

        # Insert into database
        try:
            with get_db_connection() as conn:
                conn.execute(
                    "INSERT INTO inventory (item_name, purchase_date, expiry_date) VALUES (?, ?, ?)",
                    (item_name, purchase_date, expiry_date),
                )
                conn.commit()
        except sqlite3.Error as exc:
            flash(f"Database error: {exc}", "danger")
            return render_template("add_item.html")

        flash(f"'{item_name}' added successfully.", "success")
        return redirect(url_for("home"))

    return render_template("add_item.html")


@app.route("/delete/<int:item_id>", methods=["POST"])
def delete_item(item_id: int):
    # Deletes an item from inventory
    try:
        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT item_name FROM inventory WHERE id = ?",
                (item_id,)
            ).fetchone()

            if row is None:
                flash("Item not found.", "warning")
                return redirect(url_for("home"))

            conn.execute("DELETE FROM inventory WHERE id = ?", (item_id,))
            conn.commit()

        flash(f"'{row['item_name']}' deleted successfully.", "success")

    except sqlite3.Error as exc:
        flash(f"Delete failed: {exc}", "danger")

    return redirect(url_for("home"))


@app.route("/recipes")
def recipes():
    # Displays recipe suggestions based on pantry items
    items = get_inventory_items()

    available_names = [i["item_name"] for i in items if i["status"] != "Expired"]
    suggestions = suggest_recipes(available_names)

    return render_template(
        "recipes.html",
        suggestions=suggestions,
        available=available_names
    )


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

@app.route("/api/inventory")
def api_inventory():
    # Returns inventory data as JSON (API endpoint)
    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT id, item_name, expiry_date FROM inventory ORDER BY expiry_date ASC"
        ).fetchall()

    return jsonify([dict(row) for row in rows])


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    initialize_database()
    import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port)