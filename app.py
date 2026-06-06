import sqlite3
import json
from datetime import date, datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

app = Flask(__name__)
app.secret_key = "smartpantry-dev-secret-2024"

DB_PATH = "inventory.db"


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database() -> None:
    """Create the inventory table if it doesn't already exist."""
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS inventory (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name     TEXT    NOT NULL,
                purchase_date TEXT    NOT NULL,
                expiry_date   TEXT    NOT NULL
            )
            """
        )
        conn.commit()


# ---------------------------------------------------------------------------
# Business logic
# ---------------------------------------------------------------------------

def calculate_expiry_status(expiry_date_str: str) -> str:
    """Return 'Expired', 'Expiring Soon', or 'Safe' for a given date string."""
    today = date.today()
    expiry = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()

    if expiry < today:
        return "Expired"
    if expiry <= today + timedelta(days=3):
        return "Expiring Soon"
    return "Safe"


def get_inventory_items() -> list[dict]:
    """Fetch all items and attach a computed status field."""
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
    """
    Return recipe suggestions based on what's currently in the pantry.
    Rules are hardcoded — no external API needed.
    """
    # Normalise to lowercase for matching
    pantry = {name.lower() for name in item_names}

    recipe_rules = [
        {
            "name": "Egg Sandwich",
            "required": {"egg", "bread"},
            "description": "A quick, protein-rich sandwich perfect for any meal of the day.",
        },
        {
            "name": "French Toast",
            "required": {"egg", "milk", "bread"},
            "description": "Classic breakfast made with eggs, milk, and thick-sliced bread.",
        },
        {
            "name": "Fried Rice",
            "required": {"rice", "vegetables"},
            "description": "Simple stir-fried rice with mixed vegetables — a great way to use leftovers.",
        },
        {
            "name": "Tomato Salad",
            "required": {"tomato", "onion"},
            "description": "A fresh, light salad with diced tomatoes and onions.",
        },
        {
            "name": "Omelette",
            "required": {"egg", "milk"},
            "description": "Fluffy eggs whisked with milk for a filling breakfast or snack.",
        },
        {
            "name": "Pasta with Tomato Sauce",
            "required": {"pasta", "tomato"},
            "description": "A pantry staple — pasta tossed in a simple tomato-based sauce.",
        },
        {
            "name": "Vegetable Soup",
            "required": {"vegetables", "onion"},
            "description": "Hearty soup made from whatever vegetables you have on hand.",
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
    """Aggregate counts for the dashboard statistics cards."""
    total = len(items)
    expired = sum(1 for i in items if i["status"] == "Expired")
    expiring_soon = sum(1 for i in items if i["status"] == "Expiring Soon")
    safe = total - expired - expiring_soon
    return {"total": total, "expired": expired, "expiring_soon": expiring_soon, "safe": safe}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    items = get_inventory_items()
    stats = get_statistics(items)
    return render_template("home.html", items=items, stats=stats)


@app.route("/add-item", methods=["GET", "POST"])
def add_item():
    if request.method == "POST":
        item_name = request.form.get("item_name", "").strip()
        purchase_date = request.form.get("purchase_date", "").strip()
        expiry_date = request.form.get("expiry_date", "").strip()

        # Validation
        if not item_name or not purchase_date or not expiry_date:
            flash("All fields are required. Please fill in every field.", "danger")
            return render_template("add_item.html")

        try:
            p_date = datetime.strptime(purchase_date, "%Y-%m-%d").date()
            e_date = datetime.strptime(expiry_date, "%Y-%m-%d").date()
        except ValueError:
            flash("Invalid date format. Please use the date picker.", "danger")
            return render_template("add_item.html")

        if e_date < p_date:
            flash("Expiry date cannot be earlier than the purchase date.", "danger")
            return render_template("add_item.html")

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

        flash(f"'{item_name}' was added to your pantry successfully.", "success")
        return redirect(url_for("home"))

    return render_template("add_item.html")


@app.route("/delete/<int:item_id>", methods=["POST"])
def delete_item(item_id: int):
    try:
        with get_db_connection() as conn:
            row = conn.execute("SELECT item_name FROM inventory WHERE id = ?", (item_id,)).fetchone()
            if row is None:
                flash("Item not found.", "warning")
                return redirect(url_for("home"))
            conn.execute("DELETE FROM inventory WHERE id = ?", (item_id,))
            conn.commit()
        flash(f"'{row['item_name']}' has been removed from your pantry.", "success")
    except sqlite3.Error as exc:
        flash(f"Could not delete item: {exc}", "danger")

    return redirect(url_for("home"))


@app.route("/recipes")
def recipes():
    items = get_inventory_items()
    # Only consider items that are not yet expired
    available_names = [i["item_name"] for i in items if i["status"] != "Expired"]
    suggestions = suggest_recipes(available_names)
    return render_template("recipes.html", suggestions=suggestions, available=available_names)


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

@app.route("/api/inventory")
def api_inventory():
    """Return the full inventory as a JSON array."""
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
    app.run(debug=True)
