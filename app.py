from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for
from flask_cors import CORS
import sqlite3
import psycopg
from psycopg.rows import dict_row
import requests

MODEL = "qwen2.5:3b"
OLLAMA_URL = "http://localhost:11434/api/chat"
import os
import time
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "backend", "assistant.db")

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:3b"

app = Flask(__name__, static_folder=".")
app.secret_key = os.environ.get("ADMIN_SECRET_KEY")

ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

if not ADMIN_PASSWORD:
    raise RuntimeError("ADMIN_PASSWORD environment variable belum diset")


def validate_product_input(data):
    if not isinstance(data, dict):
        return "Data produk tidak valid"

    nama = str(data.get("nama", "")).strip()
    harga = data.get("harga")
    link = str(data.get("link", "")).strip()

    if not nama:
        return "Nama produk wajib diisi"

    if len(nama) > 200:
        return "Nama produk maksimal 200 karakter"

    if harga is None or str(harga).strip() == "":
        return "Harga wajib diisi"

    try:
        harga_value = float(harga)
        if harga_value < 0:
            return "Harga tidak boleh negatif"
    except (TypeError, ValueError):
        return "Harga harus berupa angka"

    if not link:
        return "Link produk wajib diisi"

    if not (link.startswith("http://") or link.startswith("https://")):
        return "Link harus diawali http:// atau https://"

    for key, limit in {
        "marketplace": 100,
        "kategori": 100,
        "subkategori": 100,
        "deskripsi": 1000
    }.items():
        value = str(data.get(key, "") or "").strip()
        if len(value) > limit:
            return f"{key.capitalize()} maksimal {limit} karakter"

    return None


# ============================================================
# ADMIN_LOGIN_V3
# ============================================================

@app.before_request
def protect_admin_area():
    path = request.path

    allowed = {
        "/admin/login",
        "/admin/logout"
    }

    # Lindungi API admin
    if path.startswith("/api/admin/"):
        if not session.get("admin_logged_in"):
            return jsonify({"error": "Unauthorized"}), 401
        return None

    # Lindungi halaman admin
    if path.startswith("/admin") and path not in allowed:
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))


ADMIN_RATE_LIMIT = 60
ADMIN_RATE_WINDOW = 60
_admin_request_log = {}

