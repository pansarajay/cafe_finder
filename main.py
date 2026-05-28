from flask import Flask, render_template, request, jsonify
import sqlite3
import os

app = Flask(__name__)

# ——— Path to your database ———
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "cafes.db")


# ——— DB helper ———
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ————————————————————————————————————————
#  ROUTES
# ————————————————————————————————————————

# ---------- Home ----------
@app.route("/")
def home():
    return render_template("cafe_finder.html")


# ---------- Get all cafes (JSON) ----------
@app.route("/cafes", methods=["GET"])
def get_cafes():
    location = request.args.get("location")   # optional ?location=Peckham
    search   = request.args.get("search")     # optional ?search=spike

    db    = get_db()
    query = "SELECT * FROM cafe WHERE 1=1"
    args  = []

    if location:
        query += " AND location = ?"
        args.append(location)

    if search:
        query += " AND (name LIKE ? OR location LIKE ?)"
        args += [f"%{search}%", f"%{search}%"]

    rows   = db.execute(query, args).fetchall()
    db.close()

    cafes = [dict(row) for row in rows]
    return jsonify(cafes), 200


# ---------- Add a cafe ----------
@app.route("/add", methods=["POST"])
def add_cafe():
    data = request.get_json()

    name           = data.get("name", "").strip()
    location       = data.get("location", "").strip()
    map_url        = data.get("map_url", "").strip()
    img_url        = data.get("img_url", "").strip()
    seats          = data.get("seats", "").strip()
    coffee_price   = data.get("coffee_price", "").strip()
    has_wifi       = 1 if data.get("has_wifi")       else 0
    has_sockets    = 1 if data.get("has_sockets")    else 0
    has_toilet     = 1 if data.get("has_toilet")     else 0
    can_take_calls = 1 if data.get("can_take_calls") else 0

    if not name or not location:
        return jsonify({"error": "Name and location are required"}), 400

    db = get_db()
    db.execute(
        """INSERT INTO cafe
           (name, location, map_url, img_url, seats, coffee_price,
            has_wifi, has_sockets, has_toilet, can_take_calls)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (name, location, map_url, img_url, seats, coffee_price,
         has_wifi, has_sockets, has_toilet, can_take_calls)
    )
    db.commit()
    new_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.close()

    return jsonify({
        "success": True,
        "id": new_id,
        "message": f"'{name}' added successfully!"
    }), 201


# ---------- Update a cafe ----------
@app.route("/update/<int:cafe_id>", methods=["PATCH"])
def update_cafe(cafe_id):
    data = request.get_json()

    db   = get_db()
    cafe = db.execute("SELECT * FROM cafe WHERE id = ?", (cafe_id,)).fetchone()

    if not cafe:
        db.close()
        return jsonify({"error": "Cafe not found"}), 404

    # Only update fields that were actually sent
    fields = ["name", "location", "map_url", "img_url", "seats",
              "coffee_price", "has_wifi", "has_sockets", "has_toilet", "can_take_calls"]

    updates = []
    values  = []

    for field in fields:
        if field in data:
            updates.append(f"{field} = ?")
            val = data[field]
            # Normalise booleans to 0/1 for boolean columns
            if field in ("has_wifi", "has_sockets", "has_toilet", "can_take_calls"):
                val = 1 if val else 0
            values.append(val)

    if not updates:
        db.close()
        return jsonify({"error": "No fields provided to update"}), 400

    values.append(cafe_id)
    db.execute(f"UPDATE cafe SET {', '.join(updates)} WHERE id = ?", values)
    db.commit()
    db.close()

    return jsonify({"success": True, "message": "Cafe updated"}), 200


# ---------- Delete a cafe ----------
@app.route("/delete/<int:cafe_id>", methods=["DELETE"])
def delete_cafe(cafe_id):
    db   = get_db()
    cafe = db.execute("SELECT * FROM cafe WHERE id = ?", (cafe_id,)).fetchone()

    if not cafe:
        db.close()
        return jsonify({"error": "Cafe not found"}), 404

    db.execute("DELETE FROM cafe WHERE id = ?", (cafe_id,))
    db.commit()
    db.close()

    return jsonify({"success": True, "message": "Cafe deleted"}), 200


# ---------- Get a single cafe ----------
@app.route("/cafe/<int:cafe_id>", methods=["GET"])
def get_cafe(cafe_id):
    db   = get_db()
    cafe = db.execute("SELECT * FROM cafe WHERE id = ?", (cafe_id,)).fetchone()
    db.close()

    if not cafe:
        return jsonify({"error": "Cafe not found"}), 404

    return jsonify(dict(cafe)), 200


# ————————————————————————————————————————
if __name__ == "__main__":
    app.run(debug=True)
