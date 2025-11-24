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

DB_NAME = "dershane.db"

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
        self.title("Dershane Yönetim Sistemi - Esnek Planlama v5.0")
        self.geometry("1250x850")
        
        self.veritabani_baslat()
        self.tablo_stili_ayarla()

        container = ctk.CTkFrame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        sayfalar = (AnaMenu, OgretmenSayfasi, OgrenciSayfasi, EtutPlanlamaSayfasi, RaporlamaSayfasi, MuduriyetSayfasi)

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
        cur.execute("CREATE TABLE IF NOT EXISTS Ogretmenler (id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT, soyad TEXT, brans TEXT)")
        cur.execute("CREATE TABLE IF NOT EXISTS Ogrenciler (id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT, soyad TEXT, sinif TEXT, numara TEXT UNIQUE)")
        cur.execute("""CREATE TABLE IF NOT EXISTS Etutler (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, ogretmen_id INTEGER, ogrenci_id INTEGER, 
                    ders_adi TEXT, tarih TEXT, saat TEXT, bitis_saati TEXT, sure INTEGER, 
                    katilim_durumu TEXT DEFAULT 'Planlandı',
                    FOREIGN KEY(ogretmen_id) REFERENCES Ogretmenler(id),
                    FOREIGN KEY(ogrenci_id) REFERENCES Ogrenciler(id))""")
        cur.execute("""CREATE TABLE IF NOT EXISTS DersProgrami (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, ogretmen_id INTEGER, gun TEXT, baslangic_saati TEXT, bitis_saati TEXT,
                    FOREIGN KEY(ogretmen_id) REFERENCES Ogretmenler(id))""")
        try: cur.execute("ALTER TABLE Etutler ADD COLUMN bitis_saati TEXT")
        except: pass
        conn.commit(); conn.close()