@app.before_request
def admin_rate_limit():
    path = request.path

    if not (
        path.startswith("/admin")
        or path.startswith("/api/admin/")
    ):
        return None

    ip = request.remote_addr or "unknown"
    now = time.time()

    timestamps = _admin_request_log.get(ip, [])
    timestamps = [
        t for t in timestamps
        if now - t < ADMIN_RATE_WINDOW
    ]

    if len(timestamps) >= ADMIN_RATE_LIMIT:
        return jsonify({
            "error": "Too many requests. Please try again later."
        }), 429

    timestamps.append(now)
    _admin_request_log[ip] = timestamps

    return None


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":
        username = str(request.form.get("username", "")).strip()
        password = str(request.form.get("password", ""))

        if username == ADMIN_USER and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_page"))

        return send_from_directory(BASE_DIR, "admin_login.html"), 401

    return send_from_directory(BASE_DIR, "admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))
CORS(app)


# ============================================================
# DATABASE
# ============================================================

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()


class DBCursor:
    def __init__(self, cursor, is_postgres):
        self._cursor = cursor
        self.is_postgres = is_postgres

    def execute(self, sql, params=()):
        if self.is_postgres:
            sql = sql.replace("?", "%s")

        if params:
            self._cursor.execute(sql, params)
        else:
            self._cursor.execute(sql)

        return self

    def executemany(self, sql, seq):
        if self.is_postgres:
            sql = sql.replace("?", "%s")

        self._cursor.executemany(sql, seq)
        return self

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    def __getattr__(self, name):
        return getattr(self._cursor, name)


class DBConnection:
    def __init__(self, conn, is_postgres=False):
        self._conn = conn
        self.is_postgres = is_postgres

    def execute(self, sql, params=()):
        if self.is_postgres:
            sql = sql.replace("?", "%s")

        if params:
            return self._conn.execute(sql, params)

        return self._conn.execute(sql)

    def executemany(self, sql, seq):
        if self.is_postgres:
            sql = sql.replace("?", "%s")

        return self._conn.executemany(sql, seq)

    def cursor(self):
        return DBCursor(
            self._conn.cursor(),
            self.is_postgres
        )

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        return self._conn.close()

    def __getattr__(self, name):
        return getattr(self._conn, name)


def get_db():
    if DATABASE_URL:
        conn = psycopg.connect(
            DATABASE_URL,
            row_factory=dict_row
        )
        return DBConnection(conn, True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return DBConnection(conn, False)


def get_products():
    conn = get_db()

    rows = conn.execute("""
        SELECT
            id,
            jenis,
            nama,
            nama_en,
            harga,
            link,
            deskripsi,
            deskripsi_en,
            kategori,
            subkategori,
            rating,
            marketplace
        FROM products
        ORDER BY id ASC
    """).fetchall()

    conn.close()

    return [dict(row) for row in rows]


def get_categories():
    conn = get_db()

    rows = conn.execute("""
        SELECT
            id,
            nama,
            nama_en,
            icon
        FROM categories
        ORDER BY id ASC
    """).fetchall()

    conn.close()

    return [dict(row) for row in rows]


# ============================================================
# SEARCH
# ============================================================

def search_products(
    query="",
    category="",
    min_price=None,
    max_price=None
):
    products = get_products()

    query = str(query or "").strip().lower()
    category = str(category or "").strip().lower()

    results = []

    for product in products:

        searchable = " ".join([
            str(product.get("nama", "")),
            str(product.get("nama_en", "")),
            str(product.get("deskripsi", "")),
            str(product.get("deskripsi_en", "")),
            str(product.get("kategori", "")),
            str(product.get("subkategori", "")),
            str(product.get("marketplace", ""))
        ]).lower()

        if query and query not in searchable:
            continue

        if category:
            product_category = str(
                product.get("kategori", "")
            ).lower()

            if category != product_category:
                continue

        price = int(product.get("harga") or 0)

        if min_price is not None and price < min_price:
            continue

        if max_price is not None and price > max_price:
            continue

        results.append(product)

    return results


# ============================================================
# PRODUCT MATCHING
# ============================================================

def match_products(message, products):

    text = str(message or "").lower()

    stop_words = {
        "saya",
        "ingin",
        "mau",
        "cari",
        "mencari",
        "tolong",
        "rekomendasikan",
        "produk",
        "yang",
        "untuk",
        "dengan",
        "dan",
        "atau",
        "harga",
        "anggaran",
        "budget",
        "please",
        "recommend",
        "product",
        "under",
        "the",
        "for",
        "with",
        "looking"
    }

    words = [
        word
        for word in re.findall(
            r"[a-zA-Z0-9&]+",
            text
        )
        if len(word) >= 3 and word not in stop_words
    ]

    scored = []

    for product in products:

        product_text = " ".join([
            str(product.get("nama", "")),
            str(product.get("nama_en", "")),
            str(product.get("deskripsi", "")),
            str(product.get("deskripsi_en", "")),
            str(product.get("kategori", "")),
            str(product.get("subkategori", ""))
        ]).lower()

        score = 0

        for word in words:
            if word in product_text:
                score += 1

        if score > 0:
            scored.append((score, product))

    scored.sort(
        key=lambda item: (
            item[0],
            -int(item[1].get("harga") or 0)
        ),
        reverse=True
    )

    return [
        item[1]
        for item in scored[:6]
    ]


# ============================================================
# PRODUCT CONTEXT
# ============================================================

def build_product_context(products):

    if not products:
        return "PRODUCT DATABASE IS EMPTY."

    lines = []

    for product in products:

        lines.append(
            f"ID={product['id']} | "
            f"NAMA_ID={product.get('nama','')} | "
            f"NAMA_EN={product.get('nama_en','')} | "
            f"HARGA=Rp{product.get('harga',0):,} | "
            f"KATEGORI_ID={product.get('kategori','')} | "
            f"SUBKATEGORI={product.get('subkategori','')} | "
            f"DESKRIPSI_ID={product.get('deskripsi','')} | "
            f"DESKRIPSI_EN={product.get('deskripsi_en','')} | "
            f"MARKETPLACE={product.get('marketplace','')} | "
            f"LINK={product.get('link','')}"
        )

    return "\n".join(lines)


# ============================================================
# AI PROMPT
# ============================================================

def build_system_prompt(products, language):

    context = build_product_context(products)

    if language == "en":

        language_rule = """
Use English only.
Do not use Indonesian words.
Do not mix Indonesian and English.
Use clear, professional English.
"""

        role = """
You are a professional Shopping Assistant.
"""

    else:

        language_rule = """
Gunakan Bahasa Indonesia saja.
Jangan menggunakan kata-kata Bahasa Inggris.
Jangan mencampurkan Bahasa Indonesia dan Bahasa Inggris.
Gunakan Bahasa Indonesia yang formal, jelas, ringkas, dan profesional.
"""

        role = """
Anda adalah Asisten Belanja profesional.
"""

    return f"""
{role}

TUJUAN:
Membantu pengguna menemukan produk berdasarkan database produk internal.

ATURAN WAJIB:

1. Database produk adalah satu-satunya sumber kebenaran.
2. Hanya rekomendasikan produk yang benar-benar ada di database.
3. Jangan mengarang nama produk.
4. Jangan mengarang harga.
5. Jangan mengarang tautan.
6. Jangan membuat produk baru.
7. Jangan mengklaim produk tersedia jika tidak ada.
8. Jika produk tidak tersedia, katakan dengan jujur.
9. Jangan mengubah data produk.
10. Jangan membuat tautan marketplace baru.
11. Jangan mengarang stok.
12. Jangan mengarang rating.
13. Jika tidak ada produk yang cocok, jangan memaksakan rekomendasi.
14. Gunakan informasi produk yang tersedia.
15. Gunakan bahasa sesuai aturan bahasa yang diberikan.

FORMAT JAWABAN:

Nama produk
Harga
Kategori
Alasan produk sesuai
Deskripsi singkat
Marketplace dan tautan jika tersedia

ATURAN BAHASA:
{language_rule}

DATABASE PRODUK:
--------------------------------------------------
{context}
--------------------------------------------------
"""


# ============================================================
# HOME
# ============================================================

@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/style.css")
def style():
    return send_from_directory(BASE_DIR, "style.css")


@app.route("/script.js")
def script():
    return send_from_directory(BASE_DIR, "script.js")


# ============================================================
# PRODUCTS
# ============================================================

@app.route("/api/products", methods=["GET"])
def products_api():
    return jsonify(get_products())


@app.route("/api/products/<int:product_id>", methods=["GET"])
def product_detail(product_id):

    conn = get_db()

    row = conn.execute("""
        SELECT
            id,
            jenis,
            nama,
            nama_en,
            harga,
            link,
            deskripsi,
            deskripsi_en,
            kategori,
            subkategori,
            rating,
            marketplace
        FROM products
        WHERE id = ?
    """, (product_id,)).fetchone()

    conn.close()

    if not row:
        return jsonify({
            "error": "Produk tidak ditemukan."
        }), 404

    return jsonify(dict(row))


# ============================================================
# CATEGORIES
# ============================================================

@app.route("/api/categories", methods=["GET"])
def categories_api():
    return jsonify(get_categories())


# ============================================================
# SEARCH + FILTER
# ============================================================

@app.route("/api/products/search", methods=["GET"])
def products_search():

    query = request.args.get("q", "")
    category = request.args.get("category", "")

    min_raw = request.args.get("min_price")
    max_raw = request.args.get("max_price")

    try:

        min_price = (
            int(min_raw)
            if min_raw not in [None, ""]
            else None
        )

        max_price = (
            int(max_raw)
            if max_raw not in [None, ""]
            else None
        )

    except ValueError:

        return jsonify({
            "error": "Harga harus berupa angka."
        }), 400

    return jsonify(
        search_products(
            query,
            category,
            min_price,
            max_price
        )
    )


# ============================================================
# SORT
# ============================================================

@app.route("/api/products/sort", methods=["GET"])
def products_sort():

    order = request.args.get(
        "order",
        "asc"
    ).lower()

    products = get_products()

    products.sort(
        key=lambda item: int(
            item.get("harga") or 0
        ),
        reverse=(order == "desc")
    )

    return jsonify(products)


# ============================================================
# AI CHAT
# ============================================================

@app.route("/api/chat", methods=["POST"])
def chat():

    data = request.get_json(
        silent=True
    ) or {}

    message = str(
        data.get("message", "")
    ).strip()

    language = str(
        data.get("language", "id")
    ).lower()

    if language not in ["id", "en"]:
        language = "id"

    if not message:

        return jsonify({
            "reply": (
                "Silakan masukkan pertanyaan terlebih dahulu."
                if language == "id"
                else
                "Please enter a question first."
            ),
            "matched_products": []
        }), 400

    products = get_products()

    matched_products = match_products(
        message,
        products
    )

    system_prompt = build_system_prompt(
        products,
        language
    )

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": message
            }
        ],
        "stream": False,
        "options": {
            "temperature": 0.1
        }
    }

    try:

        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=120
        )

        response.raise_for_status()

        result = response.json()

        reply = (
            result
            .get("message", {})
            .get("content", "")
            .strip()
        )

        if not reply:

            reply = (
                "Maaf, saya belum dapat memberikan jawaban."
                if language == "id"
                else
                "Sorry, I could not provide an answer."
            )

        return jsonify({
            "reply": reply,
            "matched_products": matched_products
        })

    except requests.exceptions.RequestException:

        return jsonify({
            "reply": (
                "Maaf, Asisten AI sedang tidak dapat terhubung ke layanan AI."
                if language == "id"
                else
                "Sorry, the AI Assistant cannot connect to the AI service."
            ),
            "matched_products": matched_products
        }), 500

    except Exception as error:

        return jsonify({
            "reply": (
                "Maaf, terjadi kesalahan pada Asisten AI."
                if language == "id"
                else
                "Sorry, an error occurred in the AI Assistant."
            ),
            "matched_products": matched_products,
            "error": str(error)
        }), 500


