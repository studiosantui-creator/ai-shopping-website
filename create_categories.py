import sqlite3
import os

DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "backend",
    "assistant.db"
)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama TEXT NOT NULL,
    nama_en TEXT NOT NULL,
    icon TEXT NOT NULL
)
""")

categories = [
    ("Dapur", "Kitchen", "🍳"),
    ("Kamar Tidur", "Bedroom", "🛏️"),
    ("Kamar Mandi", "Bathroom", "🚿"),
    ("Ruang Tamu", "Living Room", "🛋️"),
    ("Kebersihan Rumah", "Home Cleaning", "🧹"),
    ("Tools & Perkakas", "Tools & Hardware", "🔧"),
    ("Taman & Outdoor", "Garden & Outdoor", "🌿"),
    ("Elektronik Rumah", "Home Electronics", "⚡"),
    ("Otomotif", "Automotive", "🚗"),
    ("Gadget & Elektronik", "Gadgets & Electronics", "💻"),
    ("Fashion", "Fashion", "👕"),
    ("Olahraga", "Sports", "🏃"),
    ("Sekolah & Kantor", "School & Office", "🎒"),
    ("Bayi & Anak", "Baby & Kids", "🧸"),
    ("Hewan Peliharaan", "Pets", "🐾"),
    ("Kecantikan & Perawatan", "Beauty & Personal Care", "✨"),
    ("Makanan & Minuman", "Food & Beverage", "🍽️"),
    ("Travel", "Travel", "🧳"),
    ("Hobi & Hiburan", "Hobbies & Entertainment", "🎮"),
    ("Hadiah & Lainnya", "Gifts & Others", "🎁")
]

for nama, nama_en, icon in categories:
    cursor.execute(
        "SELECT id FROM categories WHERE nama = ?",
        (nama,)
    )

    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO categories (nama, nama_en, icon) VALUES (?, ?, ?)",
            (nama, nama_en, icon)
        )

conn.commit()
conn.close()

print("Kategori berhasil dibuat.")
