# SmartPantry — Ingredient & Expiry Manager

SmartPantry is a lightweight web application that helps households and small kitchens reduce food waste. Users can log pantry ingredients, track expiry dates, get visual alerts for items that are expiring soon or have already expired, and receive simple recipe suggestions based on what's currently available.

Built with **Flask** and **SQLite** as a university-level project demonstrating full-stack web development without external ORMs or frontend frameworks.

---

## Features

- **Pantry Dashboard** — view all ingredients in a colour-coded table (green / yellow / red).
- **Statistics Cards** — at-a-glance count of total, safe, expiring-soon, and expired items.
- **Add Ingredients** — form with client-side and server-side validation.
- **Delete Items** — remove ingredients with a single click.
- **Recipe Suggestions** — rule-based engine matches current pantry stock to a set of recipes.
- **REST API** — `GET /api/inventory` returns live inventory data as JSON.
- **Flash Messages** — success and error feedback on every user action.
- **Empty States** — descriptive placeholders when no data exists.

---

## Folder Structure

```
smartpantry/
│
├── app.py               # Flask application — routes, helpers, business logic
├── inventory.db         # SQLite database (auto-created on first run)
├── requirements.txt     # Python dependencies
├── README.md
├── .gitignore
│
├── static/
│     ├── style.css      # Custom styles built on top of Bootstrap 5
│     └── script.js      # Client-side form validation and UX helpers
│
└── templates/
      ├── base.html      # Shared layout — navbar, flash messages, footer
      ├── home.html      # Pantry overview
      ├── add_item.html  # Add ingredient form
      └── recipes.html   # Recipe suggestions
```

---

## Technologies

| Layer      | Technology                  |
|------------|-----------------------------|
| Backend    | Python 3.11+, Flask 3.x     |
| Database   | SQLite (built-in `sqlite3`) |
| Frontend   | Jinja2, Bootstrap 5, vanilla JS |
| Icons      | Bootstrap Icons             |

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/smartpantry.git
cd smartpantry
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Running the Application

```bash
python app.py
```

Open your browser and navigate to **http://127.0.0.1:5000**.

The SQLite database (`inventory.db`) is created automatically on first launch.

---

## API Documentation

### `GET /api/inventory`

Returns the full pantry inventory as a JSON array.

**Example response:**

```json
[
  {
    "id": 1,
    "item_name": "Milk",
    "expiry_date": "2024-06-10"
  },
  {
    "id": 2,
    "item_name": "Eggs",
    "expiry_date": "2024-06-15"
  }
]
```

No authentication is required. Items are ordered by expiry date ascending.

---

## Expiry Status Logic

| Status         | Condition                           | Colour |
|----------------|-------------------------------------|--------|
| Safe           | Expiry date is more than 3 days away | Green  |
| Expiring Soon  | Expiry date is within 3 days        | Yellow |
| Expired        | Expiry date has passed              | Red    |

---

## Recipe Rules

Recipes are suggested when all required ingredients are present in the pantry and not expired.

| Recipe              | Required Ingredients          |
|---------------------|-------------------------------|
| Egg Sandwich        | Egg, Bread                    |
| French Toast        | Egg, Milk, Bread              |
| Fried Rice          | Rice, Vegetables              |
| Tomato Salad        | Tomato, Onion                 |
| Omelette            | Egg, Milk                     |
| Pasta Tomato Sauce  | Pasta, Tomato                 |
| Vegetable Soup      | Vegetables, Onion             |

---

## Suggested Git Commit History

```bash
git commit -m "Initialize Flask project structure"
git commit -m "Add SQLite inventory database"
git commit -m "Implement add item feature with validation"
git commit -m "Add expiry status logic and colour-coded table"
git commit -m "Add recipe suggestion engine"
git commit -m "Implement /api/inventory JSON endpoint"
git commit -m "Add statistics cards and empty states"
git commit -m "Improve styling and responsive layout"
git commit -m "Add client-side form validation"
git commit -m "Final cleanup and README"
```

---

## Deployment (Render)

1. Push the repository to GitHub.
2. Create a new **Web Service** on [Render](https://render.com).
3. Set the build command: `pip install -r requirements.txt`
4. Set the start command: `python app.py`
5. Render will detect the Flask app and deploy automatically.

---

## Authors

- Bhavadeeshwar — backend routes, database design, API endpoint  
- Deepak — templates, CSS styling, recipe logic




































































