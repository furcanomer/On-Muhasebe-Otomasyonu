import customtkinter as ctk
from tkinter import ttk, messagebox

BIRIM_LISTESI = ["Adet", "Kg", "Ton", "m³", "m²", "m", "Lt", "Litre", "Paket", "Koli", "Çuval"]

class StokView(ctk.CTkFrame):
    def __init__(self, master, db):
        super().__init__(master, corner_radius=10, fg_color="transparent")
        self.db = db
        
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=10, pady=10)
        
        lbl = ctk.CTkLabel(top_frame, text="📦 Stok/Envanter Yönetimi", font=ctk.CTkFont(family="Segoe UI Emoji", size=24, weight="bold"))
        lbl.pack(side="left")
        
        btn_ekle = ctk.CTkButton(top_frame, text="+ Yeni Ürün/Hizmet Ekle", command=self.stok_ekle_modal)
        btn_ekle.pack(side="right", padx=5)
        
        btn_duzenle = ctk.CTkButton(top_frame, text="✏️ Düzenle", command=self.stok_duzenle_modal, fg_color="orange", hover_color="darkorange")
        btn_duzenle.pack(side="right", padx=5)
        
        btn_sil = ctk.CTkButton(top_frame, text="🗑️ Sil", command=self.stok_sil_aksiyon, fg_color="red", hover_color="darkred")
        btn_sil.pack(side="right", padx=5)
        
        btn_yenile = ctk.CTkButton(top_frame, text="🔄 Yenile", command=self.tabloyu_guncelle, fg_color="gray", hover_color="darkgray")
        btn_yenile.pack(side="right", padx=5)

        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("id", "barkod", "urun", "miktar", "birim", "kritik", "fiyat")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        self.tree.heading("id", text="ID")
        self.tree.heading("barkod", text="Barkod / Kod")
        self.tree.heading("urun", text="Ürün / Hizmet Adı")
        self.tree.heading("miktar", text="Miktar")
        self.tree.heading("birim", text="Birim")
        self.tree.heading("kritik", text="Kritik Seviye")
        self.tree.heading("fiyat", text="Birim Fiyat (TL)")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("miktar", width=80, anchor="center")
        self.tree.column("birim", width=70, anchor="center")
        self.tree.column("kritik", width=80, anchor="center")
        self.tree.column("fiyat", width=110, anchor="e")
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.tabloyu_guncelle()

    def tabloyu_guncelle(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        stoklar = self.db.tum_stoklari_getir()
        for s in stoklar:
            # s = (id, barkod, urun_adi, miktar, kritik_seviye, fiyat, birim)
            # Fiyat 4 hane gösterilecek
            self.tree.insert("", "end", values=(s[0], s[1], s[2], s[3], s[6], s[4], f"{s[5]:.4f}"))

    def stok_sil_aksiyon(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen silmek istediğiniz ürünü seçin.")
            return
        
        s_id = self.tree.item(selected[0])['values'][0]
        if messagebox.askyesno("Onay", "Bu ürünü silmek istediğinize emin misiniz?"):
            if self.db.stok_sil(s_id):
                messagebox.showinfo("Başarılı", "Ürün silindi.")
                self.tabloyu_guncelle()
            else:
                messagebox.showerror("Hata", "Ürün silinemedi.")

    def stok_ekle_modal(self):
        pencere = ctk.CTkToplevel(self)
        pencere.title("Yeni Ürün / Hizmet Ekle")
        pencere.geometry("420x520")
        pencere.grab_set()
        
        ctk.CTkLabel(pencere, text="Barkod / Kod:").pack(pady=(15,0))
        e_barkod = ctk.CTkEntry(pencere, width=280)
        e_barkod.pack(pady=5)
        
        ctk.CTkLabel(pencere, text="Ürün / Hizmet Adı:").pack(pady=(10,0))
        e_urun = ctk.CTkEntry(pencere, width=280)
        e_urun.pack(pady=5)

        ctk.CTkLabel(pencere, text="Birim:").pack(pady=(10,0))
        cmb_birim = ctk.CTkComboBox(pencere, values=BIRIM_LISTESI, width=280)
        cmb_birim.set("Adet")
        cmb_birim.pack(pady=5)
        
        ctk.CTkLabel(pencere, text="Başlangıç Miktarı:").pack(pady=(10,0))
        e_miktar = ctk.CTkEntry(pencere, width=280)
        e_miktar.insert(0, "0")
        e_miktar.pack(pady=5)

        ctk.CTkLabel(pencere, text="Kritik Stok Uyarı Seviyesi:").pack(pady=(10,0))
        e_kritik = ctk.CTkEntry(pencere, width=280)
        e_kritik.insert(0, "10")
        e_kritik.pack(pady=5)

        ctk.CTkLabel(pencere, text="Birim Fiyat (TL):").pack(pady=(10,0))
        e_fiyat = ctk.CTkEntry(pencere, width=280)
        e_fiyat.insert(0, "0.0")
        e_fiyat.pack(pady=5)

        def kaydet():
            try:
                b = e_barkod.get().strip()
                u = e_urun.get().strip()
                birim = cmb_birim.get()
                m = float(e_miktar.get().replace(",", "."))
                k = float(e_kritik.get().replace(",", "."))
                f = float(e_fiyat.get().replace(",", "."))
                if not u or not b:
                    messagebox.showerror("Hata", "Ürün adı ve barkod zorunludur.")
                    return
                with self.master.master.islem_bekle():
                    if self.db.stok_ekle(b, u, m, k, f, birim):
                        self.tabloyu_guncelle()
                        messagebox.showinfo("Başarılı", "Ürün eklendi!")
                        pencere.destroy()
                    else:
                        messagebox.showerror("Hata", "Barkod mevcut veya kayıt başarısız.")
            except ValueError:
                messagebox.showerror("Hata", "Miktar, Seviye veya Fiyat sayısal değer olmalıdır!")

        ctk.CTkButton(pencere, text="💾 Kaydet (F2)", command=kaydet).pack(pady=20)
        pencere.bind("<F2>", lambda e: kaydet())
        pencere.bind("<Escape>", lambda e: pencere.destroy())

    def stok_duzenle_modal(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen düzenlemek istediğiniz ürünü seçin.")
            return
        
        item = self.tree.item(selected[0])['values']
        s_id, barkod, urun, miktar, birim, kritik, fiyat = item
        
        pencere = ctk.CTkToplevel(self)
        pencere.title("Ürün Düzenle")
        pencere.geometry("420x520")
        pencere.grab_set()
        
        ctk.CTkLabel(pencere, text="Barkod / Kod:").pack(pady=(15,0))
        e_barkod = ctk.CTkEntry(pencere, width=280)
        e_barkod.insert(0, str(barkod))
        e_barkod.pack(pady=5)
        
        ctk.CTkLabel(pencere, text="Ürün / Hizmet Adı:").pack(pady=(10,0))
        e_urun = ctk.CTkEntry(pencere, width=280)
        e_urun.insert(0, str(urun))
        e_urun.pack(pady=5)

        ctk.CTkLabel(pencere, text="Birim:").pack(pady=(10,0))
        cmb_birim = ctk.CTkComboBox(pencere, values=BIRIM_LISTESI, width=280)
        cmb_birim.set(str(birim) if birim else "Adet")
        cmb_birim.pack(pady=5)
        
        ctk.CTkLabel(pencere, text="Mevcut Miktar:").pack(pady=(10,0))
        e_miktar = ctk.CTkEntry(pencere, width=280)
        e_miktar.insert(0, str(miktar))
        e_miktar.pack(pady=5)

        ctk.CTkLabel(pencere, text="Kritik Seviye:").pack(pady=(10,0))
        e_kritik = ctk.CTkEntry(pencere, width=280)
        e_kritik.insert(0, str(kritik))
        e_kritik.pack(pady=5)

        ctk.CTkLabel(pencere, text="Birim Fiyat (TL):").pack(pady=(10,0))
        e_fiyat = ctk.CTkEntry(pencere, width=280)
        e_fiyat.insert(0, str(fiyat))
        e_fiyat.pack(pady=5)

        def guncelle():
            try:
                b = e_barkod.get().strip()
                u = e_urun.get().strip()
                birim_v = cmb_birim.get()
                m = float(e_miktar.get().replace(",", "."))
                k = float(e_kritik.get().replace(",", "."))
                f = float(e_fiyat.get().replace(",", "."))
                if not u or not b:
                    messagebox.showerror("Hata", "Ürün adı ve barkod zorunludur.")
                    return
                with self.master.master.islem_bekle():
                    if self.db.stok_guncelle(s_id, b, u, m, k, f, birim_v):
                        self.tabloyu_guncelle()
                        messagebox.showinfo("Başarılı", "Ürün güncellendi!")
                        pencere.destroy()
                    else:
                        messagebox.showerror("Hata", "Güncelleme başarısız.")
            except ValueError:
                messagebox.showerror("Hata", "Miktar, Seviye veya Fiyat sayısal değer olmalıdır!")

        ctk.CTkButton(pencere, text="Güncelle", command=guncelle).pack(pady=20)
