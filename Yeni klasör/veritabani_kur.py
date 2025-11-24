import sqlite3
import os

# Veritabanı dosyasının adı
DB_NAME = "dershane.db"

def veritabanini_olustur():
    """
    Gerekli tablolarla birlikte veritabanını oluşturur.
    Eğer tablolar zaten varsa, yeniden oluşturmaz.
    """
    
    # Veritabanına bağlan (Dosya yoksa otomatik olarak oluşturulur)
    try:
        baglanti = sqlite3.connect(DB_NAME)
        cursor = baglanti.cursor()
        
        # 1. Ogretmenler Tablosu
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Ogretmenler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad TEXT NOT NULL,
            soyad TEXT NOT NULL,
            brans TEXT
        )
        """)
        
        # 2. Ogrenciler Tablosu 
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Ogrenciler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad TEXT NOT NULL,
            soyad TEXT NOT NULL,
            sinif TEXT,
            numara TEXT UNIQUE
        )
        """)
        
        # 3. Etutler Tablosu 
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Etutler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ogretmen_id INTEGER,
            ogrenci_id INTEGER,
            ders_adi TEXT NOT NULL,
            tarih TEXT NOT NULL,
            saat TEXT NOT NULL,
            katilim_durumu TEXT DEFAULT 'Planlandı', 
            FOREIGN KEY (ogretmen_id) REFERENCES Ogretmenler(id) ON DELETE SET NULL,
            FOREIGN KEY (ogrenci_id) REFERENCES Ogrenciler(id) ON DELETE CASCADE
        )
        """)

        baglanti.commit()
        print(f"BAŞARILI: '{DB_NAME}' veritabanı ve tablolar başarıyla oluşturuldu/kontrol edildi.")
        
    except sqlite3.Error as e:
        print(f"VERİTABANI HATASI: {e}")
        
    finally:
        if baglanti:
            baglanti.close()

# --- Ana programı çalıştır ---
if __name__ == "__main__":
    veritabanini_olustur()