# ============================================================
# STATS
# ============================================================

@app.route("/api/stats", methods=["GET"])
def stats():

    products = get_products()
    categories = get_categories()

    prices = [
        int(product.get("harga") or 0)
        for product in products
    ]

    return jsonify({
        "products": len(products),
        "categories": len(categories),
        "min_price": min(prices) if prices else 0,
        "max_price": max(prices) if prices else 0
    })


# ============================================================
# HEALTH
# ============================================================

@app.route("/api/health", methods=["GET"])
def health():

    return jsonify({
        "status": "ok",
        "ai": "Ollama",
        "model": MODEL,
        "products": len(get_products()),
        "categories": len(get_categories())
    })


# ============================================================
# SERVER
# ============================================================


@app.route("/api/shopping-assistant", methods=["POST"])
def shopping_assistant():
    try:
        data = request.get_json(silent=True) or {}
        message = str(data.get("message", "")).strip()

        if not message:
            return jsonify({
                "reply": "Silakan jelaskan produk yang Anda cari.",
                "products": []
            })

        products = get_products()

        # Cari produk berdasarkan teks pengguna.
        query = message.lower()

        matched = []

        for product in products:
            searchable = " ".join([
                str(product.get("nama") or ""),
                str(product.get("nama_en") or ""),
                str(product.get("deskripsi") or ""),
                str(product.get("deskripsi_en") or ""),
                str(product.get("kategori") or ""),
                str(product.get("subkategori") or "")
            ]).lower()

            score = 0

            for word in query.split():
                if len(word) >= 3 and word in searchable:
                    score += 1

            if score > 0:
                matched.append((score, product))

        matched.sort(
            key=lambda x: x[0],
            reverse=True
        )

        recommendations = [
            item[1]
            for item in matched[:5]
        ]

        context_text = ""

        for product in recommendations:
            context_text += (
                "ID: " + str(product.get("id")) +
                "\nNama: " + str(product.get("nama") or "") +
                "\nHarga: Rp" + str(product.get("harga") or 0) +
                "\nKategori: " + str(product.get("kategori") or "") +
                "\nDeskripsi: " + str(product.get("deskripsi") or "") +
                "\nMarketplace: " + str(product.get("marketplace") or "") +
                "\n\n"
            )

        if not context_text:
            context_text = "Tidak ada produk yang cocok."

        prompt = (
            "Anda adalah AI Shopping Assistant.\n\n"
            "Gunakan hanya produk yang tersedia pada DATA PRODUK.\n"
            "Jangan mengarang nama, harga, link, stok, atau produk.\n"
            "Jika tidak ada produk yang cocok, katakan dengan jujur.\n"
            "Berikan alasan singkat mengapa produk cocok.\n"
            "Gunakan bahasa Indonesia profesional.\n\n"
            "DATA PRODUK:\n"
            + context_text
            + "\nPERMINTAAN PENGGUNA:\n"
            + message
        )

        payload = {
            "model": MODEL,
            "stream": False,
            "prompt": prompt
        }

        response = requests.post(
            OLLAMA_URL.replace("/api/chat", "/api/generate"),
            json=payload,
            timeout=120
        )

        response.raise_for_status()

        result = response.json()

        reply = str(
            result.get("response") or
            "Saya belum menemukan rekomendasi yang sesuai."
        ).strip()

        return jsonify({
            "reply": reply,
            "products": recommendations
        })

    except Exception as e:
        print("SHOPPING ASSISTANT ERROR:", repr(e))

        return jsonify({
            "reply": "Maaf, Asisten Belanja sedang mengalami kendala.",
            "products": [],
            "error": str(e)
        }), 500

