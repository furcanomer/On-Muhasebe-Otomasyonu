
import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime

class PersonelView(ctk.CTkFrame):
    def __init__(self, master, db):
        super().__init__(master, corner_radius=10, fg_color="transparent")
        self.db = db

        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=10, pady=10)

        lbl = ctk.CTkLabel(top_frame, text="👤 Çalışan (Personel) Yönetimi", font=ctk.CTkFont(family="Segoe UI Emoji", size=24, weight="bold"))
        lbl.pack(side="left")

        btn_ekle = ctk.CTkButton(top_frame, text="+ Yeni Personel Ekle", command=self.personel_ekle_modal, fg_color="#2ecc71")
        btn_ekle.pack(side="right", padx=5)
        
        btn_hareket = ctk.CTkButton(top_frame, text="💸 Ödeme/Maaş Girişi", command=self.hareket_ekle_modal, fg_color="#e67e22")
        btn_hareket.pack(side="right", padx=5)

        # Tablo
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        cols = ("id", "ad", "kat", "giris", "cikis", "maas", "tel", "bakiye")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("ad", text="Ad Soyad")
        self.tree.heading("kat", text="Kategori")
        self.tree.heading("giris", text="Giriş")
        self.tree.heading("cikis", text="Çıkış")
        self.tree.heading("maas", text="Aylık Maaş")
        self.tree.heading("tel", text="Telefon")
        self.tree.heading("bakiye", text="Bakiye (Alacak)")

        for c in cols: self.tree.column(c, width=100, anchor="center")
        self.tree.column("ad", width=150)
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)

        self.tabloyu_guncelle()

    def tabloyu_guncelle(self):
        for row in self.tree.get_children(): self.tree.delete(row)
        for p in self.db.tum_calisanlari_getir():
            self.tree.insert("", "end", values=p)

    def personel_ekle_modal(self):
        p = ctk.CTkToplevel(self)
        p.title("Yeni Personel")
        p.geometry("400x500")
        p.grab_set()

        ctk.CTkLabel(p, text="Ad Soyad:").pack(pady=(15, 0))
        e_ad = ctk.CTkEntry(p, width=250)
        e_ad.pack(pady=5)

        ctk.CTkLabel(p, text="Kategori (Şoför, Ofis vb.):").pack(pady=(10, 0))
        e_kat = ctk.CTkEntry(p, width=250)
        e_kat.pack(pady=5)

        ctk.CTkLabel(p, text="İşe Giriş Tarihi:").pack(pady=(10, 0))
        e_giris = ctk.CTkEntry(p, width=250)
        e_giris.insert(0, datetime.now().strftime("%Y-%m-%d"))
        e_giris.pack(pady=5)

        ctk.CTkLabel(p, text="Aylık Maaş:").pack(pady=(10, 0))
        e_maas = ctk.CTkEntry(p, width=250)
        e_maas.insert(0, "0.00")
        e_maas.pack(pady=5)

        ctk.CTkLabel(p, text="Telefon:").pack(pady=(10, 0))
        e_tel = ctk.CTkEntry(p, width=250)
        e_tel.pack(pady=5)

        def kaydet():
            try:
                if self.db.calisan_ekle(e_ad.get(), e_kat.get(), e_giris.get(), float(e_maas.get()), e_tel.get()):
                    self.tabloyu_guncelle()
                    p.destroy()
            except: messagebox.showerror("Hata", "Maaş sayısal olmalı")

        ctk.CTkButton(p, text="💾 Kaydet", command=kaydet).pack(pady=20)

    def hareket_ekle_modal(self):
        sel = self.tree.selection()
        if not sel: 
            messagebox.showwarning("Uyarı", "Lütfen bir personel seçin.")
            return
        p_id = self.tree.item(sel[0])['values'][0]
        p_ad = self.tree.item(sel[0])['values'][1]

        m = ctk.CTkToplevel(self)
        m.title(f"Hareket Girişi - {p_ad}")
        m.geometry("400x400")
        m.grab_set()

        ctk.CTkLabel(m, text="İşlem Türü:").pack(pady=(15, 0))
        cmb_tur = ctk.CTkComboBox(m, values=["Maaş Tahakkuku", "Ödeme", "Avans"], width=250)
        cmb_tur.set("Ödeme")
        cmb_tur.pack(pady=5)

        ctk.CTkLabel(m, text="Tutar:").pack(pady=(10, 0))
        e_tutar = ctk.CTkEntry(m, width=250)
        e_tutar.pack(pady=5)

        ctk.CTkLabel(m, text="Açıklama:").pack(pady=(10, 0))
        e_acik = ctk.CTkEntry(m, width=250)
        e_acik.pack(pady=5)

        def kaydet():
            try:
                if self.db.personel_hareketi_ekle(p_id, float(e_tutar.get()), cmb_tur.get(), e_acik.get()):
                    self.tabloyu_guncelle()
                    m.destroy()
            except: messagebox.showerror("Hata", "Tutar sayısal olmalı")

        ctk.CTkButton(m, text="💾 Onayla", command=kaydet).pack(pady=20)
