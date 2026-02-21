import sqlite3
import logging
import os
from datetime import datetime

logging.basicConfig(
    filename='app_errors.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
import sys
import zipfile
import shutil

def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(".")

class MasterDatabase:
    def __init__(self, master_db="master.db"):
        self.db_name = os.path.join(get_base_path(), master_db)
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_name)

    def _init_db(self):
        try:
            with self._connect() as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS sirketler (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sirket_adi TEXT NOT NULL UNIQUE,
                        db_kodu TEXT NOT NULL UNIQUE,
                        olusturma_tarihi TEXT,
                        is_deleted INTEGER DEFAULT 0
                    )
                ''')
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS master_ayarlar (
                        anahtar TEXT PRIMARY KEY,
                        deger TEXT
                    )
                ''')
                conn.execute("INSERT OR IGNORE INTO master_ayarlar (anahtar, deger) VALUES ('tema', 'Dark')")
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Master DB oluşturma hatası: {e}")

    def tum_sirketleri_getir(self):
        with self._connect() as conn:
            return conn.execute("SELECT id, sirket_adi, db_kodu FROM sirketler WHERE is_deleted=0 ORDER BY id DESC").fetchall()

    def sirket_ekle(self, sirket_adi, db_kodu):
        try:
            with self._connect() as conn:
                tarih = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                conn.execute("INSERT INTO sirketler (sirket_adi, db_kodu, olusturma_tarihi) VALUES (?, ?, ?)",
                             (sirket_adi, db_kodu, tarih))
                conn.commit()
                return True
        except sqlite3.Error: return False

    def sirket_sil(self, sirket_id):
        try:
            with self._connect() as conn:
                conn.execute("DELETE FROM sirketler WHERE id=?", (sirket_id,))
                conn.commit()
                return True
        except sqlite3.Error: return False

    def sirket_guncelle(self, sirket_id, yeni_ad):
        try:
            with self._connect() as conn:
                conn.execute("UPDATE sirketler SET sirket_adi=? WHERE id=?", (yeni_ad, sirket_id))
                conn.commit()
                return True
        except sqlite3.Error: return False

    def ayar_getir(self, anahtar, varsayilan=None):
        with self._connect() as conn:
            res = conn.execute("SELECT deger FROM master_ayarlar WHERE anahtar=?", (anahtar,)).fetchone()
            return res[0] if res else varsayilan

    def ayar_kaydet(self, anahtar, deger):
        with self._connect() as conn:
            conn.execute("INSERT OR REPLACE INTO master_ayarlar (anahtar, deger) VALUES (?, ?)", (anahtar, deger))
            conn.commit()

class AppDatabase:
    def __init__(self, db_name="muhasebe.db"):
        if not os.path.isabs(db_name):
            self.db_name = os.path.join(get_base_path(), db_name)
        else:
            self.db_name = db_name
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_name)

    def _init_db(self):
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                
                # 1. Cari
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cariler (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        unvan TEXT NOT NULL,
                        vergi_no TEXT,
                        telefon TEXT,
                        bakiye REAL DEFAULT 0.0,
                        eklenme_tarihi TEXT,
                        cari_turu TEXT DEFAULT 'Hibrit', -- 'Müşteri', 'Tedarikçi', 'Hibrit'
                        ozel_iskonto REAL DEFAULT 0.0,
                        fiyat_grubu TEXT, -- 'Liste', 'Özel1', 'Özel2' vb.
                        is_deleted INTEGER DEFAULT 0
                    )
                ''')
                
                # 2. Stok
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS stoklar (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        barkod TEXT UNIQUE,
                        urun_adi TEXT NOT NULL,
                        miktar INTEGER DEFAULT 0,
                        kritik_seviye INTEGER DEFAULT 10,
                        fiyat REAL DEFAULT 0.0,
                        is_deleted INTEGER DEFAULT 0
                    )
                ''')
                
                # 3. Kasa
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS kasalar (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        hesap_adi TEXT NOT NULL,
                        bakiye REAL DEFAULT 0.0,
                        is_deleted INTEGER DEFAULT 0
                    )
                ''')

                # Varsayılan Kasa oluştur (Eğer boşsa)
                cursor.execute("SELECT COUNT(*) FROM kasalar")
                if cursor.fetchone()[0] == 0:
                    cursor.execute("INSERT INTO kasalar (hesap_adi, bakiye) VALUES ('Merkez Kasa', 0.0)")
                
                # 4. Kasa Hareketleri
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS kasa_hareketleri (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        kasa_id INTEGER,
                        cari_id INTEGER,
                        tarih TEXT,
                        tutar REAL,
                        tur TEXT, -- 'Giriş' / 'Çıkış'
                        aciklama TEXT,
                        proje_kodu TEXT,
                        is_deleted INTEGER DEFAULT 0,
                        FOREIGN KEY(kasa_id) REFERENCES kasalar(id),
                        FOREIGN KEY(cari_id) REFERENCES cariler(id)
                    )
                ''')

                # 4b. Bankalar
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS bankalar (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        hesap_adi TEXT NOT NULL,
                        iban TEXT,
                        bakiye REAL DEFAULT 0.0,
                        is_deleted INTEGER DEFAULT 0
                    )
                ''')

                # 4c. Banka Hareketleri
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS banka_hareketleri (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        banka_id INTEGER,
                        cari_id INTEGER,
                        tarih TEXT,
                        tutar REAL,
                        tur TEXT, -- 'Giriş' / 'Çıkış'
                        aciklama TEXT,
                        proje_kodu TEXT,
                        is_deleted INTEGER DEFAULT 0,
                        FOREIGN KEY(banka_id) REFERENCES bankalar(id),
                        FOREIGN KEY(cari_id) REFERENCES cariler(id)
                    )
                ''')

                # Kasa ve Banka Hareketleri tablosuna sonradan cari_id eklemek (eski db uyumluluğu)
                try: cursor.execute("ALTER TABLE kasa_hareketleri ADD COLUMN cari_id INTEGER REFERENCES cariler(id)")
                except sqlite3.OperationalError: pass
                
                try: cursor.execute("ALTER TABLE banka_hareketleri ADD COLUMN cari_id INTEGER REFERENCES cariler(id)")
                except sqlite3.OperationalError: pass

                # 5. Fatura
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS faturalar (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        fatura_no TEXT UNIQUE,
                        cari_id INTEGER,
                        tarih TEXT,
                        toplam_tutar REAL DEFAULT 0.0,
                        tur TEXT, -- 'Alış' / 'Satış'
                        belge_turu TEXT DEFAULT 'Fatura', -- 'Sipariş', 'İrsaliye', 'Fatura'
                        fiyat_goster INTEGER DEFAULT 1, -- 0: Gizle, 1: Göster
                        kaynak_id INTEGER, -- Dönüştürülen evrağın ID'si
                        odeme_turu TEXT DEFAULT 'Nakit', -- 'Nakit', 'Veresiye'
                        proje_kodu TEXT,
                        yuvarlama_farki REAL DEFAULT 0.0,
                        tevkifat_turu TEXT,
                        is_deleted INTEGER DEFAULT 0,
                        FOREIGN KEY(cari_id) REFERENCES cariler(id),
                        FOREIGN KEY(kaynak_id) REFERENCES faturalar(id)
                    )
                ''')
                
                # 6. Fatura Detay
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS fatura_detay (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        fatura_id INTEGER,
                        stok_id INTEGER,
                        miktar REAL,
                        birim_fiyat REAL,
                        kdv_orani REAL DEFAULT 0.0,
                        tevkifat_orani REAL DEFAULT 0.0,
                        birim TEXT,
                        is_deleted INTEGER DEFAULT 0,
                        FOREIGN KEY(fatura_id) REFERENCES faturalar(id),
                        FOREIGN KEY(stok_id) REFERENCES stoklar(id)
                    )
                ''')
                
                # 7. Audit Log
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS audit_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tablo_adi TEXT,
                        kayit_id INTEGER,
                        islem_turu TEXT, -- 'INSERT', 'UPDATE', 'DELETE'
                        eski_deger TEXT,
                        yeni_deger TEXT,
                        kullanici TEXT,
                        tarih TEXT
                    )
                ''')
                # Tablo sütun güncellemeleri (Eski DB'ler için)
                try: cursor.execute("ALTER TABLE cariler ADD COLUMN cari_turu TEXT DEFAULT 'Hibrit'")
                except: pass
                try: cursor.execute("ALTER TABLE cariler ADD COLUMN ozel_iskonto REAL DEFAULT 0.0")
                except: pass
                try: cursor.execute("ALTER TABLE cariler ADD COLUMN fiyat_grubu TEXT")
                except: pass
                
                try: cursor.execute("ALTER TABLE faturalar ADD COLUMN belge_turu TEXT DEFAULT 'Fatura'")
                except: pass
                try: cursor.execute("ALTER TABLE faturalar ADD COLUMN fiyat_goster INTEGER DEFAULT 1")
                except: pass
                try: cursor.execute("ALTER TABLE faturalar ADD COLUMN kaynak_id INTEGER")
                except: pass
                try: cursor.execute("ALTER TABLE faturalar ADD COLUMN odeme_turu TEXT DEFAULT 'Nakit'")
                except: pass

                # Yeni Alanlar: KDV, Tevkifat, Birim
                try: cursor.execute("ALTER TABLE fatura_detay ADD COLUMN kdv_orani REAL DEFAULT 0.0")
                except: pass
                try: cursor.execute("ALTER TABLE fatura_detay ADD COLUMN tevkifat_orani REAL DEFAULT 0.0")
                except: pass
                try: cursor.execute("ALTER TABLE stoklar ADD COLUMN birim TEXT DEFAULT 'Adet'")
                except: pass
                try: cursor.execute("ALTER TABLE fatura_detay ADD COLUMN birim TEXT DEFAULT ''")
                except: pass
                try: cursor.execute("ALTER TABLE faturalar ADD COLUMN aciklama TEXT")
                except: pass
                
                # v2.0 Güncellemeleri
                tablolar = ["cariler", "stoklar", "kasalar", "bankalar", "faturalar", "kasa_hareketleri", "banka_hareketleri"]
                for t in tablolar:
                    try: cursor.execute(f"ALTER TABLE {t} ADD COLUMN is_deleted INTEGER DEFAULT 0")
                    except: pass
                
                try: cursor.execute("ALTER TABLE faturalar ADD COLUMN proje_kodu TEXT")
                except: pass
                try: cursor.execute("ALTER TABLE faturalar ADD COLUMN yuvarlama_farki REAL DEFAULT 0.0")
                except: pass
                try: cursor.execute("ALTER TABLE faturalar ADD COLUMN tevkifat_turu TEXT")
                except: pass
                try: cursor.execute("ALTER TABLE kasa_hareketleri ADD COLUMN proje_kodu TEXT")
                except: pass
                try: cursor.execute("ALTER TABLE banka_hareketleri ADD COLUMN proje_kodu TEXT")
                except: pass
                try: cursor.execute("ALTER TABLE faturalar ADD COLUMN dosya_yolu TEXT")
                except: pass

                # Varsayılan Perakende Carisi
                cursor.execute("SELECT COUNT(*) FROM cariler WHERE unvan='PERAKENDE MÜŞTERİ'")
                if cursor.fetchone()[0] == 0:
                    cursor.execute("INSERT INTO cariler (unvan, cari_turu, bakiye) VALUES ('PERAKENDE MÜŞTERİ', 'Müşteri', 0.0)")

                # 8. Cari Notlar (v1.6)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cari_notlar (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cari_id INTEGER,
                        not_icerik TEXT,
                        guncelleme_tarihi TEXT,
                        is_deleted INTEGER DEFAULT 0,
                        FOREIGN KEY(cari_id) REFERENCES cariler(id)
                    )
                ''')

                # 9. Takvim Etkinlikleri (v1.6)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS takvim_etkinlikleri (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        baslik TEXT,
                        aciklama TEXT,
                        tarih TEXT,
                        saat TEXT,
                        oncelik TEXT DEFAULT 'Normal',
                        is_deleted INTEGER DEFAULT 0
                    )
                ''')

                # 10. Çalışanlar (v1.6)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS calisanlar (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ad_soyad TEXT NOT NULL,
                        kategori TEXT,
                        ise_giris TEXT,
                        isten_cikis TEXT,
                        aylik_maas REAL DEFAULT 0.0,
                        telefon TEXT,
                        bakiye REAL DEFAULT 0.0,
                        is_deleted INTEGER DEFAULT 0
                    )
                ''')

                # 11. Personel Hareketleri (v1.6)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS personel_hareketleri (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        personel_id INTEGER,
                        tarih TEXT,
                        tutar REAL,
                        tur TEXT,
                        aciklama TEXT,
                        is_deleted INTEGER DEFAULT 0,
                        FOREIGN KEY(personel_id) REFERENCES calisanlar(id)
                    )
                ''')

                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Veri tabanı oluşturma hatası: {e}")

    def log_tut(self, tablo, kayit_id, islem, eski="", yeni="", kullanici="Sistem"):
        try:
            with self._connect() as conn:
                tarih = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                conn.execute(
                    "INSERT INTO audit_logs (tablo_adi, kayit_id, islem_turu, eski_deger, yeni_deger, kullanici, tarih) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (tablo, kayit_id, islem, str(eski), str(yeni), kullanici, tarih)
                )
                conn.commit()
        except Exception as e:
            logging.error(f"Audit log hatası: {e}")

    def yedekle(self):
        try:
            backup_folder = os.path.join(get_base_path(), "Backups")
            if not os.path.exists(backup_folder):
                os.makedirs(backup_folder)
            
            tarih_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            db_adi = os.path.basename(self.db_name)
            zip_adi = f"{db_adi}_{tarih_str}.zip"
            zip_path = os.path.join(backup_folder, zip_adi)
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(self.db_name, db_adi)
            
            # Eski yedekleri temizle (Son 10 yedek kalsın)
            yapakler = sorted([os.path.join(backup_folder, f) for f in os.listdir(backup_folder) if f.endswith('.zip')])
            if len(yapakler) > 10:
                for i in range(len(yapakler) - 10):
                    os.remove(yapakler[i])
            return True
        except Exception as e:
            logging.error(f"Yedekleme hatası: {e}")
            return False

    # --- AYARLAR ---
    def ayar_getir(self, anahtar, varsayilan=None):
        with self._connect() as conn:
            res = conn.execute("SELECT deger FROM ayarlar WHERE anahtar=?", (anahtar,)).fetchone()
            return res[0] if res else varsayilan

    def ayar_kaydet(self, anahtar, deger):
        with self._connect() as conn:
            conn.execute("INSERT OR REPLACE INTO ayarlar (anahtar, deger) VALUES (?, ?)", (anahtar, deger))
            conn.commit()

    # --- CARİ (MÜŞTERİ/TEDARİKÇİ) ---
    def cari_ekle(self, unvan, vergi_no, telefon, cari_turu='Hibrit', ozel_iskonto=0.0, fiyat_grubu=None, tarih=None):
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                if not tarih:
                    tarih = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute(
                    "INSERT INTO cariler (unvan, vergi_no, telefon, cari_turu, ozel_iskonto, fiyat_grubu, eklenme_tarihi) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (unvan, vergi_no, telefon, cari_turu, ozel_iskonto, fiyat_grubu, tarih)
                )
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Cari kayıt hatası: {e}")
            return False

    def cari_sil(self, cari_id):
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                # SOFT DELETE
                cursor.execute("UPDATE cariler SET is_deleted=1 WHERE id=?", (cari_id,))
                conn.commit()
                self.log_tut("cariler", cari_id, "DELETE", "is_deleted=0", "is_deleted=1")
                return True
        except sqlite3.Error as e:
            logging.error(f"Cari silme hatası: {e}")
            return False

    def cari_guncelle(self, cari_id, unvan, vergi_no, telefon, cari_turu='Hibrit', ozel_iskonto=0.0, fiyat_grubu=None):
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE cariler SET unvan=?, vergi_no=?, telefon=?, cari_turu=?, ozel_iskonto=?, fiyat_grubu=? WHERE id=?",
                    (unvan, vergi_no, telefon, cari_turu, ozel_iskonto, fiyat_grubu, cari_id)
                )
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Cari güncelleme hatası: {e}")
            return False

    def cari_bakiye_guncelle(self, cari_id, miktar, tur="Ekle"):
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                if tur == "Ekle":
                    cursor.execute("UPDATE cariler SET bakiye = bakiye + ? WHERE id=?", (miktar, cari_id))
                else:
                    cursor.execute("UPDATE cariler SET bakiye = bakiye - ? WHERE id=?", (miktar, cari_id))
                conn.commit()
                return True
        except sqlite3.Error: return False

    def tum_carileri_getir(self):
        with self._connect() as conn:
            return conn.execute("SELECT id, unvan, vergi_no, telefon, bakiye, eklenme_tarihi, cari_turu, ozel_iskonto, fiyat_grubu FROM cariler WHERE is_deleted=0").fetchall()

    # --- STOK / ENVANTER ---
    def stok_ekle(self, barkod, urun_adi, miktar, kritik_seviye, fiyat, birim='Adet'):
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO stoklar (barkod, urun_adi, miktar, kritik_seviye, fiyat, birim) VALUES (?, ?, ?, ?, ?, ?)",
                    (barkod, urun_adi, miktar, kritik_seviye, fiyat, birim)
                )
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Stok kayıt hatası: {e}")
            return False

    def stok_sil(self, stok_id):
        try:
            with self._connect() as conn:
                conn.execute("UPDATE stoklar SET is_deleted=1 WHERE id=?", (stok_id,))
                conn.commit()
                self.log_tut("stoklar", stok_id, "DELETE", "is_deleted=0", "is_deleted=1")
                return True
        except sqlite3.Error: return False

    def tum_stoklari_getir(self):
        with self._connect() as conn:
            return conn.execute("SELECT id, barkod, urun_adi, miktar, kritik_seviye, fiyat, COALESCE(birim,'Adet') FROM stoklar WHERE is_deleted=0").fetchall()

    def stok_guncelle_miktar(self, stok_id, artis):
        try:
            with self._connect() as conn:
                conn.execute("UPDATE stoklar SET miktar = miktar + ? WHERE id=?", (artis, stok_id))
                conn.commit()
                return True
        except sqlite3.Error: return False

    def stok_guncelle(self, stok_id, barkod, urun_adi, miktar, kritik_seviye, fiyat, birim='Adet'):
        try:
            with self._connect() as conn:
                conn.execute(
                    "UPDATE stoklar SET barkod=?, urun_adi=?, miktar=?, kritik_seviye=?, fiyat=?, birim=? WHERE id=?",
                    (barkod, urun_adi, miktar, kritik_seviye, fiyat, birim, stok_id)
                )
                conn.commit()
                return True
        except sqlite3.Error: return False

    # --- KASA ---
    def tum_kasalari_getir(self):
        with self._connect() as conn:
            return conn.execute("SELECT id, hesap_adi, bakiye FROM kasalar WHERE is_deleted=0").fetchall()

    def kasa_ekle(self, hesap_adi):
        try:
            with self._connect() as conn:
                conn.execute("INSERT INTO kasalar (hesap_adi) VALUES (?)", (hesap_adi,))
                conn.commit()
                return True
        except sqlite3.Error: return False

    def kasa_guncelle(self, kasa_id, hesap_adi):
        try:
            with self._connect() as conn:
                conn.execute("UPDATE kasalar SET hesap_adi=? WHERE id=?", (hesap_adi, kasa_id))
                conn.commit()
                return True
        except sqlite3.Error: return False

    def kasa_sil(self, kasa_id):
        try:
            with self._connect() as conn:
                conn.execute("UPDATE kasalar SET is_deleted=1 WHERE id=?", (kasa_id,))
                conn.commit()
                self.log_tut("kasalar", kasa_id, "DELETE", "is_deleted=0", "is_deleted=1")
                return True
        except sqlite3.Error: return False

    def kasa_hareketi_ekle(self, kasa_id, tutar, tur, aciklama, tarih=None, cari_id=None, proje_kodu=None):
        try:
            with self._connect() as conn:
                if not tarih:
                    tarih = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                conn.execute(
                    "INSERT INTO kasa_hareketleri (kasa_id, cari_id, tarih, tutar, tur, aciklama, proje_kodu) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (kasa_id, cari_id, tarih, tutar, tur, aciklama, proje_kodu)
                )
                if tur == "Giriş":
                    conn.execute("UPDATE kasalar SET bakiye = bakiye + ? WHERE id=?", (tutar, kasa_id))
                    if cari_id is not None:
                        conn.execute("UPDATE cariler SET bakiye = bakiye - ? WHERE id=?", (tutar, cari_id))
                else:
                    conn.execute("UPDATE kasalar SET bakiye = bakiye - ? WHERE id=?", (tutar, kasa_id))
                    if cari_id is not None:
                        conn.execute("UPDATE cariler SET bakiye = bakiye + ? WHERE id=?", (tutar, cari_id))
                conn.commit()
                return True
        except sqlite3.Error as e: 
            logging.error(f"Kasa movement error {e}")
            return False

    def kasa_hareket_sil(self, hareket_id):
        try:
            # Önce tutarı geri almalıyız
            with self._connect() as conn:
                h = conn.execute("SELECT kasa_id, tutar, tur, cari_id FROM kasa_hareketleri WHERE id=?", (hareket_id,)).fetchone()
                if h:
                    kid, tutar, tur, cid = h
                    if tur == "Giriş":
                        conn.execute("UPDATE kasalar SET bakiye = bakiye - ? WHERE id=?", (tutar, kid))
                        if cid is not None:
                            conn.execute("UPDATE cariler SET bakiye = bakiye + ? WHERE id=?", (tutar, cid))
                    else:
                        conn.execute("UPDATE kasalar SET bakiye = bakiye + ? WHERE id=?", (tutar, kid))
                        if cid is not None:
                            conn.execute("UPDATE cariler SET bakiye = bakiye - ? WHERE id=?", (tutar, cid))
                    conn.execute("DELETE FROM kasa_hareketleri WHERE id=?", (hareket_id,))
                    conn.commit()
                    return True
                return False
        except sqlite3.Error: return False

    def kasa_hareket_guncelle(self, h_id, n_kasa_id, n_tutar, n_tur, n_aciklama, n_tarih, n_cari_id):
        try:
            with self._connect() as conn:
                h = conn.execute("SELECT kasa_id, tutar, tur, cari_id FROM kasa_hareketleri WHERE id=?", (h_id,)).fetchone()
                if not h: return False
                kid, tutar, tur, cid = h
                if tur == "Giriş":
                    conn.execute("UPDATE kasalar SET bakiye = bakiye - ? WHERE id=?", (tutar, kid))
                    if cid is not None: conn.execute("UPDATE cariler SET bakiye = bakiye + ? WHERE id=?", (tutar, cid))
                else:
                    conn.execute("UPDATE kasalar SET bakiye = bakiye + ? WHERE id=?", (tutar, kid))
                    if cid is not None: conn.execute("UPDATE cariler SET bakiye = bakiye - ? WHERE id=?", (tutar, cid))
                
                conn.execute("UPDATE kasa_hareketleri SET kasa_id=?, cari_id=?, tarih=?, tutar=?, tur=?, aciklama=? WHERE id=?", (n_kasa_id, n_cari_id, n_tarih, n_tutar, n_tur, n_aciklama, h_id))
                
                if n_tur == "Giriş":
                    conn.execute("UPDATE kasalar SET bakiye = bakiye + ? WHERE id=?", (n_tutar, n_kasa_id))
                    if n_cari_id is not None: conn.execute("UPDATE cariler SET bakiye = bakiye - ? WHERE id=?", (n_tutar, n_cari_id))
                else:
                    conn.execute("UPDATE kasalar SET bakiye = bakiye - ? WHERE id=?", (n_tutar, n_kasa_id))
                    if n_cari_id is not None: conn.execute("UPDATE cariler SET bakiye = bakiye + ? WHERE id=?", (n_tutar, n_cari_id))
                conn.commit()
                return True
        except sqlite3.Error: return False

    def tum_kasa_hareketleri(self):
        with self._connect() as conn:
            return conn.execute("""
                SELECT kh.id, kb.hesap_adi, ifnull(c.unvan, '-'), kh.tarih, kh.tutar, kh.tur, kh.aciklama 
                FROM kasa_hareketleri kh
                JOIN kasalar kb ON kh.kasa_id = kb.id
                LEFT JOIN cariler c ON kh.cari_id = c.id
                WHERE kh.is_deleted = 0
                ORDER BY kh.id DESC
            """).fetchall()

    # --- BANKA ---
    def tum_bankalari_getir(self):
        with self._connect() as conn:
            return conn.execute("SELECT id, hesap_adi, iban, bakiye FROM bankalar WHERE is_deleted=0").fetchall()

    def banka_ekle(self, hesap_adi, iban):
        try:
            with self._connect() as conn:
                conn.execute("INSERT INTO bankalar (hesap_adi, iban) VALUES (?, ?)", (hesap_adi, iban))
                conn.commit()
                return True
        except sqlite3.Error: return False

    def banka_guncelle(self, banka_id, hesap_adi, iban):
        try:
            with self._connect() as conn:
                conn.execute("UPDATE bankalar SET hesap_adi=?, iban=? WHERE id=?", (hesap_adi, iban, banka_id))
                conn.commit()
                return True
        except sqlite3.Error: return False

    def banka_sil(self, banka_id):
        try:
            with self._connect() as conn:
                conn.execute("UPDATE bankalar SET is_deleted=1 WHERE id=?", (banka_id,))
                conn.commit()
                self.log_tut("bankalar", banka_id, "DELETE", "is_deleted=0", "is_deleted=1")
                return True
        except sqlite3.Error: return False

    def banka_hareketi_ekle(self, banka_id, tutar, tur, aciklama, tarih=None, cari_id=None, proje_kodu=None):
        try:
            with self._connect() as conn:
                if not tarih:
                    tarih = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                conn.execute(
                    "INSERT INTO banka_hareketleri (banka_id, cari_id, tarih, tutar, tur, aciklama, proje_kodu) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (banka_id, cari_id, tarih, tutar, tur, aciklama, proje_kodu)
                )
                if tur == "Giriş":
                    conn.execute("UPDATE bankalar SET bakiye = bakiye + ? WHERE id=?", (tutar, banka_id))
                    if cari_id is not None:
                        conn.execute("UPDATE cariler SET bakiye = bakiye - ? WHERE id=?", (tutar, cari_id))
                else:
                    conn.execute("UPDATE bankalar SET bakiye = bakiye - ? WHERE id=?", (tutar, banka_id))
                    if cari_id is not None:
                        conn.execute("UPDATE cariler SET bakiye = bakiye + ? WHERE id=?", (tutar, cari_id))
                conn.commit()
                return True
        except sqlite3.Error as e: 
            logging.error(f"Banka movement error {e}")
            return False

    def banka_hareket_sil(self, hareket_id):
        try:
            with self._connect() as conn:
                h = conn.execute("SELECT banka_id, tutar, tur, cari_id FROM banka_hareketleri WHERE id=?", (hareket_id,)).fetchone()
                if h:
                    bid, tutar, tur, cid = h
                    if tur == "Giriş":
                        conn.execute("UPDATE bankalar SET bakiye = bakiye - ? WHERE id=?", (tutar, bid))
                        if cid is not None:
                            conn.execute("UPDATE cariler SET bakiye = bakiye + ? WHERE id=?", (tutar, cid))
                    else:
                        conn.execute("UPDATE bankalar SET bakiye = bakiye + ? WHERE id=?", (tutar, bid))
                        if cid is not None:
                            conn.execute("UPDATE cariler SET bakiye = bakiye - ? WHERE id=?", (tutar, cid))
                    conn.execute("DELETE FROM banka_hareketleri WHERE id=?", (hareket_id,))
                    conn.commit()
                    return True
                return False
        except sqlite3.Error: return False

    def banka_hareket_guncelle(self, h_id, n_banka_id, n_tutar, n_tur, n_aciklama, n_tarih, n_cari_id):
        try:
            with self._connect() as conn:
                h = conn.execute("SELECT banka_id, tutar, tur, cari_id FROM banka_hareketleri WHERE id=?", (h_id,)).fetchone()
                if not h: return False
                bid, tutar, tur, cid = h
                if tur == "Giriş":
                    conn.execute("UPDATE bankalar SET bakiye = bakiye - ? WHERE id=?", (tutar, bid))
                    if cid is not None: conn.execute("UPDATE cariler SET bakiye = bakiye + ? WHERE id=?", (tutar, cid))
                else:
                    conn.execute("UPDATE bankalar SET bakiye = bakiye + ? WHERE id=?", (tutar, bid))
                    if cid is not None: conn.execute("UPDATE cariler SET bakiye = bakiye - ? WHERE id=?", (tutar, cid))
                
                conn.execute("UPDATE banka_hareketleri SET banka_id=?, cari_id=?, tarih=?, tutar=?, tur=?, aciklama=? WHERE id=?", (n_banka_id, n_cari_id, n_tarih, n_tutar, n_tur, n_aciklama, h_id))
                
                if n_tur == "Giriş":
                    conn.execute("UPDATE bankalar SET bakiye = bakiye + ? WHERE id=?", (n_tutar, n_banka_id))
                    if n_cari_id is not None: conn.execute("UPDATE cariler SET bakiye = bakiye - ? WHERE id=?", (n_tutar, n_cari_id))
                else:
                    conn.execute("UPDATE bankalar SET bakiye = bakiye - ? WHERE id=?", (n_tutar, n_banka_id))
                    if n_cari_id is not None: conn.execute("UPDATE cariler SET bakiye = bakiye + ? WHERE id=?", (n_tutar, n_cari_id))
                conn.commit()
                return True
        except sqlite3.Error: return False

    def tum_banka_hareketleri(self):
        with self._connect() as conn:
            return conn.execute("""
                SELECT bh.id, b.hesap_adi, ifnull(c.unvan, '-'), bh.tarih, bh.tutar, bh.tur, bh.aciklama 
                FROM banka_hareketleri bh
                JOIN bankalar b ON bh.banka_id = b.id
                LEFT JOIN cariler c ON bh.cari_id = c.id
                WHERE bh.is_deleted = 0
                ORDER BY bh.id DESC
            """).fetchall()

    # --- FATURA ---
    def fatura_olustur(self, fatura_no, cari_id, tur, detaylar, belge_turu='Fatura', fiyat_goster=1, tarih=None, kaynak_id=None, odeme_turu='Veresiye', aciklama="", proje_kodu="", yuvarlama_farki=0.0, tevkifat_turu=""):
        # detaylar = list of (stok_id, miktar, birim_fiyat, kdv_orani, tevkifat_orani, birim)
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                if not tarih:
                    tarih = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # KDVsiz + KDV - Tevkifat + Yuvarlama = Net Tutar (Cari Bakiyeyi bu etkiler)
                toplam_tutar = 0.0
                for d in detaylar:
                    kdvsiz = float(d[1]) * float(d[2])
                    kdv_t = kdvsiz * (float(d[3]) if len(d) > 3 else 0.0) / 100
                    tevk_t = kdvsiz * (float(d[4]) if len(d) > 4 else 0.0) / 100
                    toplam_tutar += (kdvsiz + kdv_t - tevk_t)
                
                toplam_tutar += float(yuvarlama_farki)

                cursor.execute(
                    "INSERT INTO faturalar (fatura_no, cari_id, tarih, toplam_tutar, tur, belge_turu, fiyat_goster, kaynak_id, odeme_turu, aciklama, proje_kodu, yuvarlama_farki, tevkifat_turu) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (fatura_no, cari_id, tarih, toplam_tutar, tur, belge_turu, fiyat_goster, kaynak_id, odeme_turu, aciklama, proje_kodu, yuvarlama_farki, tevkifat_turu)
                )
                fatura_id = cursor.lastrowid
                
                for d in detaylar:
                    stok_id = d[0]
                    miktar = d[1]
                    birim_fiyat = d[2]
                    kdv = d[3] if len(d) > 3 else 0.0
                    tevkifat = d[4] if len(d) > 4 else 0.0
                    birim_str = d[5] if len(d) > 5 else ''
                    cursor.execute(
                        "INSERT INTO fatura_detay (fatura_id, stok_id, miktar, birim_fiyat, kdv_orani, tevkifat_orani, birim) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (fatura_id, stok_id, miktar, birim_fiyat, kdv, tevkifat, birim_str)
                    )
                    
                    # Sipariş stoğu etkilemez. İrsaliye ve Fatura etkiler.
                    if belge_turu in ['İrsaliye', 'Fatura']:
                        artis = miktar if tur == "Alış" else -miktar
                        cursor.execute("UPDATE stoklar SET miktar = miktar + ? WHERE id=?", (artis, stok_id))
                
                # Cari bakiye ve Kasa sadece Fatura ve Nakit ise etkilenir
                if belge_turu == 'Fatura':
                    if odeme_turu == 'Nakit':
                        # Nakit ise cari bakiye etkilenmez (nötr kalır), direkt kasaya girer
                        # Kasa bulalım (Merkez Kasa)
                        kasa = cursor.execute("SELECT id FROM kasalar LIMIT 1").fetchone()
                        if kasa:
                            kid = kasa[0]
                            k_tur = 'Giriş' if tur == 'Satış' else 'Çıkış'
                            cursor.execute("INSERT INTO kasa_hareketleri (kasa_id, cari_id, tarih, tutar, tur, aciklama) VALUES (?, ?, ?, ?, ?, ?)",
                                         (kid, cari_id, tarih, toplam_tutar, k_tur, f"{fatura_no} nolu Nakit Fatura"))
                            if k_tur == 'Giriş':
                                cursor.execute("UPDATE kasalar SET bakiye = bakiye + ? WHERE id=?", (toplam_tutar, kid))
                            else:
                                cursor.execute("UPDATE kasalar SET bakiye = bakiye - ? WHERE id=?", (toplam_tutar, kid))
                    else:
                        # Veresiye ise cari bakiye etkilenir
                        bakiye_etkisi = toplam_tutar if tur == "Satış" else -toplam_tutar
                        cursor.execute("UPDATE cariler SET bakiye = bakiye + ? WHERE id=?", (bakiye_etkisi, cari_id))

                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Fatura hatası: {e}")
            return False

    def evrak_full_getir(self, f_id):
        """Bir evrağın (fatura/irsaliye/sipariş) hem başlık hem detay verilerini döndürür."""
        try:
            f_id = int(f_id) # ID'yi sayıya zorla
            with self._connect() as conn:
                cursor = conn.cursor()
                header = cursor.execute("""
                    SELECT f.*, c.unvan, c.vergi_no, '' as vergi_dairesi, '' as adres
                    FROM faturalar f
                    LEFT JOIN cariler c ON f.cari_id = c.id
                    WHERE f.id=?
                """, (f_id,)).fetchone()
                
                if not header: 
                    print(f"HATA: Evrak başlığı bulunamadı! ID: {f_id}")
                    return None
                
                detaylar = cursor.execute("""
                    SELECT fd.*, s.urun_adi, s.barkod
                    FROM fatura_detay fd
                    LEFT JOIN stoklar s ON fd.stok_id = s.id
                    WHERE fd.fatura_id=?
                """, (f_id,)).fetchall()
                
                return {"header": header, "detaylar": detaylar}
        except Exception as e:
            print(f"evrak_full_getir KRİTİK HATA: {e}")
            logging.error(f"evrak_full_getir hatası: {e}")
            return None

    def fatura_sil(self, fatura_id):
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                # Önce faturayı bulalım
                f = cursor.execute("SELECT cari_id, toplam_tutar, tur FROM faturalar WHERE id=?", (fatura_id,)).fetchone()
                if not f: return False
                cid, tutar, tur = f
                
                # Detayları bulup stokları geri düzeltelim
                detaylar = cursor.execute("SELECT stok_id, miktar FROM fatura_detay WHERE fatura_id=?", (fatura_id,)).fetchall()
                for sid, mik in detaylar:
                    artis = -mik if tur == "Alış" else mik
                    cursor.execute("UPDATE stoklar SET miktar = miktar + ? WHERE id=?", (artis, sid))
                
                # Cari bakiyeyi geri düzeltelim
                bakiye_etkisi = -tutar if tur == "Satış" else tutar
                cursor.execute("UPDATE cariler SET bakiye = bakiye + ? WHERE id=?", (bakiye_etkisi, cid))
                
                # SOFT DELETE
                cursor.execute("UPDATE faturalar SET is_deleted=1 WHERE id=?", (fatura_id,))
                cursor.execute("UPDATE fatura_detay SET is_deleted=1 WHERE fatura_id=?", (fatura_id,))
                
                conn.commit()
                self.log_tut("faturalar", fatura_id, "DELETE")
                return True
        except sqlite3.Error as e:
            logging.error(f"Fatura silme hatası {e}")
            return False

    def fatura_guncelle(self, f_id, fno, cid, tur, detaylar, tarih, belge_turu='Fatura', fiyat_goster=1, odeme_turu='Veresiye', aciklama="", proje_kodu="", yuvarlama_farki=0.0, tevkifat_turu=""):
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                # Önce eski faturayı tamamen geri alalım
                eski = cursor.execute("SELECT cari_id, toplam_tutar, tur, belge_turu, odeme_turu, fatura_no, aciklama FROM faturalar WHERE id=?", (f_id,)).fetchone()
                if not eski: return False
                o_cid, o_tutar, o_tur, o_bturu, o_oturu, o_fno = eski
                
                # 1. Stok Revert
                if o_bturu in ['İrsaliye', 'Fatura']:
                    e_detay = cursor.execute("SELECT stok_id, miktar FROM fatura_detay WHERE fatura_id=?", (f_id,)).fetchall()
                    for sid, mik in e_detay:
                        artis = -mik if o_tur == "Alış" else mik
                        cursor.execute("UPDATE stoklar SET miktar = miktar + ? WHERE id=?", (artis, sid))
                
                # 2. Cari/Kasa Revert
                if o_bturu == 'Fatura':
                    if o_oturu == 'Nakit':
                        k_tur = 'Giriş' if o_tur == 'Satış' else 'Çıkış'
                        if k_tur == 'Giriş':
                             cursor.execute("UPDATE kasalar SET bakiye = bakiye - ? WHERE bakiye >= 0", (o_tutar,))
                        else:
                             cursor.execute("UPDATE kasalar SET bakiye = bakiye + ? WHERE bakiye >= 0", (o_tutar,))
                        cursor.execute("DELETE FROM kasa_hareketleri WHERE aciklama LIKE ?", (f"{o_fno}%",))
                    else:
                        o_b_etki = -o_tutar if o_tur == "Satış" else o_tutar
                        cursor.execute("UPDATE cariler SET bakiye = bakiye + ? WHERE id=?", (o_b_etki, o_cid))
                
                cursor.execute("DELETE FROM fatura_detay WHERE fatura_id=?", (f_id,))

                # 3. Yeni verileri uygula
                toplam_tutar = 0.0
                for d in detaylar:
                    kdvsiz = float(d[1]) * float(d[2])
                    kdv_t = kdvsiz * (float(d[3]) if len(d) > 3 else 0.0) / 100
                    tevk_t = kdvsiz * (float(d[4]) if len(d) > 4 else 0.0) / 100
                    toplam_tutar += (kdvsiz + kdv_t - tevk_t)
                
                toplam_tutar += float(yuvarlama_farki)

                cursor.execute(
                    "UPDATE faturalar SET fatura_no=?, cari_id=?, tarih=?, toplam_tutar=?, tur=?, belge_turu=?, fiyat_goster=?, odeme_turu=?, aciklama=?, proje_kodu=?, yuvarlama_farki=?, tevkifat_turu=? WHERE id=?",
                    (fno, cid, tarih, toplam_tutar, tur, belge_turu, fiyat_goster, odeme_turu, aciklama, proje_kodu, yuvarlama_farki, tevkifat_turu, f_id)
                )
                
                for d in detaylar:
                    sid = d[0]; mik = d[1]; bfiy = d[2]
                    kdv = d[3] if len(d) > 3 else 0.0
                    tevk = d[4] if len(d) > 4 else 0.0
                    birim_str = d[5] if len(d) > 5 else ''
                    cursor.execute("INSERT INTO fatura_detay (fatura_id, stok_id, miktar, birim_fiyat, kdv_orani, tevkifat_orani, birim) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                 (f_id, sid, mik, bfiy, kdv, tevk, birim_str))
                    if belge_turu in ['İrsaliye', 'Fatura']:
                        artis = mik if tur == "Alış" else -mik
                        cursor.execute("UPDATE stoklar SET miktar = miktar + ? WHERE id=?", (artis, sid))
                
                if belge_turu == 'Fatura':
                    if odeme_turu == 'Nakit':
                        kasa = cursor.execute("SELECT id FROM kasalar LIMIT 1").fetchone()
                        if kasa:
                            kid = kasa[0]
                            k_tur = 'Giriş' if tur == 'Satış' else 'Çıkış'
                            cursor.execute("INSERT INTO kasa_hareketleri (kasa_id, cari_id, tarih, tutar, tur, aciklama) VALUES (?, ?, ?, ?, ?, ?)",
                                         (kid, cid, tarih, toplam_tutar, k_tur, f"{fno} nolu Nakit Fatura (G)"))
                            if k_tur == 'Giriş': cursor.execute("UPDATE kasalar SET bakiye = bakiye + ? WHERE id=?", (toplam_tutar, kid))
                            else: cursor.execute("UPDATE kasalar SET bakiye = bakiye - ? WHERE id=?", (toplam_tutar, kid))
                    else:
                        n_b_etki = toplam_tutar if tur == "Satış" else -toplam_tutar
                        cursor.execute("UPDATE cariler SET bakiye = bakiye + ? WHERE id=?", (n_b_etki, cid))

                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Fatura update err {e}")
            return False

    def tum_faturalari_getir(self, belge_turu=None, baslangic=None, bitis=None):
        with self._connect() as conn:
            query = """
                SELECT f.id, f.fatura_no, c.unvan, f.tarih, f.toplam_tutar, f.tur, f.belge_turu, f.odeme_turu, f.aciklama
                FROM faturalar f
                JOIN cariler c ON f.cari_id = c.id
                WHERE f.is_deleted = 0
            """
            params = []
            if belge_turu:
                query += " AND f.belge_turu=?"
                params.append(belge_turu)
            if baslangic:
                query += " AND f.tarih >= ?"
                params.append(baslangic)
            if bitis:
                query += " AND f.tarih <= ?"
                params.append(bitis + " 23:59:59")
                
            return conn.execute(query + " ORDER BY f.id DESC", params).fetchall()

    def evrak_donustur(self, kaynak_id, hedef_turu):
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                k = cursor.execute("SELECT * FROM faturalar WHERE id=?", (kaynak_id,)).fetchone()
                if not k: return False
                
                # Yeni numara
                prefix = 'IRS' if hedef_turu == 'İrsaliye' else 'FAT'
                y_no = f"{prefix}-{int(datetime.now().timestamp())}"
                
                # Detaylar
                detaylar = cursor.execute("SELECT stok_id, miktar, birim_fiyat, kdv_orani, tevkifat_orani, birim FROM fatura_detay WHERE fatura_id=?", (kaynak_id,)).fetchall()
                
                # fatura_olustur'u conn içinde manuel çağıralım veya yeni evrak oluşturalım
                # Basitlik için fatura_olustur mantığını burada çalıştıralım:
                res = self.fatura_olustur(y_no, k[2], k[5], detaylar, belge_turu=hedef_turu, kaynak_id=kaynak_id)
                return res
        except sqlite3.Error: return False

    def gunluk_ozet_getir(self):
        with self._connect() as conn:
            tarih_bugun = datetime.now().strftime("%Y-%m-%d")
            c = conn.cursor()
            
            # Toplam Ciro (Satış Faturaları)
            ciro = c.execute("SELECT SUM(toplam_tutar) FROM faturalar WHERE tur='Satış' AND belge_turu='Fatura' AND tarih LIKE ?", (f"{tarih_bugun}%",)).fetchone()[0] or 0.0
            
            # Toplam Nakit Tahsilat
            nakit = c.execute("SELECT SUM(tutar) FROM kasa_hareketleri WHERE tur='Giriş' AND tarih LIKE ?", (f"{tarih_bugun}%",)).fetchone()[0] or 0.0
            
            # Toplam Veresiye Satış
            veresiye = c.execute("SELECT SUM(toplam_tutar) FROM faturalar WHERE tur='Satış' AND belge_turu='Fatura' AND odeme_turu='Veresiye' AND tarih LIKE ?", (f"{tarih_bugun}%",)).fetchone()[0] or 0.0
            
            return {
                "ciro": ciro,
                "nakit": nakit,
                "veresiye": veresiye
            }

    # --- RAPORLAMA ---
    def genel_durum_getir(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(bakiye) FROM cariler WHERE bakiye > 0")
            alacaklar = cursor.fetchone()[0] or 0.0
            
            cursor.execute("SELECT SUM(bakiye) FROM cariler WHERE bakiye < 0")
            borclar = abs(cursor.fetchone()[0] or 0.0)
            
            cursor.execute("SELECT SUM(bakiye) FROM kasalar")
            kasa_toplam = cursor.fetchone()[0] or 0.0
            
            cursor.execute("SELECT SUM(bakiye) FROM bankalar")
            banka_toplam = cursor.fetchone()[0] or 0.0
            
            nakit = kasa_toplam + banka_toplam
            
            cursor.execute("SELECT SUM(miktar * fiyat) FROM stoklar")
            stok_degeri = cursor.fetchone()[0] or 0.0
            
            return {
                "Alacaklar": alacaklar,
                "Borçlar": borclar,
                "Kasa_Banka": nakit,
                "Stok_Degeri": stok_degeri
            }

    def cari_ekstresi_getir(self, cari_id, baslangic=None, bitis=None):
        """Bir carinin tüm işlem geçmişini döndürür: faturalar + kasa hareketleri + banka hareketleri."""
        with self._connect() as conn:
            c = conn.cursor()
            
            # Fatura hareketleri
            fatura_q = """
                SELECT tarih, fatura_no as aciklama, belge_turu as tur,
                       CASE WHEN tur='Satış' THEN toplam_tutar ELSE 0 END as borc,
                       CASE WHEN tur='Alış' THEN toplam_tutar ELSE 0 END as alacak,
                       toplam_tutar, 'Fatura/Evrak' as kaynak
                FROM faturalar
                WHERE cari_id=? AND belge_turu='Fatura'
            """
            params = [cari_id]
            if baslangic:
                fatura_q += " AND tarih >= ?"
                params.append(baslangic)
            if bitis:
                fatura_q += " AND tarih <= ?"
                params.append(bitis + " 23:59:59")
            
            faturalar = c.execute(fatura_q, params).fetchall()
            
            # Kasa hareketleri
            kasa_q = """
                SELECT kh.tarih, kh.aciklama, kh.tur,
                       CASE WHEN kh.tur='Çıkış' THEN kh.tutar ELSE 0 END as borc,
                       CASE WHEN kh.tur='Giriş' THEN kh.tutar ELSE 0 END as alacak,
                       kh.tutar, 'Kasa' as kaynak
                FROM kasa_hareketleri kh
                WHERE kh.cari_id=?
            """
            kasa_params = [cari_id]
            if baslangic:
                kasa_q += " AND kh.tarih >= ?"
                kasa_params.append(baslangic)
            if bitis:
                kasa_q += " AND kh.tarih <= ?"
                kasa_params.append(bitis + " 23:59:59")
            
            kasa_h = c.execute(kasa_q, kasa_params).fetchall()
            
            # Banka hareketleri
            banka_q = """
                SELECT bh.tarih, bh.aciklama, bh.tur,
                       CASE WHEN bh.tur='Çıkış' THEN bh.tutar ELSE 0 END as borc,
                       CASE WHEN bh.tur='Giriş' THEN bh.tutar ELSE 0 END as alacak,
                       bh.tutar, 'Banka' as kaynak
                FROM banka_hareketleri bh
                WHERE bh.cari_id=?
            """
            banka_params = [cari_id]
            if baslangic:
                banka_q += " AND bh.tarih >= ?"
                banka_params.append(baslangic)
            if bitis:
                banka_q += " AND bh.tarih <= ?"
                banka_params.append(bitis + " 23:59:59")
            
            banka_h = c.execute(banka_q, banka_params).fetchall()
            
            tum_hareketler = list(faturalar) + list(kasa_h) + list(banka_h)
            tum_hareketler.sort(key=lambda x: str(x[0]))
            return tum_hareketler

    def kdv_ozet_getir(self, baslangic=None, bitis=None):
        """KDV bazlı özet rapor döndürür."""
        with self._connect() as conn:
            q = """
                SELECT 
                    SUM(fd.miktar * fd.birim_fiyat) as kdvsiz_tutar,
                    SUM(fd.miktar * fd.birim_fiyat * COALESCE(fd.kdv_orani,0) / 100) as kdv_tutari,
                    SUM(fd.miktar * fd.birim_fiyat * COALESCE(fd.tevkifat_orani,0) / 100) as tevkifat_tutari,
                    f.tur
                FROM fatura_detay fd
                JOIN faturalar f ON fd.fatura_id = f.id
                WHERE f.belge_turu = 'Fatura' AND f.is_deleted = 0
            """
            params = []
            if baslangic:
                q += " AND f.tarih >= ?"
                params.append(baslangic)
            if bitis:
                q += " AND f.tarih <= ?"
                params.append(bitis + " 23:59:59")
            q += " GROUP BY f.tur"
            return conn.execute(q, params).fetchall()

    # --- YENİ MODÜL METODLARI ---

    # 1. Cari Notlar
    def cari_not_getir(self, cari_id):
        with self._connect() as conn:
            return conn.execute("SELECT not_icerik FROM cari_notlar WHERE cari_id=? AND is_deleted=0", (cari_id,)).fetchone()

    def cari_not_kaydet(self, cari_id, icerik):
        tarih = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._connect() as conn:
            conn.execute("INSERT OR REPLACE INTO cari_notlar (id, cari_id, not_icerik, guncelleme_tarihi) VALUES ((SELECT id FROM cari_notlar WHERE cari_id=?), ?, ?, ?)",
                         (cari_id, cari_id, icerik, tarih))
            conn.commit()
            return True

    # 2. Takvim
    def etkinlik_ekle(self, baslik, aciklama, tarih, saat, oncelik='Normal'):
        with self._connect() as conn:
            conn.execute("INSERT INTO takvim_etkinlikleri (baslik, aciklama, tarih, saat, oncelik) VALUES (?, ?, ?, ?, ?)",
                         (baslik, aciklama, tarih, saat, oncelik))
            conn.commit()
            return True

    def etkinlikleri_getir(self, tarih=None):
        with self._connect() as conn:
            if tarih:
                return conn.execute("SELECT id, baslik, aciklama, tarih, saat, oncelik FROM takvim_etkinlikleri WHERE tarih=? AND is_deleted=0", (tarih,)).fetchall()
            return conn.execute("SELECT id, baslik, aciklama, tarih, saat, oncelik FROM takvim_etkinlikleri WHERE is_deleted=0 ORDER BY tarih ASC").fetchall()

    def etkinlik_sil(self, e_id):
        with self._connect() as conn:
            conn.execute("UPDATE takvim_etkinlikleri SET is_deleted=1 WHERE id=?", (e_id,))
            conn.commit()
            return True

    # 3. Personel (Çalışan)
    def calisan_ekle(self, ad_soyad, kategori, ise_giris, maas, tel):
        try:
            with self._connect() as conn:
                conn.execute("INSERT INTO calisanlar (ad_soyad, kategori, ise_giris, aylik_maas, telefon) VALUES (?, ?, ?, ?, ?)",
                             (ad_soyad, kategori, ise_giris, maas, tel))
                conn.commit()
                return True
        except sqlite3.Error: return False

    def calisani_guncelle(self, id, ad_soyad, kategori, ise_giris, isten_cikis, maas, tel):
        try:
            with self._connect() as conn:
                conn.execute("UPDATE calisanlar SET ad_soyad=?, kategori=?, ise_giris=?, isten_cikis=?, aylik_maas=?, telefon=? WHERE id=?",
                             (ad_soyad, kategori, ise_giris, isten_cikis, maas, tel, id))
                conn.commit()
                return True
        except sqlite3.Error: return False

    def tum_calisanlari_getir(self):
        with self._connect() as conn:
            return conn.execute("SELECT * FROM calisanlar WHERE is_deleted=0").fetchall()

    def calisan_sil(self, id):
        with self._connect() as conn:
            conn.execute("UPDATE calisanlar SET is_deleted=1 WHERE id=?", (id,))
            conn.commit()
            return True

    def personel_hareketi_ekle(self, p_id, tutar, tur, aciklama, tarih=None):
        if not tarih: tarih = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self._connect() as conn:
                conn.execute("INSERT INTO personel_hareketleri (personel_id, tarih, tutar, tur, aciklama) VALUES (?, ?, ?, ?, ?)",
                             (p_id, tarih, tutar, tur, aciklama))
                # Bakiye Güncelle: Maaş Tahakkuku bakiyeyi artırır (şirketin personele borcu artırır), Ödeme/Avans azaltır.
                etki = tutar if tur == 'Maaş Tahakkuku' else -tutar
                conn.execute("UPDATE calisanlar SET bakiye = bakiye + ? WHERE id=?", (etki, p_id))
                conn.commit()
                return True
        except sqlite3.Error: return False

    def personel_hareketleri_getir(self, p_id):
        with self._connect() as conn:
            return conn.execute("SELECT id, tarih, tutar, tur, aciklama FROM personel_hareketleri WHERE personel_id=? AND is_deleted=0 ORDER BY tarih DESC", (p_id,)).fetchall()
