import customtkinter as ctk  # pip install customtkinter
import tkinter as tk
from tkinter import ttk
import sqlite3
from tkinter import messagebox
from tkinter import filedialog
from datetime import datetime, timedelta
import os

# --- AYARLAR ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

DB_NAME = "dershane_pro_v2.db"  # Yeni veritabanı adı (yapı değiştiği için)

# Excel Kontrolü
try:
    from openpyxl import Workbook
    OPENPYXL_YUKLU = True
except ImportError:
    OPENPYXL_YUKLU = False
    print("UYARI: 'openpyxl' yok. Raporlama çalışmaz.")

# ====================================================================
# ANA UYGULAMA (CONTROLLER)
# ====================================================================
class DershaneApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Dershane Yönetim Sistemi Pro - Tam Otomasyon")
        self.geometry("1300x850")
        
        self.veritabani_baslat()
        self.tablo_stili_ayarla()

        # Ana Konteyner
        container = ctk.CTkFrame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        # Sayfa Listesi (Yeni Sayfalar Eklendi)
        sayfalar = (AnaMenu, OgretmenSayfasi, OgrenciSayfasi, EtutPlanlamaSayfasi, TalepSayfasi, CezaSayfasi)

        for F in sayfalar:
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(AnaMenu)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()
        if hasattr(frame, "verileri_tazele"):
            frame.verileri_tazele()

    def tablo_stili_ayarla(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", rowheight=30, borderwidth=0, font=("Arial", 11))
        style.map('Treeview', background=[('selected', '#1f538d')])
        style.configure("Treeview.Heading", background="#1f538d", foreground="white", relief="flat", font=("Arial", 12, "bold"))
        style.map("Treeview.Heading", background=[('active', '#14375e')])

    def veritabani_baslat(self):
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        
        # Öğretmenler (Tatil Günü Eklendi)
        cur.execute("""CREATE TABLE IF NOT EXISTS Ogretmenler (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    ad TEXT, soyad TEXT, brans TEXT, 
                    tatil_gunu TEXT)""")
        
        # Öğrenciler (Ceza Durumu Eklendi: 0=Temiz, 1=Cezalı)
        cur.execute("""CREATE TABLE IF NOT EXISTS Ogrenciler (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    ad TEXT, soyad TEXT, sinif TEXT, numara TEXT UNIQUE,
                    ceza_durumu INTEGER DEFAULT 0, 
                    ceza_notu TEXT)""")
        
        # Etütler
        cur.execute("""CREATE TABLE IF NOT EXISTS Etutler (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, ogretmen_id INTEGER, ogrenci_id INTEGER, 
                    ders_adi TEXT, tarih TEXT, saat TEXT, bitis_saati TEXT, 
                    katilim_durumu TEXT DEFAULT 'Planlandı',
                    FOREIGN KEY(ogretmen_id) REFERENCES Ogretmenler(id),
                    FOREIGN KEY(ogrenci_id) REFERENCES Ogrenciler(id))""")
        
        # Talepler (Yeni Tablo)
        cur.execute("""CREATE TABLE IF NOT EXISTS Talepler (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, ogrenci_id INTEGER, ogretmen_id INTEGER,
                    tarih TEXT, saat_araligi TEXT, durum TEXT DEFAULT 'Bekliyor',
                    FOREIGN KEY(ogretmen_id) REFERENCES Ogretmenler(id),
                    FOREIGN KEY(ogrenci_id) REFERENCES Ogrenciler(id))""")
        
        conn.commit()
        conn.close()


# ====================================================================
# 1. ANA MENÜ
# ====================================================================
class AnaMenu(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        ctk.CTkLabel(self, text="DERSHANE OTOMASYONU", font=("Roboto Medium", 36)).pack(pady=(50, 30))
        
        grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        grid_frame.pack()
        
        conf = {"width": 220, "height": 70, "font": ("Roboto", 15, "bold"), "corner_radius": 12}

        # Satır 1
        ctk.CTkButton(grid_frame, text="ÖĞRETMEN\n(Tatil Günleri)", command=lambda: controller.show_frame(OgretmenSayfasi), **conf).grid(row=0, column=0, padx=15, pady=15)
        ctk.CTkButton(grid_frame, text="ÖĞRENCİ\n(Kayıt & Ceza)", command=lambda: controller.show_frame(OgrenciSayfasi), **conf).grid(row=0, column=1, padx=15, pady=15)
        
        # Satır 2
        ctk.CTkButton(grid_frame, text="ETÜT PLANLAMA\n(Sadece Pazartesi)", fg_color="#1f6aa5", command=lambda: controller.show_frame(EtutPlanlamaSayfasi), **conf).grid(row=1, column=0, padx=15, pady=15)
        ctk.CTkButton(grid_frame, text="BEKLEYEN\nTALEPLER", fg_color="#8E44AD", command=lambda: controller.show_frame(TalepSayfasi), **conf).grid(row=1, column=1, padx=15, pady=15)

        # Satır 3 (Ceza & Rapor)
        ctk.CTkButton(grid_frame, text="CEZA & DEVAMSIZLIK\nKONTROLÜ", fg_color="#C0392B", command=lambda: controller.show_frame(CezaSayfasi), **conf).grid(row=2, column=0, padx=15, pady=15)
        ctk.CTkButton(grid_frame, text="ÇIKIŞ", fg_color="gray", command=parent.quit, **conf).grid(row=2, column=1, padx=15, pady=15)


# ====================================================================
# 2. ÖĞRETMEN SAYFASI (Tatil Günü Ekli)
# ====================================================================
class OgretmenSayfasi(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.ust_bar_olustur(controller, "ÖĞRETMEN YÖNETİMİ")
        
        form = ctk.CTkFrame(self); form.pack(padx=20, pady=10, fill="x")
        self.ad = self.mk_ent(form, "Ad:", 0, 0); self.soyad = self.mk_ent(form, "Soyad:", 0, 2); self.brans = self.mk_ent(form, "Branş:", 0, 4)
        
        ctk.CTkLabel(form, text="Tatil Günü:").grid(row=0, column=6, padx=5)
        self.cb_tatil = ctk.CTkComboBox(form, values=["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar", "YOK"])
        self.cb_tatil.grid(row=0, column=7, padx=5)
        self.cb_tatil.set("YOK")

        ctk.CTkButton(form, text="KAYDET", fg_color="green", command=self.kaydet).grid(row=0, column=8, padx=20)
        
        self.tree = ttk.Treeview(self, columns=('id', 'ad', 'soyad', 'brans', 'tatil'), show='headings', height=12)
        for c in ('id', 'ad', 'soyad', 'brans', 'tatil'): self.tree.heading(c, text=c.upper())
        self.tree.column('id', width=40); self.tree.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkButton(self, text="SEÇİLİ ÖĞRETMENİ SİL", fg_color="red", command=self.sil).pack(pady=10)

    def ust_bar_olustur(self, controller, baslik):
        top = ctk.CTkFrame(self, height=50, corner_radius=0, fg_color=("gray85", "gray20")); top.pack(side="top", fill="x")
        ctk.CTkButton(top, text="< GERİ", width=80, fg_color="transparent", border_width=2, text_color=("black", "white"), command=lambda: controller.show_frame(AnaMenu)).pack(side="left", padx=10, pady=10)
        ctk.CTkLabel(top, text=baslik, font=("Roboto", 20, "bold")).pack(side="left", padx=20)

    def mk_ent(self, p, t, r, c):
        ctk.CTkLabel(p, text=t).grid(row=r, column=c, padx=5); e=ctk.CTkEntry(p, width=120); e.grid(row=r, column=c+1, padx=5); return e

    def verileri_tazele(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = sqlite3.connect(DB_NAME); cur = conn.cursor(); cur.execute("SELECT * FROM Ogretmenler")
        for r in cur.fetchall(): self.tree.insert("", "end", values=r)
        conn.close()

    def kaydet(self):
        v = (self.ad.get(), self.soyad.get(), self.brans.get(), self.cb_tatil.get())
        if all(v[:3]):
            conn = sqlite3.connect(DB_NAME); conn.execute("INSERT INTO Ogretmenler (ad, soyad, brans, tatil_gunu) VALUES (?,?,?,?)", v); conn.commit(); conn.close()
            self.verileri_tazele(); messagebox.showinfo("Başarılı", "Öğretmen eklendi.")
        else: messagebox.showwarning("Hata", "Eksik bilgi")

    def sil(self):
        s = self.tree.focus()
        if s and messagebox.askyesno("Sil", "Silinsin mi?"):
            conn = sqlite3.connect(DB_NAME); conn.execute("DELETE FROM Ogretmenler WHERE id=?", (self.tree.item(s,'values')[0],)); conn.commit(); conn.close(); self.verileri_tazele()


# ====================================================================
# 3. ÖĞRENCİ SAYFASI (Ceza/Disiplin Eklendi)
# ====================================================================
class OgrenciSayfasi(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.ust_bar_olustur(controller, "ÖĞRENCİ YÖNETİMİ")
        
        form = ctk.CTkFrame(self); form.pack(padx=20, pady=10, fill="x")
        self.ad = self.mk_ent(form, "Ad:", 0, 0); self.soyad = self.mk_ent(form, "Soyad:", 0, 2)
        self.sinif = self.mk_ent(form, "Sınıf:", 0, 4); self.no = self.mk_ent(form, "No:", 0, 6)
        ctk.CTkButton(form, text="KAYDET", fg_color="green", command=self.kaydet).grid(row=0, column=8, padx=20)

        self.tree = ttk.Treeview(self, columns=('id', 'ad', 'soyad', 'sinif', 'num', 'ceza'), show='headings', height=12)
        for c in ('id', 'ad', 'soyad', 'sinif', 'num', 'ceza'): self.tree.heading(c, text=c.upper())
        self.tree.column('id', width=40); self.tree.column('ceza', width=60); self.tree.pack(fill="both", expand=True, padx=20, pady=10)
        
        bf = ctk.CTkFrame(self, fg_color="transparent"); bf.pack(pady=10)
        ctk.CTkButton(bf, text="SİL", fg_color="red", command=self.sil).pack(side="left", padx=10)
        ctk.CTkButton(bf, text="CEZA DURUMU DEĞİŞTİR (Banla/Kaldır)", fg_color="orange", width=250, command=self.ceza_degistir).pack(side="left", padx=10)

    def ust_bar_olustur(self, controller, baslik):
        top = ctk.CTkFrame(self, height=50, corner_radius=0, fg_color=("gray85", "gray20")); top.pack(side="top", fill="x")
        ctk.CTkButton(top, text="< GERİ", width=80, fg_color="transparent", border_width=2, text_color=("black", "white"), command=lambda: controller.show_frame(AnaMenu)).pack(side="left", padx=10, pady=10)
        ctk.CTkLabel(top, text=baslik, font=("Roboto", 20, "bold")).pack(side="left", padx=20)
    def mk_ent(self, p, t, r, c):
        ctk.CTkLabel(p, text=t).grid(row=r, column=c, padx=5); e=ctk.CTkEntry(p, width=120); e.grid(row=r, column=c+1, padx=5); return e

    def verileri_tazele(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = sqlite3.connect(DB_NAME); cur = conn.cursor(); cur.execute("SELECT id, ad, soyad, sinif, numara, CASE WHEN ceza_durumu=1 THEN 'CEZALI' ELSE 'TEMİZ' END FROM Ogrenciler")
        for r in cur.fetchall(): 
            # Cezalıları kırmızı yapabiliriz (tag ile), şimdilik metin yeterli
            self.tree.insert("", "end", values=r)
        conn.close()

    def kaydet(self):
        v = (self.ad.get(), self.soyad.get(), self.sinif.get(), self.no.get())
        if all(v):
            try:
                conn = sqlite3.connect(DB_NAME); conn.execute("INSERT INTO Ogrenciler (ad, soyad, sinif, numara, ceza_durumu) VALUES (?,?,?,?,0)", v); conn.commit(); conn.close()
                messagebox.showinfo("Tamam", "Eklendi"); self.verileri_tazele()
                self.ad.delete(0,"end"); self.soyad.delete(0,"end"); self.sinif.delete(0,"end"); self.no.delete(0,"end")
            except: messagebox.showerror("Hata", "Numara kayıtlı")
        else: messagebox.showwarning("Hata", "Eksik")

    def sil(self):
        s = self.tree.focus()
        if s and messagebox.askyesno("Sil", "Silinsin mi?"):
            conn = sqlite3.connect(DB_NAME); conn.execute("DELETE FROM Ogrenciler WHERE id=?", (self.tree.item(s,'values')[0],)); conn.commit(); conn.close(); self.verileri_tazele()

    def ceza_degistir(self):
        s = self.tree.focus()
        if not s: return
        data = self.tree.item(s, 'values')
        oid = data[0]
        yeni_durum = 0 if data[5] == "CEZALI" else 1
        mesaj = "Cezayı Kaldır?" if yeni_durum == 0 else "Öğrenciyi Banla/Cezalandır?"
        
        if messagebox.askyesno("Ceza İşlemi", mesaj):
            conn = sqlite3.connect(DB_NAME)
            conn.execute("UPDATE Ogrenciler SET ceza_durumu=? WHERE id=?", (yeni_durum, oid))
            conn.commit(); conn.close(); self.verileri_tazele()


# ====================================================================
# 4. ETÜT PLANLAMA (Gelişmiş: 09-22, Pazartesi Kuralı, Branş Limiti)
# ====================================================================
class EtutPlanlamaSayfasi(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.ust_bar_olustur(controller, "ETÜT PLANLAMA (Sadece Pazartesi)")
        
        self.secili_tarih_str = ""
        self.ogretmen_map = {}

        # Tarih Seçimi
        f = ctk.CTkFrame(self); f.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(f, text="Tarih (GG.AA.YYYY):").pack(side="left", padx=10)
        self.ent_tarih = ctk.CTkEntry(f, placeholder_text="25.11.2025"); self.ent_tarih.pack(side="left", padx=10)
        ctk.CTkButton(f, text="GÜNÜ YÜKLE", command=self.gunu_yukle).pack(side="left", padx=10)

        # Zaman Çizelgesi (Scrollable)
        self.scroll = ctk.CTkScrollableFrame(self, label_text="Zaman Dilimleri (09:00 - 22:00)"); self.scroll.pack(fill="both", expand=True, padx=20, pady=10)

    def ust_bar_olustur(self, controller, baslik):
        top = ctk.CTkFrame(self, height=50, corner_radius=0, fg_color=("gray85", "gray20")); top.pack(side="top", fill="x")
        ctk.CTkButton(top, text="< GERİ", width=80, fg_color="transparent", border_width=2, text_color=("black", "white"), command=lambda: controller.show_frame(AnaMenu)).pack(side="left", padx=10, pady=10)
        ctk.CTkLabel(top, text=baslik, font=("Roboto", 20, "bold")).pack(side="left", padx=20)

    def verileri_tazele(self):
        # Varsayılan olarak gelecek ilk Pazartesiyi bulup yazabiliriz ama şimdilik boş kalsın
        pass

    def gunu_yukle(self):
        tarih = self.ent_tarih.get()
        try:
            dt = datetime.strptime(tarih, "%d.%m.%Y")
            if dt.weekday() != 0: # 0 = Pazartesi
                messagebox.showerror("Kural Hatası", "Sadece PAZARTESİ günlerine etüt verilebilir!")
                return
            self.secili_tarih_str = tarih
            self.slots_olustur()
        except ValueError:
            messagebox.showerror("Format", "Tarih formatı: GG.AA.YYYY olmalı")

    def slots_olustur(self):
        for w in self.scroll.winfo_children(): w.destroy()
        
        # 09:00'dan 22:00'ye kadar döngü
        baslangic = datetime.strptime("09:00", "%H:%M")
        bitis_siniri = datetime.strptime("22:00", "%H:%M")
        
        while baslangic < bitis_siniri:
            saat_str = baslangic.strftime("%H:%M")
            bitis_dt = baslangic + timedelta(minutes=50)
            bitis_str = bitis_dt.strftime("%H:%M")
            
            # Slot Kartı
            f = ctk.CTkFrame(self.scroll, fg_color="#333"); f.pack(fill="x", pady=5, padx=10)
            ctk.CTkLabel(f, text=f"{saat_str} - {bitis_str}", font=("Roboto", 16, "bold"), width=120).pack(side="left", padx=10)
            
            # O saatteki doluluk durumunu çekelim mi? (Burada genel bir buton koyacağız, tıklayınca hoca seçecek)
            # Basitleştirmek için: "Bu Saate Etüt Ekle" butonu
            ctk.CTkButton(f, text="ETÜT AYARLA / TALEP OLUŞTUR", height=40, 
                          command=lambda s=saat_str, b=bitis_str: self.etut_popup_ac(s, b)).pack(side="left", fill="x", expand=True, padx=10)

            # 1 saat ileri (50 dk ders + 10 dk teneffüs)
            baslangic += timedelta(minutes=60)

    def etut_popup_ac(self, saat, bitis_saati):
        # Popup Aç
        pop = ctk.CTkToplevel(self)
        pop.title(f"Etüt Ekle: {self.secili_tarih_str} | {saat}")
        pop.geometry("450x500")
        pop.grab_set()

        conn = sqlite3.connect(DB_NAME); cur = conn.cursor()
        
        # Öğretmenler (Ad, Soyad, Branş, Tatil Günü)
        hoca_map = {}; hoca_list = []
        cur.execute("SELECT id, ad, soyad, brans, tatil_gunu FROM Ogretmenler")
        for r in cur.fetchall():
            txt = f"{r[1]} {r[2]} ({r[3]})"
            # Eğer tatil günü "Pazartesi" ise listeye ekleme veya işaretle (Burada ekleyelim ama kontrol koyalım)
            hoca_map[txt] = {'id': r[0], 'brans': r[3], 'tatil': r[4]}
            hoca_list.append(txt)
        
        # Öğrenciler (Cezalılar Hariç mi? Kontrolü kayıtta yapalım)
        ogr_map = {}; ogr_list = []
        cur.execute("SELECT id, ad, soyad, numara, ceza_durumu FROM Ogrenciler")
        for r in cur.fetchall():
            durum = " (CEZALI)" if r[4] == 1 else ""
            txt = f"{r[1]} {r[2]} ({r[3]}){durum}"
            ogr_map[txt] = {'id': r[0], 'ceza': r[4]}
            ogr_list.append(txt)
        conn.close()

        ctk.CTkLabel(pop, text="Öğretmen Seç:").pack(pady=5)
        cb_hoca = ctk.CTkComboBox(pop, values=hoca_list, width=300); cb_hoca.pack()

        ctk.CTkLabel(pop, text="Öğrenci Seç:").pack(pady=5)
        cb_ogr = ctk.CTkComboBox(pop, values=ogr_list, width=300); cb_ogr.pack()

        ctk.CTkLabel(pop, text="Konu:").pack(pady=5)
        ent_ders = ctk.CTkEntry(pop, width=300); ent_ders.pack()

        def islem_yap():
            hoca_txt = cb_hoca.get()
            ogr_txt = cb_ogr.get()
            
            if not (hoca_txt and ogr_txt): messagebox.showwarning("Eksik", "Seçim yapın"); return
            
            hoca_data = hoca_map[hoca_txt]
            ogr_data = ogr_map[ogr_txt]
            
            # 1. CEZA KONTROLÜ
            if ogr_data['ceza'] == 1:
                messagebox.showerror("Yasak", "Bu öğrenci CEZALI! Etüt alamaz."); return

            # 2. TATİL GÜNÜ KONTROLÜ
            if hoca_data['tatil'] == "Pazartesi":
                # Bu biraz paradoks çünkü sistem sadece Pazartesi çalışıyor :)
                # Ama hoca "Pazartesi tatil" dediyse o gün derse gelemez.
                messagebox.showerror("Hata", "Bu hocanın tatil günü Pazartesi!"); return

            conn = sqlite3.connect(DB_NAME); cur = conn.cursor()

            # 3. HOCA DOLULUK KONTROLÜ (Aynı saatte başka etüdü var mı?)
            cur.execute("SELECT count(*) FROM Etutler WHERE ogretmen_id=? AND tarih=? AND saat=?", 
                        (hoca_data['id'], self.secili_tarih_str, saat))
            if cur.fetchone()[0] > 0:
                # HOCA DOLU! -> TALEP OLUŞTURMA TEKLİFİ
                if messagebox.askyesno("Hoca Dolu", "Seçilen saatte hoca dolu.\n\nBekleme listesine (TALEP) eklemek ister misiniz?"):
                    cur.execute("INSERT INTO Talepler (ogrenci_id, ogretmen_id, tarih, saat_araligi) VALUES (?,?,?,?)",
                                (ogr_data['id'], hoca_data['id'], self.secili_tarih_str, f"{saat}-{bitis_saati}"))
                    conn.commit(); conn.close(); pop.destroy()
                    messagebox.showinfo("Talep", "Öğrenci talep listesine eklendi.")
                else:
                    conn.close()
                return

            # 4. BRANŞ LİMİTİ (Öğrenci aynı branştan tamamlanmamış etüdü var mı?)
            # Branşı bul: hoca_data['brans']
            # Öğrencinin bu branştaki 'Planlandı' durumundaki etütlerini say
            cur.execute("""SELECT count(*) FROM Etutler E
                           JOIN Ogretmenler O ON E.ogretmen_id = O.id
                           WHERE E.ogrenci_id=? AND O.brans=? AND E.katilim_durumu='Planlandı'""", 
                           (ogr_data['id'], hoca_data['brans']))
            aktif_brans_sayisi = cur.fetchone()[0]
            
            if aktif_brans_sayisi > 0:
                messagebox.showerror("Branş Limiti", f"Öğrencinin '{hoca_data['brans']}' branşından zaten aktif bir etüdü var.\nÖnce onu tamamlamalı.")
                conn.close(); return

            # KAYIT
            cur.execute("INSERT INTO Etutler (ogretmen_id, ogrenci_id, ders_adi, tarih, saat, bitis_saati, sure) VALUES (?,?,?,?,?,?,?)",
                        (hoca_data['id'], ogr_data['id'], ent_ders.get(), self.secili_tarih_str, saat, bitis_saati, 50))
            conn.commit(); conn.close()
            messagebox.showinfo("Başarılı", "Etüt eklendi."); pop.destroy()

        ctk.CTkButton(pop, text="KAYDET / TALEP OLUŞTUR", fg_color="green", height=50, command=islem_yap).pack(pady=20, fill="x", padx=20)


# ====================================================================
# 5. TALEP SAYFASI (Bekleyen İstekler)
# ====================================================================
class TalepSayfasi(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.ust_bar_olustur(controller, "BEKLEYEN TALEPLER")
        
        self.tree = ttk.Treeview(self, columns=('id', 'ogr', 'hoca', 'tar', 'saat', 'durum'), show='headings', height=20)
        for c in ('id', 'ogr', 'hoca', 'tar', 'saat', 'durum'): self.tree.heading(c, text=c.upper())
        self.tree.column('id', width=40); self.tree.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkButton(self, text="TALEBİ SİL / ÇÖZÜLDÜ", fg_color="orange", command=self.sil).pack(pady=10)

    def ust_bar_olustur(self, controller, baslik):
        top = ctk.CTkFrame(self, height=50, corner_radius=0, fg_color=("gray85", "gray20")); top.pack(side="top", fill="x")
        ctk.CTkButton(top, text="< GERİ", width=80, fg_color="transparent", border_width=2, text_color=("black", "white"), command=lambda: controller.show_frame(AnaMenu)).pack(side="left", padx=10, pady=10)
        ctk.CTkLabel(top, text=baslik, font=("Roboto", 20, "bold")).pack(side="left", padx=20)

    def verileri_tazele(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = sqlite3.connect(DB_NAME); cur = conn.cursor()
        cur.execute("""SELECT T.id, Og.ad||' '||Og.soyad, O.ad||' '||O.soyad, T.tarih, T.saat_araligi, T.durum
                       FROM Talepler T
                       LEFT JOIN Ogrenciler Og ON T.ogrenci_id = Og.id
                       LEFT JOIN Ogretmenler O ON T.ogretmen_id = O.id""")
        for r in cur.fetchall(): self.tree.insert("", "end", values=r)
        conn.close()

    def sil(self):
        s = self.tree.focus()
        if s:
            conn = sqlite3.connect(DB_NAME); conn.execute("DELETE FROM Talepler WHERE id=?", (self.tree.item(s,'values')[0],)); conn.commit(); conn.close(); self.verileri_tazele()


# ====================================================================
# 6. CEZA & DEVAMSIZLIK SAYFASI
# ====================================================================
class CezaSayfasi(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.ust_bar_olustur(controller, "CEZA & DEVAMSIZLIK YÖNETİMİ")
        
        # 1. Otomatik Tespit
        f1 = ctk.CTkFrame(self); f1.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(f1, text="OTOMATİK SİSTEM: Geçmiş tarihte olup 'Planlandı' (Girilmeyen) veya 'Gelmedi' olanları bulur.").pack(pady=5)
        ctk.CTkButton(f1, text="DEVAMSIZLARI TESPİT ET VE CEZALANDIR", fg_color="red", height=50, command=self.otomatik_ceza).pack(fill="x", padx=20, pady=10)

        # 2. Cezalı Listesi
        ctk.CTkLabel(self, text="ŞU AN CEZALI OLAN ÖĞRENCİLER", font=("Roboto", 16, "bold")).pack(pady=10)
        self.tree = ttk.Treeview(self, columns=('id', 'ad', 'soyad', 'no', 'not'), show='headings', height=10)
        for c in ('id', 'ad', 'soyad', 'no', 'not'): self.tree.heading(c, text=c.upper())
        self.tree.pack(fill="both", expand=True, padx=20)
        
        ctk.CTkButton(self, text="SEÇİLİ ÖĞRENCİNİN CEZASINI KALDIR", fg_color="green", command=self.ceza_kaldir).pack(pady=10)

    def ust_bar_olustur(self, controller, baslik):
        top = ctk.CTkFrame(self, height=50, corner_radius=0, fg_color=("gray85", "gray20")); top.pack(side="top", fill="x")
        ctk.CTkButton(top, text="< GERİ", width=80, fg_color="transparent", border_width=2, text_color=("black", "white"), command=lambda: controller.show_frame(AnaMenu)).pack(side="left", padx=10, pady=10)
        ctk.CTkLabel(top, text=baslik, font=("Roboto", 20, "bold")).pack(side="left", padx=20)

    def verileri_tazele(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = sqlite3.connect(DB_NAME); cur = conn.cursor()
        # Sadece cezalıları getir
        cur.execute("SELECT id, ad, soyad, numara, ceza_notu FROM Ogrenciler WHERE ceza_durumu=1")
        for r in cur.fetchall(): self.tree.insert("", "end", values=r)
        conn.close()

    def otomatik_ceza(self):
        if not messagebox.askyesno("Onay", "Geçmiş tarihli 'Gelmedi' veya girilmemiş etütleri olan öğrencileri CEZALI duruma getirecek. Onaylıyor musunuz?"): return
        
        bugun_str = datetime.now().strftime("%d.%m.%Y")
        # Basit mantık: Tarih string karşılaştırması sqlite'da zordur, Python'da çekip kontrol edeceğiz
        conn = sqlite3.connect(DB_NAME); cur = conn.cursor()
        cur.execute("SELECT id, ogrenci_id, tarih, katilim_durumu FROM Etutler")
        tum_etutler = cur.fetchall()
        
        ceza_sayisi = 0
        for eid, oid, tar, durum in tum_etutler:
            try:
                etut_tarih = datetime.strptime(tar, "%d.%m.%Y")
                bugun_tarih = datetime.now()
                
                # Etüt tarihi geçmişse VE (Durum 'Gelmedi' İSE veya Durum hala 'Planlandı' ise)
                if etut_tarih < bugun_tarih:
                    if durum == "Gelmedi" or durum == "Planlandı":
                        # Öğrenciyi cezalandır
                        cur.execute("UPDATE Ogrenciler SET ceza_durumu=1, ceza_notu='Devamsızlık' WHERE id=?", (oid,))
                        ceza_sayisi += 1
            except: pass
        
        conn.commit(); conn.close()
        messagebox.showinfo("İşlem Tamam", f"Tarama bitti. {ceza_sayisi} adet devamsızlık işlemi işlendi (Mükerrer olabilir).")
        self.verileri_tazele()

    def ceza_kaldir(self):
        s = self.tree.focus()
        if s:
            oid = self.tree.item(s, 'values')[0]
            conn = sqlite3.connect(DB_NAME)
            conn.execute("UPDATE Ogrenciler SET ceza_durumu=0, ceza_notu='' WHERE id=?", (oid,))
            conn.commit(); conn.close(); self.verileri_tazele()

if __name__ == "__main__":
    app = DershaneApp()
    app.mainloop()
