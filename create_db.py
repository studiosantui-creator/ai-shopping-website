import sqlite3

db = r"backend\assistant.db"

conn = sqlite3.connect(db)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    jenis TEXT,
    nama TEXT,
    harga INTEGER,
    link TEXT,
    deskripsi TEXT
)
""")

cursor.execute("SELECT COUNT(*) FROM products")

if cursor.fetchone()[0] == 0:
    cursor.execute("""
    INSERT INTO products (jenis, nama, harga, link, deskripsi)
    VALUES (?, ?, ?, ?, ?)
    """, (
        "lynkid",
        "Ebook AI Agent Pemula",
        50000,
        "https://contoh.com/ebook",
        "Ebook belajar membuat AI Agent dari dasar."
    ))

    cursor.execute("""
    INSERT INTO products (jenis, nama, harga, link, deskripsi)
    VALUES (?, ?, ?, ?, ?)
    """, (
        "shopee",
        "Mouse Wireless",
        150000,
        "https://contoh.com",
        "Mouse wireless untuk kerja dan belajar."
    ))

conn.commit()

print("DATABASE BERHASIL DIBUAT")
print("Produk:")

for row in cursor.execute("SELECT * FROM products"):
    print(row)

conn.close()