@app.route("/api/products/<int:product_id>/click", methods=["POST"])
def product_click(product_id):
    conn = get_db()
    row = conn.execute(
        "SELECT marketplace FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()

    if not row:
        conn.close()
        return jsonify({"error": "Produk tidak ditemukan."}), 404

    conn.execute(
        "INSERT INTO product_clicks (product_id, marketplace) VALUES (?, ?)",
        (product_id, row["marketplace"] or "")
    )
    conn.commit()
    conn.close()

    return jsonify({
        "status": "ok",
        "product_id": product_id
    })


@app.route("/go/<int:product_id>")
def affiliate_redirect(product_id):
    conn = get_db()

    row = conn.execute(
        "SELECT link, marketplace, is_affiliate FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()

    if not row:
        conn.close()
        return jsonify({"error": "Produk tidak ditemukan."}), 404

    link = (row["link"] or "").strip()
    marketplace = row["marketplace"] or ""

    if not link.startswith(("http://", "https://")):
        conn.close()
        return jsonify({"error": "Link produk tidak valid."}), 400

    conn.execute(
        "INSERT INTO product_clicks (product_id, marketplace) VALUES (?, ?)",
        (product_id, marketplace)
    )
    conn.commit()
    conn.close()

    return redirect(link)


@app.route("/admin")
def admin_page():
    return send_from_directory(BASE_DIR, "admin.html")


@app.route("/api/admin/products", methods=["POST"])
def admin_create_product():
    data = request.get_json(silent=True) or {}

    nama = str(data.get("nama", "")).strip()
    harga_raw = data.get("harga", 0)
    link = str(data.get("link", "")).strip()
    deskripsi = str(data.get("deskripsi", "")).strip()
    kategori = str(data.get("kategori", "Hadiah & Lainnya")).strip()
    subkategori = str(data.get("subkategori", "")).strip()
    marketplace = str(data.get("marketplace", "")).strip()
    jenis = str(data.get("jenis", marketplace)).strip()

    if not nama:
        return jsonify({"error": "Nama produk wajib diisi."}), 400

    try:
        harga = int(harga_raw)
        if harga < 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "Harga harus berupa angka 0 atau lebih."}), 400

    conn = get_db()

    cur = conn.execute("""
        INSERT INTO products
        (jenis, nama, harga, link, deskripsi, kategori, subkategori,
         rating, marketplace, nama_en, deskripsi_en, is_affiliate)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        jenis,
        nama,
        harga,
        link,
        deskripsi,
        kategori,
        subkategori,
        0,
        marketplace,
        "",
        "",
        1 if marketplace.lower() == "shopee" else 0
    ))

    conn.commit()
    product_id = cur.lastrowid
    conn.close()

    return jsonify({
        "status": "ok",
        "product_id": product_id
    }), 201


@app.route("/api/admin/products/<int:product_id>", methods=["PUT"])
def admin_update_product(product_id):
    data = request.get_json(silent=True) or {}

    conn = get_db()

    row = conn.execute(
        "SELECT id FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()

    if not row:
        conn.close()
        return jsonify({"error": "Produk tidak ditemukan."}), 404

    allowed = {
        "nama": data.get("nama"),
        "harga": data.get("harga"),
        "link": data.get("link"),
        "deskripsi": data.get("deskripsi"),
        "kategori": data.get("kategori"),
        "subkategori": data.get("subkategori"),
        "marketplace": data.get("marketplace"),
    }

    if allowed["nama"] is not None:
        nama = str(allowed["nama"]).strip()
        if not nama:
            conn.close()
            return jsonify({"error": "Nama produk tidak boleh kosong."}), 400
        conn.execute(
            "UPDATE products SET nama=? WHERE id=?",
            (nama, product_id)
        )

    if allowed["harga"] is not None:
        try:
            harga = int(allowed["harga"])
            if harga < 0:
                raise ValueError
        except (TypeError, ValueError):
            conn.close()
            return jsonify({"error": "Harga harus berupa angka 0 atau lebih."}), 400

        conn.execute(
            "UPDATE products SET harga=? WHERE id=?",
            (harga, product_id)
        )

    field_map = {
        "link": "link",
        "deskripsi": "deskripsi",
        "kategori": "kategori",
        "subkategori": "subkategori",
        "marketplace": "marketplace",
    }

    for key, column in field_map.items():
        if allowed[key] is not None:
            conn.execute(
                f"UPDATE products SET {column}=? WHERE id=?",
                (str(allowed[key]).strip(), product_id)
            )

    conn.commit()
    conn.close()

    return jsonify({
        "status": "ok",
        "product_id": product_id
    })


@app.route("/api/admin/products/<int:product_id>", methods=["DELETE"])
def admin_delete_product(product_id):
    conn = get_db()

    row = conn.execute(
        "SELECT id FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()

    if not row:
        conn.close()
        return jsonify({"error": "Produk tidak ditemukan."}), 404

    conn.execute(
        "DELETE FROM products WHERE id = ?",
        (product_id,)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "status": "ok",
        "product_id": product_id
    })


@app.route("/api/admin/products/<int:product_id>/affiliate", methods=["PUT"])
def admin_set_affiliate(product_id):
    data = request.get_json(silent=True) or {}

    if "is_affiliate" not in data:
        return jsonify({
            "error": "Field is_affiliate wajib diisi"
        }), 400

    value = data.get("is_affiliate")

    if isinstance(value, bool):
        is_affiliate = 1 if value else 0
    elif str(value).strip() in ("1", "true", "True"):
        is_affiliate = 1
    elif str(value).strip() in ("0", "false", "False"):
        is_affiliate = 0
    else:
        return jsonify({
            "error": "is_affiliate harus bernilai true/false"
        }), 400

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT id FROM products WHERE id = ?",
        (product_id,)
    )

    if cur.fetchone() is None:
        conn.close()
        return jsonify({
            "error": "Produk tidak ditemukan"
        }), 404

    cur.execute(
        "UPDATE products SET is_affiliate = ? WHERE id = ?",
        (is_affiliate, product_id)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "product_id": product_id,
        "is_affiliate": bool(is_affiliate)
    })


@app.route("/api/admin/products/<int:product_id>/commission", methods=["PUT"])
def admin_set_commission(product_id):
    data = request.get_json(silent=True) or {}
    value = data.get("commission_rate")

    try:
        rate = float(value)
    except (TypeError, ValueError):
        return jsonify({
            "error": "commission_rate harus berupa angka"
        }), 400

    if rate < 0 or rate > 100:
        return jsonify({
            "error": "commission_rate harus antara 0 dan 100"
        }), 400

    conn = get_db()

    row = conn.execute(
        "SELECT id, harga FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()

    if not row:
        conn.close()
        return jsonify({
            "error": "Produk tidak ditemukan"
        }), 404

    conn.execute(
        "UPDATE products SET commission_rate = ? WHERE id = ?",
        (rate, product_id)
    )
    conn.commit()
    conn.close()

    harga = float(row["harga"] or 0)
    estimated_commission = harga * (rate / 100)

    return jsonify({
        "success": True,
        "product_id": product_id,
        "commission_rate": rate,
        "estimated_commission": estimated_commission
    })


@app.route("/api/admin/monetization", methods=["GET"])
def admin_monetization_stats():
    conn = get_db()

    summary = conn.execute("""
        SELECT
            COUNT(*) AS affiliate_products,
            COALESCE(SUM(
                COALESCE(pc.clicks, 0)
            ), 0) AS affiliate_clicks,
            COALESCE(SUM(
                COALESCE(pc.clicks, 0)
                * (CAST(p.harga AS REAL) * COALESCE(p.commission_rate, 0) / 100.0)
            ), 0) AS estimated_commission
        FROM products p
        LEFT JOIN (
            SELECT product_id, COUNT(*) AS clicks
            FROM product_clicks
            GROUP BY product_id
        ) pc ON pc.product_id = p.id
        WHERE COALESCE(p.is_affiliate, 0) = 1
    """).fetchone()

    products = conn.execute("""
        SELECT
            p.id,
            p.nama,
            p.harga,
            COALESCE(p.commission_rate, 0) AS commission_rate,
            COALESCE(pc.clicks, 0) AS clicks,
            COALESCE(
                pc.clicks * (CAST(p.harga AS REAL) * COALESCE(p.commission_rate, 0) / 100.0),
                0
            ) AS estimated_commission
        FROM products p
        LEFT JOIN (
            SELECT product_id, COUNT(*) AS clicks
            FROM product_clicks
            GROUP BY product_id
        ) pc ON pc.product_id = p.id
        WHERE COALESCE(p.is_affiliate, 0) = 1
        ORDER BY clicks DESC, p.id DESC
    """).fetchall()

    conn.close()

    return jsonify({
        "summary": {
            "affiliate_products": int(summary["affiliate_products"] or 0),
            "affiliate_clicks": int(summary["affiliate_clicks"] or 0),
            "estimated_commission": float(summary["estimated_commission"] or 0)
        },
        "products": [
            {
                "id": int(row["id"]),
                "nama": row["nama"],
                "harga": float(row["harga"] or 0),
                "commission_rate": float(row["commission_rate"] or 0),
                "clicks": int(row["clicks"] or 0),
                "estimated_commission": float(row["estimated_commission"] or 0)
            }
            for row in products
        ]
    })


@app.route("/api/admin/stats", methods=["GET"])
def admin_stats():
    conn = get_db()

    products = conn.execute(
        "SELECT COUNT(*) FROM products"
    ).fetchone()[0]

    categories = conn.execute(
        "SELECT COUNT(*) FROM categories"
    ).fetchone()[0]

    clicks = conn.execute(
        "SELECT COUNT(*) FROM product_clicks"
    ).fetchone()[0]

    conn.close()

    return jsonify({
        "products": products,
        "categories": categories,
        "clicks": clicks
    })

if __name__ == "__main__":

    print("""
========================================
       AI SHOPPING ASSISTANT
========================================
Website : http://127.0.0.1:5000
AI      : Ollama
Model   : qwen2.5:3b
Database: C:\\AI-WEBSITE\\backend\\assistant.db
========================================
""")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )






