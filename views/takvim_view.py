
import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

class TakvimView(ctk.CTkFrame):
    def __init__(self, master, db):
        super().__init__(master, corner_radius=10, fg_color="transparent")
        self.db = db

        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=10, pady=10)

        lbl = ctk.CTkLabel(top_frame, text="📅 Akıllı Takvim ve Hatırlatıcı", font=ctk.CTkFont(family="Segoe UI Emoji", size=24, weight="bold"))
        lbl.pack(side="left")

        btn_ekle = ctk.CTkButton(top_frame, text="+ Yeni Hatırlatıcı Ekle", command=self.etkinlik_ekle_modal, fg_color="#3498db")
        btn_ekle.pack(side="right", padx=5)

        # Tablo
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(table_frame, columns=("id", "tarih", "saat", "baslik", "oncelik", "aciklama"), show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("tarih", text="Tarih")
        self.tree.heading("saat", text="Saat")
        self.tree.heading("baslik", text="Etkinlik Başlığı")
        self.tree.heading("oncelik", text="Öncelik")
        self.tree.heading("aciklama", text="Açıklama")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("tarih", width=100, anchor="center")
        self.tree.column("saat", width=60, anchor="center")
        self.tree.column("oncelik", width=80, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)

        btn_sil = ctk.CTkButton(self, text="🗑️ Seçiliyi Sil", fg_color="#e74c3c", command=self.etkinlik_sil_aksiyon)
        btn_sil.pack(pady=10)

        self.tabloyu_guncelle()

    def tabloyu_guncelle(self):
        for row in self.tree.get_children(): self.tree.delete(row)
        for e in self.db.etkinlikleri_getir():
            self.tree.insert("", "end", values=e)

    def etkinlik_sil_aksiyon(self):
        sel = self.tree.selection()
        if not sel: return
        if messagebox.askyesno("Onay", "Seçili hatırlatıcıyı silmek istiyor musunuz?"):
            self.db.etkinlik_sil(self.tree.item(sel[0])['values'][0])
            self.tabloyu_guncelle()

    def etkinlik_ekle_modal(self):
        p = ctk.CTkToplevel(self)
        p.title("Yeni Hatırlatıcı")
        p.geometry("400x450")
        p.grab_set()

        ctk.CTkLabel(p, text="Tarih (YYYY-AA-GG):").pack(pady=(15, 0))
        e_tarih = ctk.CTkEntry(p, width=250)
        e_tarih.insert(0, datetime.now().strftime("%Y-%m-%d"))
        e_tarih.pack(pady=5)

        ctk.CTkLabel(p, text="Saat (SS:DD):").pack(pady=(10, 0))
        e_saat = ctk.CTkEntry(p, width=250)
        e_saat.insert(0, "09:00")
        e_saat.pack(pady=5)

        ctk.CTkLabel(p, text="Başlık:").pack(pady=(10, 0))
        e_baslik = ctk.CTkEntry(p, width=250)
        e_baslik.pack(pady=5)

        ctk.CTkLabel(p, text="Öncelik:").pack(pady=(10, 0))
        cmb_oncelik = ctk.CTkComboBox(p, values=["Düşük", "Normal", "Yüksek"], width=250)
        cmb_oncelik.set("Normal")
        cmb_oncelik.pack(pady=5)

        ctk.CTkLabel(p, text="Açıklama:").pack(pady=(10, 0))
        e_aciklama = ctk.CTkEntry(p, width=250)
        e_aciklama.pack(pady=5)

        def kaydet():
            if not e_baslik.get(): return
            if self.db.etkinlik_ekle(e_baslik.get(), e_aciklama.get(), e_tarih.get(), e_saat.get(), cmb_oncelik.get()):
                self.tabloyu_guncelle()
                p.destroy()

        ctk.CTkButton(p, text="💾 Kaydet", command=kaydet).pack(pady=20)