# ====================================================================
# 1. ANA MENÜ
# ====================================================================
class AnaMenu(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        ctk.CTkLabel(self, text="DERSHANE YÖNETİM PANELİ", font=("Roboto Medium", 36)).pack(pady=(60, 40))
        btn_frame = ctk.CTkFrame(self, fg_color="transparent"); btn_frame.pack()
        conf = {"width": 240, "height": 70, "font": ("Roboto", 16, "bold"), "corner_radius": 12}
        ctk.CTkButton(btn_frame, text="ÖĞRETMEN\nİŞLEMLERİ", command=lambda: controller.show_frame(OgretmenSayfasi), **conf).grid(row=0, column=0, padx=15, pady=15)
        ctk.CTkButton(btn_frame, text="ÖĞRENCİ\nİŞLEMLERİ", command=lambda: controller.show_frame(OgrenciSayfasi), **conf).grid(row=0, column=1, padx=15, pady=15)
        ctk.CTkButton(btn_frame, text="ESNEK ETÜT\nPLANLAMA", fg_color="#1f6aa5", command=lambda: controller.show_frame(EtutPlanlamaSayfasi), **conf).grid(row=1, column=0, padx=15, pady=15)
        ctk.CTkButton(btn_frame, text="GENEL RAPORLAR", command=lambda: controller.show_frame(RaporlamaSayfasi), **conf).grid(row=1, column=1, padx=15, pady=15)
        ctk.CTkLabel(self, text="---------------------------------------------------", text_color="gray").pack(pady=10)
        ctk.CTkButton(self, text="MÜDÜRİYET PANELİ\n(Günlük Yoklama)", fg_color="#D35400", hover_color="#A04000", width=400, height=80, font=("Roboto", 20, "bold"), corner_radius=15, command=lambda: controller.show_frame(MuduriyetSayfasi)).pack(pady=20)


# ====================================================================
# 2. ÖĞRETMEN SAYFASI
# ====================================================================
class OgretmenSayfasi(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        top = ctk.CTkFrame(self, height=60, corner_radius=0, fg_color=("gray85", "gray20")); top.pack(side="top", fill="x")
        ctk.CTkButton(top, text="< ANA MENÜ", width=100, fg_color="transparent", border_width=2, text_color=("black", "white"), command=lambda: controller.show_frame(AnaMenu)).pack(side="left", padx=10, pady=10)
        ctk.CTkLabel(top, text="ÖĞRETMEN YÖNETİMİ", font=("Roboto", 22, "bold")).pack(side="left", padx=20)
        
        form = ctk.CTkFrame(self); form.pack(padx=20, pady=20, fill="x")
        self.ad = self.mk_ent(form, "Ad:", 0, 0); self.soyad = self.mk_ent(form, "Soyad:", 0, 2); self.brans = self.mk_ent(form, "Branş:", 0, 4)
        ctk.CTkButton(form, text="KAYDET", fg_color="green", command=self.kaydet).grid(row=0, column=6, padx=20)
        
        self.tree = ttk.Treeview(self, columns=('id', 'ad', 'soyad', 'brans'), show='headings', height=10)
        for c in ('id', 'ad', 'soyad', 'brans'): self.tree.heading(c, text=c.upper())
        self.tree.column('id', width=50); self.tree.pack(fill="both", expand=True, padx=20, pady=10)
        
        bf = ctk.CTkFrame(self, fg_color="transparent"); bf.pack(pady=10)
        ctk.CTkButton(bf, text="SEÇİLİ ÖĞRETMENİ SİL", fg_color="red", width=200, command=self.sil).pack(side="left", padx=10)
        ctk.CTkButton(bf, text="HAFTALIK DERS PROGRAMI", fg_color="#F39C12", hover_color="#D68910", width=300, command=self.ders_programi_ac).pack(side="left", padx=10)

    def mk_ent(self, p, t, r, c):
        ctk.CTkLabel(p, text=t).grid(row=r, column=c, padx=10); e=ctk.CTkEntry(p); e.grid(row=r, column=c+1, padx=10); return e
    def verileri_tazele(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = sqlite3.connect(DB_NAME); cur = conn.cursor(); cur.execute("SELECT * FROM Ogretmenler")
        for r in cur.fetchall(): self.tree.insert("", "end", values=r)
        conn.close()
    def kaydet(self):
        v = (self.ad.get(), self.soyad.get(), self.brans.get())
        if all(v):
            conn = sqlite3.connect(DB_NAME); conn.execute("INSERT INTO Ogretmenler (ad, soyad, brans) VALUES (?,?,?)", v); conn.commit(); conn.close()
            messagebox.showinfo("Tamam", "Eklendi"); self.verileri_tazele(); self.ad.delete(0,"end"); self.soyad.delete(0,"end"); self.brans.delete(0,"end")
        else: messagebox.showwarning("Hata", "Eksik bilgi")
    def sil(self):
        sel = self.tree.focus()
        if sel:
            if messagebox.askyesno("Sil", "Silmek istediğine emin misin?"):
                id = self.tree.item(sel, 'values')[0]
                conn = sqlite3.connect(DB_NAME); conn.execute("DELETE FROM Ogretmenler WHERE id=?", (id,)); conn.commit(); conn.close(); self.verileri_tazele()
    
    def ders_programi_ac(self):
        sel = self.tree.focus()
        if not sel: messagebox.showwarning("Uyarı", "Listeden bir öğretmen seçin!"); return
        data = self.tree.item(sel, 'values'); hoca_id = data[0]; hoca_ad = f"{data[1]} {data[2]}"
        dp = ctk.CTkToplevel(self); dp.title(f"Ders Programı: {hoca_ad}"); dp.geometry("600x500"); dp.grab_set()
        ctk.CTkLabel(dp, text=f"{hoca_ad} - Meşgul Olduğu Saatler", font=("Roboto", 18, "bold")).pack(pady=10)
        f = ctk.CTkFrame(dp); f.pack(fill="x", padx=10)
        gunler = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
        cb_gun = ctk.CTkComboBox(f, values=gunler); cb_gun.pack(side="left", padx=5)
        ctk.CTkLabel(f, text="Başlangıç:").pack(side="left", padx=5); ent_bas = ctk.CTkEntry(f, width=60, placeholder_text="09:00"); ent_bas.pack(side="left")
        ctk.CTkLabel(f, text="Bitiş:").pack(side="left", padx=5); ent_bit = ctk.CTkEntry(f, width=60, placeholder_text="11:00"); ent_bit.pack(side="left")
        tree_prog = ttk.Treeview(dp, columns=('id', 'gun', 'bas', 'bit'), show='headings', height=10)
        tree_prog.heading('gun', text='Gün'); tree_prog.heading('bas', text='Başlangıç'); tree_prog.heading('bit', text='Bitiş'); tree_prog.column('id', width=0, stretch=False); tree_prog.pack(fill="both", expand=True, padx=10, pady=10)
        def program_yukle():
            for i in tree_prog.get_children(): tree_prog.delete(i)
            conn = sqlite3.connect(DB_NAME); cur = conn.cursor(); cur.execute("SELECT id, gun, baslangic_saati, bitis_saati FROM DersProgrami WHERE ogretmen_id=?", (hoca_id,))
            for r in cur.fetchall(): tree_prog.insert("", "end", values=r)
            conn.close()
        def program_ekle():
            gun = cb_gun.get(); bas = ent_bas.get(); bit = ent_bit.get()
            if not (gun and bas and bit): return
            conn = sqlite3.connect(DB_NAME); conn.execute("INSERT INTO DersProgrami (ogretmen_id, gun, baslangic_saati, bitis_saati) VALUES (?,?,?,?)", (hoca_id, gun, bas, bit)); conn.commit(); conn.close(); program_yukle()
        def program_sil():
            sel = tree_prog.focus()
            if sel:
                pid = tree_prog.item(sel, 'values')[0]
                conn = sqlite3.connect(DB_NAME); conn.execute("DELETE FROM DersProgrami WHERE id=?", (pid,)); conn.commit(); conn.close(); program_yukle()
        ctk.CTkButton(f, text="EKLE", width=60, command=program_ekle).pack(side="left", padx=10)
        ctk.CTkButton(dp, text="Seçili Saati Sil", fg_color="red", command=program_sil).pack(pady=10)
        program_yukle()


# ====================================================================
# 3. ÖĞRENCİ SAYFASI (Standart)
# ====================================================================
class OgrenciSayfasi(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        top = ctk.CTkFrame(self, height=60, corner_radius=0, fg_color=("gray85", "gray20")); top.pack(side="top", fill="x")
        ctk.CTkButton(top, text="< ANA MENÜ", width=100, fg_color="transparent", border_width=2, text_color=("black", "white"), command=lambda: controller.show_frame(AnaMenu)).pack(side="left", padx=10, pady=10)
        ctk.CTkLabel(top, text="ÖĞRENCİ YÖNETİMİ", font=("Roboto", 22, "bold")).pack(side="left", padx=20)
        
        form = ctk.CTkFrame(self); form.pack(padx=20, pady=10, fill="x")
        self.ad = self.mk_ent(form, "Ad:", 0, 0); self.soyad = self.mk_ent(form, "Soyad:", 0, 2)
        self.sinif = self.mk_ent(form, "Sınıf:", 0, 4); self.no = self.mk_ent(form, "No:", 0, 6)
        ctk.CTkButton(form, text="KAYDET", fg_color="green", command=self.kaydet).grid(row=0, column=8, padx=20)
        
        self.tree = ttk.Treeview(self, columns=('id', 'ad', 'soyad', 'sinif', 'num'), show='headings', height=15)
        for c in ('id', 'ad', 'soyad', 'sinif', 'num'): self.tree.heading(c, text=c.upper())
        self.tree.column('id', width=50); self.tree.pack(fill="both", expand=True, padx=20, pady=10)
        ctk.CTkButton(self, text="SİL", fg_color="red", command=self.sil).pack(pady=20)

    def mk_ent(self, p, t, r, c):
        ctk.CTkLabel(p, text=t).grid(row=r, column=c, padx=10); e=ctk.CTkEntry(p); e.grid(row=r, column=c+1, padx=10); return e
    def verileri_tazele(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = sqlite3.connect(DB_NAME); cur = conn.cursor(); cur.execute("SELECT * FROM Ogrenciler")
        for r in cur.fetchall(): self.tree.insert("", "end", values=r)
        conn.close()
    def kaydet(self):
        v = (self.ad.get(), self.soyad.get(), self.sinif.get(), self.no.get())
        if all(v):
            try:
                conn = sqlite3.connect(DB_NAME); conn.execute("INSERT INTO Ogrenciler (ad, soyad, sinif, numara) VALUES (?,?,?,?)", v); conn.commit(); conn.close(); messagebox.showinfo("Tamam", "Eklendi"); self.verileri_tazele(); self.ad.delete(0,"end"); self.soyad.delete(0,"end"); self.sinif.delete(0,"end"); self.no.delete(0,"end")
            except: messagebox.showerror("Hata", "Numara kayıtlı")
        else: messagebox.showwarning("Hata", "Eksik")
    def sil(self):
        s = self.tree.focus()
        if s:
            if messagebox.askyesno("Sil", "Silinsin mi?"):
                conn = sqlite3.connect(DB_NAME); conn.execute("DELETE FROM Ogrenciler WHERE id=?", (self.tree.item(s,'values')[0],)); conn.commit(); conn.close(); self.verileri_tazele()


# ====================================================================
# 4. ETÜT PLANLAMA (ESNEK TABLO + MANUEL SEÇİM)
# ====================================================================
class EtutPlanlamaSayfasi(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.ogretmen_map = {}
        
        # Başlık
        top = ctk.CTkFrame(self, height=60, corner_radius=0, fg_color=("gray85", "gray20"))
        top.pack(side="top", fill="x")
        ctk.CTkButton(top, text="< ANA MENÜ", width=100, fg_color="transparent", border_width=2, text_color=("black", "white"), command=lambda: controller.show_frame(AnaMenu)).pack(side="left", padx=10, pady=10)
        ctk.CTkLabel(top, text="ESNEK ETÜT PLANLAMA", font=("Roboto", 22, "bold")).pack(side="left", padx=20)

        # --- Filtreleme Alanı ---
        filter_frame = ctk.CTkFrame(self)
        filter_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(filter_frame, text="Tarih (GG.AA.YYYY):").pack(side="left", padx=5)
        self.ent_tarih = ctk.CTkEntry(filter_frame, width=120)
        self.ent_tarih.pack(side="left", padx=5)
        self.ent_tarih.insert(0, datetime.now().strftime("%d.%m.%Y"))

        ctk.CTkLabel(filter_frame, text="Öğretmen Seç:").pack(side="left", padx=10)
        self.cb_hoca = ctk.CTkComboBox(filter_frame, width=200, command=self.tabloyu_guncelle)
        self.cb_hoca.pack(side="left", padx=5)

        ctk.CTkButton(filter_frame, text="TABLOYU GÖSTER", command=self.tabloyu_guncelle).pack(side="left", padx=20)

        # --- Görsel Tablo Alanı ---
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="Öğretmen Doluluk Durumu")
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # --- Manuel Ekleme Butonu ---
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(btn_frame, text="+ YENİ ETÜT EKLE", fg_color="green", height=50, font=("Roboto", 16, "bold"), command=self.yeni_etut_penceresi_ac).pack(fill="x")

    def verileri_tazele(self):
        conn = sqlite3.connect(DB_NAME); cur = conn.cursor()
        self.ogretmen_map.clear(); hl = []
        cur.execute("SELECT id, ad, soyad, brans FROM Ogretmenler")
        for r in cur.fetchall(): 
            txt = f"{r[1]} {r[2]} ({r[3]})"
            self.ogretmen_map[txt] = r[0]
            hl.append(txt)
        conn.close()
        self.cb_hoca.configure(values=hl)
        if hl: self.cb_hoca.set(hl[0])
        
        # Tabloyu temizle
        for widget in self.scroll_frame.winfo_children(): widget.destroy()

    def tabloyu_guncelle(self, event=None):
        for widget in self.scroll_frame.winfo_children(): widget.destroy()
        
        secili_hoca = self.cb_hoca.get()
        if not secili_hoca: return
        hoca_id = self.ogretmen_map[secili_hoca]
        tarih = self.ent_tarih.get()

        conn = sqlite3.connect(DB_NAME); cur = conn.cursor()
        
        # 1. Etütleri Çek
        cur.execute("""SELECT E.saat, E.bitis_saati, O.ad || ' ' || O.soyad, E.ders_adi, E.id 
                       FROM Etutler E LEFT JOIN Ogrenciler O ON E.ogrenci_id=O.id 
                       WHERE E.ogretmen_id=? AND E.tarih=? ORDER BY E.saat""", (hoca_id, tarih))
        etutler = cur.fetchall()

        # 2. Ders Programını Çek
        tarih_obj = datetime.strptime(tarih, "%d.%m.%Y")
        gunler = {0: "Pazartesi", 1: "Salı", 2: "Çarşamba", 3: "Perşembe", 4: "Cuma", 5: "Cumartesi", 6: "Pazar"}
        gun_adi = gunler[tarih_obj.weekday()]
        cur.execute("SELECT baslangic_saati, bitis_saati FROM DersProgrami WHERE ogretmen_id=? AND gun=?", (hoca_id, gun_adi))
        dersler = cur.fetchall()
        conn.close()

        # --- GÖRSELLEŞTİRME ---
        row = 0
        ctk.CTkLabel(self.scroll_frame, text=f"{secili_hoca} - {tarih} Programı", font=("Roboto", 16, "bold")).grid(row=row, column=0, sticky="w", padx=10, pady=5); row+=1

        # Sabit Dersler
        if dersler:
            ctk.CTkLabel(self.scroll_frame, text="--- OKUL DERSLERİ (MEŞGUL) ---", text_color="orange").grid(row=row, column=0, sticky="w", padx=10); row+=1
            for d in dersler:
                card = ctk.CTkFrame(self.scroll_frame, fg_color="#D35400", corner_radius=8)
                card.grid(row=row, column=0, sticky="ew", padx=10, pady=2)
                ctk.CTkLabel(card, text=f"🕒 {d[0]} - {d[1]} | OKUL DERSİ", text_color="white", font=("Roboto", 14, "bold")).pack(side="left", padx=10, pady=10)
                row += 1

        # Etütler
        ctk.CTkLabel(self.scroll_frame, text="--- ETÜTLER ---", text_color="#5DADE2").grid(row=row, column=0, sticky="w", padx=10); row+=1
        if not etutler:
            ctk.CTkLabel(self.scroll_frame, text="Henüz etüt yok. Aşağıdan ekleyin.").grid(row=row, column=0, padx=10)
        
        for e in etutler: # e: (saat, bitis, ogr_ad, ders, id)
            card = ctk.CTkFrame(self.scroll_frame, fg_color="#2E4053", corner_radius=8)
            card.grid(row=row, column=0, sticky="ew", padx=10, pady=2)
            
            bilgi = f"🕒 {e[0]} - {e[1]} | 👤 {e[2]} | 📚 {e[3]}"
            ctk.CTkLabel(card, text=bilgi, font=("Roboto", 14)).pack(side="left", padx=10, pady=10)
            
            ctk.CTkButton(card, text="SİL", fg_color="red", width=60, command=lambda eid=e[4]: self.etut_sil(eid)).pack(side="right", padx=10)
            row += 1

    def etut_sil(self, eid):
        if messagebox.askyesno("Sil", "Bu etüdü silmek istediğinize emin misiniz?"):
            conn = sqlite3.connect(DB_NAME); conn.execute("DELETE FROM Etutler WHERE id=?", (eid,)); conn.commit(); conn.close()
            self.tabloyu_guncelle()

    def yeni_etut_penceresi_ac(self):
        secili_hoca = self.cb_hoca.get()
        tarih = self.ent_tarih.get()
        
        if not secili_hoca: messagebox.showwarning("Hata", "Önce listeden öğretmen seçin!"); return

        # Popup
        pop = ctk.CTkToplevel(self)
        pop.title("Yeni Etüt Ekle")
        pop.geometry("400x500")
        pop.grab_set()

        ctk.CTkLabel(pop, text=f"Hoca: {secili_hoca}\nTarih: {tarih}", font=("Roboto", 16, "bold")).pack(pady=15)

        # Öğrenci Seçimi
        conn = sqlite3.connect(DB_NAME); cur = conn.cursor()
        cur.execute("SELECT id, ad, soyad, sinif, numara FROM Ogrenciler")
        ogr_map = {}; ogr_list = []
        for r in cur.fetchall():
            txt = f"{r[1]} {r[2]} ({r[3]}-{r[4]})"
            ogr_map[txt] = r[0]
            ogr_list.append(txt)
        conn.close()

        ctk.CTkLabel(pop, text="Öğrenci Seç:").pack()
        cb_ogr = ctk.CTkComboBox(pop, values=ogr_list, width=250)
        cb_ogr.pack(pady=5)

        ctk.CTkLabel(pop, text="Başlangıç Saati (SS:DD):").pack()
        ent_saat = ctk.CTkEntry(pop, width=100, placeholder_text="14:00")
        ent_saat.pack(pady=5)

        ctk.CTkLabel(pop, text="Süre (dk):").pack()
        ent_sure = ctk.CTkEntry(pop, width=100)
        ent_sure.insert(0, "40")
        ent_sure.pack(pady=5)

        ctk.CTkLabel(pop, text="Ders Konusu:").pack()
        ent_ders = ctk.CTkEntry(pop, width=250)
        ent_ders.pack(pady=5)

        def kaydet():
            ogr_txt = cb_ogr.get(); saat = ent_saat.get(); sure = ent_sure.get(); ders = ent_ders.get()
            if not (ogr_txt and saat and sure and ders): messagebox.showwarning("Hata", "Tüm alanları doldurun."); return
            
            ogr_id = ogr_map[ogr_txt]
            hoca_id = self.ogretmen_map[secili_hoca]

            # Hesaplamalar
            try:
                bas_dt = datetime.strptime(saat, "%H:%M")
                bit_dt = bas_dt + timedelta(minutes=int(sure))
                bit_saat = bit_dt.strftime("%H:%M")
            except: messagebox.showerror("Hata", "Saat formatı hatalı (Örn: 14:30)"); return

            conn = sqlite3.connect(DB_NAME); cur = conn.cursor()

            # 1. Çakışma Kontrolü (Ders Programı)
            dt_obj = datetime.strptime(tarih, "%d.%m.%Y")
            gunler = {0: "Pazartesi", 1: "Salı", 2: "Çarşamba", 3: "Perşembe", 4: "Cuma", 5: "Cumartesi", 6: "Pazar"}
            gun_adi = gunler[dt_obj.weekday()]
            cur.execute("SELECT baslangic_saati, bitis_saati FROM DersProgrami WHERE ogretmen_id=? AND gun=?", (hoca_id, gun_adi))
            for sb, se in cur.fetchall():
                if not (bit_saat <= sb or saat >= se): messagebox.showerror("Çakışma", f"Hoca {sb}-{se} arası okul dersinde!"); conn.close(); return

            # 2. Çakışma Kontrolü (Etütler)
            cur.execute("SELECT saat, bitis_saati FROM Etutler WHERE ogretmen_id=? AND tarih=?", (hoca_id, tarih))
            for es, ee in cur.fetchall():
                if not ee: ee = (datetime.strptime(es, "%H:%M") + timedelta(minutes=40)).strftime("%H:%M") # Eskiler için
                if not (bit_saat <= es or saat >= ee): messagebox.showerror("Çakışma", f"Hoca {es}-{ee} arası dolu!"); conn.close(); return

            # 3. 3 Hak Kuralı (Yumuşak Limit)
            cur.execute("SELECT count(*) FROM Etutler WHERE ogrenci_id=? AND katilim_durumu NOT IN ('Geldi', 'Gelmedi')", (ogr_id,))
            if cur.fetchone()[0] >= 3:
                if not messagebox.askyesno("Limit Uyarısı", "Öğrencinin limiti dolmuş. Yine de verilsin mi?"): conn.close(); return

            # Kayıt
            cur.execute("INSERT INTO Etutler (ogretmen_id, ogrenci_id, ders_adi, tarih, saat, bitis_saati, sure) VALUES (?,?,?,?,?,?,?)",
                        (hoca_id, ogr_id, ders, tarih, saat, bit_saat, sure))
            conn.commit(); conn.close()
            messagebox.showinfo("Başarılı", "Etüt Eklendi"); pop.destroy(); self.tabloyu_guncelle()

        ctk.CTkButton(pop, text="KAYDET", fg_color="green", height=40, command=kaydet).pack(pady=20, fill="x", padx=20)


# ====================================================================
# 5. MÜDÜRİYET SAYFASI
# ====================================================================
class MuduriyetSayfasi(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        top = ctk.CTkFrame(self, height=60, corner_radius=0, fg_color="#D35400"); top.pack(side="top", fill="x")
        ctk.CTkButton(top, text="< ANA MENÜ", width=100, fg_color="transparent", border_width=2, text_color="white", command=lambda: controller.show_frame(AnaMenu)).pack(side="left", padx=10)
        ctk.CTkLabel(top, text="MÜDÜRİYET PANELİ", font=("Roboto", 22, "bold"), text_color="white").pack(side="left", padx=20)

        filt = ctk.CTkFrame(self); filt.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(filt, text="Tarih:").pack(side="left", padx=10)
        self.ent_tar = ctk.CTkEntry(filt); self.ent_tar.pack(side="left", padx=10)
        self.ent_tar.insert(0, (datetime.now() - timedelta(days=1)).strftime("%d.%m.%Y"))
        ctk.CTkButton(filt, text="GETİR", command=self.getir).pack(side="left", padx=10)

        self.tree = ttk.Treeview(self, columns=('id', 'hoca', 'ogr', 'ders', 'saat', 'durum'), show='headings', height=15)
        for c in ('id', 'hoca', 'ogr', 'ders', 'saat', 'durum'): self.tree.heading(c, text=c.upper())
        self.tree.column('id', width=40); self.tree.pack(fill="both", expand=True, padx=20, pady=5)

        bf = ctk.CTkFrame(self, fg_color="transparent"); bf.pack(fill="x", padx=20, pady=20)
        ctk.CTkButton(bf, text="GELDİ (✓)", fg_color="green", height=60, command=lambda: self.isaretle("Geldi")).pack(side="left", fill="x", expand=True, padx=10)
        ctk.CTkButton(bf, text="GELMEDİ (X)", fg_color="#C0392B", height=60, command=lambda: self.isaretle("Gelmedi")).pack(side="left", fill="x", expand=True, padx=10)

    def verileri_tazele(self): self.getir()
    def getir(self):
        tar = self.ent_tar.get()
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = sqlite3.connect(DB_NAME); cur = conn.cursor()
        cur.execute("""SELECT E.id, O.ad||' '||O.soyad, Og.ad||' '||Og.soyad, E.ders_adi, E.saat, E.katilim_durumu 
                       FROM Etutler E LEFT JOIN Ogretmenler O ON E.ogretmen_id=O.id LEFT JOIN Ogrenciler Og ON E.ogrenci_id=Og.id
                       WHERE E.tarih=? ORDER BY E.saat ASC""", (tar,))
        for r in cur.fetchall(): self.tree.insert("", "end", values=r)
        conn.close()
    def isaretle(self, d):
        s = self.tree.focus()
        if s:
            conn = sqlite3.connect(DB_NAME); conn.execute("UPDATE Etutler SET katilim_durumu=? WHERE id=?", (d, self.tree.item(s,'values')[0])); conn.commit(); conn.close(); self.getir()

# ====================================================================
# 6. RAPORLAMA
# ====================================================================
class RaporlamaSayfasi(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller; self.ogretmen_map = {}; self.ogrenci_map = {}
        top = ctk.CTkFrame(self, height=60, corner_radius=0, fg_color=("gray85", "gray20")); top.pack(side="top", fill="x")
        ctk.CTkButton(top, text="< ANA MENÜ", width=100, fg_color="transparent", border_width=2, text_color=("black", "white"), command=lambda: controller.show_frame(AnaMenu)).pack(side="left", padx=10)
        ctk.CTkLabel(top, text="RAPORLAMA", font=("Roboto", 22, "bold")).pack(side="left", padx=20)

        kf = ctk.CTkFrame(self); kf.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(kf, text="Başlangıç:").grid(row=0, column=0); self.eb = ctk.CTkEntry(kf); self.eb.grid(row=0, column=1, padx=5)
        ctk.CTkLabel(kf, text="Bitiş:").grid(row=0, column=2); self.ebr = ctk.CTkEntry(kf); self.ebr.grid(row=0, column=3, padx=5)
        ctk.CTkLabel(kf, text="Hoca:").grid(row=1, column=0); self.co = ctk.CTkComboBox(kf); self.co.grid(row=1, column=1, padx=5, pady=5)
        ctk.CTkLabel(kf, text="Öğrenci:").grid(row=1, column=2); self.cs = ctk.CTkComboBox(kf); self.cs.grid(row=1, column=3, padx=5, pady=5)
        ctk.CTkButton(kf, text="GETİR", command=self.raporla).grid(row=2, column=0, columnspan=4, pady=10)

        self.tree = ttk.Treeview(self, columns=('id', 'h', 'o', 'd', 't', 's', 'du'), show='headings')
        for c in ('id', 'h', 'o', 'd', 't', 's', 'du'): self.tree.heading(c, text=c)
        self.tree.pack(fill="both", expand=True, padx=20)
        ctk.CTkButton(self, text="EXCEL", fg_color="green", command=self.excel).pack(pady=10)

    def verileri_tazele(self):
        n = datetime.now(); self.ebr.delete(0,"end"); self.ebr.insert(0, n.strftime("%d.%m.%Y"))
        self.eb.delete(0,"end"); self.eb.insert(0, (n-timedelta(30)).strftime("%d.%m.%Y"))
        conn = sqlite3.connect(DB_NAME); cur = conn.cursor()
        self.ogretmen_map={"TÜMÜ":None}; l1=["TÜMÜ"]; cur.execute("SELECT id, ad, soyad FROM Ogretmenler")
        for r in cur.fetchall(): t=f"{r[1]} {r[2]}"; self.ogretmen_map[t]=r[0]; l1.append(t)
        self.co.configure(values=l1); self.co.set("TÜMÜ")
        self.ogrenci_map={"TÜMÜ":None}; l2=["TÜMÜ"]; cur.execute("SELECT id, ad, soyad FROM Ogrenciler")
        for r in cur.fetchall(): t=f"{r[1]} {r[2]}"; self.ogrenci_map[t]=r[0]; l2.append(t)
        self.cs.configure(values=l2); self.cs.set("TÜMÜ")
        conn.close(); self.raporla()

    def raporla(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        try:
            b = self.eb.get().split('.'); s = self.ebr.get().split('.')
            bs = f"{b[2]}.{b[1]}.{b[0]}"; ss = f"{s[2]}.{s[1]}.{s[0]}"
        except: return
        hid = self.ogretmen_map.get(self.co.get()); oid = self.ogrenci_map.get(self.cs.get())
        sql = "SELECT E.id, O.ad||' '||O.soyad, Og.ad||' '||Og.soyad, E.ders_adi, E.tarih, E.saat, E.katilim_durumu FROM Etutler E LEFT JOIN Ogretmenler O ON E.ogretmen_id=O.id LEFT JOIN Ogrenciler Og ON E.ogrenci_id=Og.id"
        cond = ["substr(E.tarih,7,4)||'.'||substr(E.tarih,4,2)||'.'||substr(E.tarih,1,2) BETWEEN ? AND ?"]; p = [bs, ss]
        if hid: cond.append("E.ogretmen_id=?"); p.append(hid)
        if oid: cond.append("E.ogrenci_id=?"); p.append(oid)
        sql += " WHERE " + " AND ".join(cond) + " ORDER BY substr(E.tarih,7,4) DESC, E.saat DESC"
        conn = sqlite3.connect(DB_NAME); cur = conn.cursor(); cur.execute(sql, p)
        for r in cur.fetchall(): self.tree.insert("", "end", values=r)
        conn.close()

    def excel(self):
        if not OPENPYXL_YUKLU: messagebox.showerror("Hata", "openpyxl yok"); return
        p = filedialog.asksaveasfilename(defaultextension=".xlsx")
        if p:
            wb = Workbook(); ws = wb.active; ws.append(['ID','Hoca','Ogr','Ders','Tar','Saat','Durum'])
            for i in self.tree.get_children(): ws.append(self.tree.item(i)['values'])
            wb.save(p); messagebox.showinfo("Tamam", "Kaydedildi")

if __name__ == "__main__":
    app = DershaneApp()
    app.mainloop()