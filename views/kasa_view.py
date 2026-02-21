import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime

class KasaView(ctk.CTkFrame):
    def __init__(self, master, db):
        super().__init__(master, corner_radius=10, fg_color="transparent")
        self.db = db
        
        # Üst Panel
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=10, pady=10)
        
        lbl = ctk.CTkLabel(top_frame, text="💵 Kasa Yönetimi", font=ctk.CTkFont(family="Segoe UI Emoji", size=24, weight="bold"))
        lbl.pack(side="left")
        
        btn_ekle = ctk.CTkButton(top_frame, text="+ Yeni Kasa Tanımla", command=self.kasa_tanimla_modal)
        btn_ekle.pack(side="right", padx=5)

        btn_kasa_duzenle = ctk.CTkButton(top_frame, text="✏️ Kasa Düzenle", command=self.kasa_duzenle_modal, fg_color="orange", hover_color="darkorange")
        btn_kasa_duzenle.pack(side="right", padx=5)

        btn_hareket = ctk.CTkButton(top_frame, text="↕ Nakit Giriş/Çıkış Yap", command=self.hareket_ekle_modal)
        btn_hareket.pack(side="right", padx=5)
        
        btn_sil = ctk.CTkButton(top_frame, text="🗑️ Kasa Sil", command=self.kasa_sil_aksiyon, fg_color="red", hover_color="darkred")
        btn_sil.pack(side="right", padx=5)

        btn_yenile = ctk.CTkButton(top_frame, text="🔄 Yenile", command=self.tabloyu_guncelle, fg_color="gray", hover_color="darkgray")
        btn_yenile.pack(side="right", padx=5)

        # Orta: Kasalar Tablosu
        orta_frame = ctk.CTkFrame(self)
        orta_frame.pack(fill="both", expand=True, padx=10, pady=(10,5))
        
        ctk.CTkLabel(orta_frame, text="Kasalar ve Nakit Durumu", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=5)
        
        self.tree_kasa = ttk.Treeview(orta_frame, columns=("id", "hesap_adi", "bakiye"), show="headings", height=5)
        self.tree_kasa.heading("id", text="ID")
        self.tree_kasa.heading("hesap_adi", text="Kasa Adı")
        self.tree_kasa.heading("bakiye", text="Güncel Bakiye (TL)")
        self.tree_kasa.column("id", width=50, anchor="center")
        self.tree_kasa.pack(fill="both", expand=True, padx=5, pady=5)

        # Alt: Hareketler Tablosu
        alt_frame = ctk.CTkFrame(self)
        alt_frame.pack(fill="both", expand=True, padx=10, pady=(5,10))

        alt_baslik_frame = ctk.CTkFrame(alt_frame, fg_color="transparent")
        alt_baslik_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(alt_baslik_frame, text="Kasa Hareketleri Defteri", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        
        btn_har_sil = ctk.CTkButton(alt_baslik_frame, text="🗑️ Seçili Hareketi Sil", command=self.kasa_hareket_sil_aksiyon, fg_color="red", hover_color="darkred", height=25, font=ctk.CTkFont(size=12))
        btn_har_sil.pack(side="right")

        btn_har_duzenle = ctk.CTkButton(alt_baslik_frame, text="✏️ Seçili Hareketi Düzenle", command=self.hareket_duzenle_modal, fg_color="orange", hover_color="darkorange", height=25, font=ctk.CTkFont(size=12))
        btn_har_duzenle.pack(side="right", padx=5)

        self.tree_har = ttk.Treeview(alt_frame, columns=("id", "kasa", "cari", "tarih", "tutar", "tur", "aciklama"), show="headings", height=10)
        self.tree_har.heading("id", text="ID")
        self.tree_har.heading("kasa", text="İlgili Kasa")
        self.tree_har.heading("cari", text="İlgili Cari")
        self.tree_har.heading("tarih", text="Tarih")
        self.tree_har.heading("tutar", text="Tutar (TL)")
        self.tree_har.heading("tur", text="Tür")
        self.tree_har.heading("aciklama", text="Açıklama / Makbuz No")
        self.tree_har.column("id", width=50, anchor="center")
        self.tree_har.pack(fill="both", expand=True, padx=5, pady=5)

        self.tabloyu_guncelle()

    def tabloyu_guncelle(self):
        for row in self.tree_kasa.get_children(): self.tree_kasa.delete(row)
        for k in self.db.tum_kasalari_getir(): self.tree_kasa.insert("", "end", values=k)

        for row in self.tree_har.get_children(): self.tree_har.delete(row)
        for h in self.db.tum_kasa_hareketleri(): self.tree_har.insert("", "end", values=h)

    def kasa_tanimla_modal(self):
        p = ctk.CTkToplevel(self)
        p.title("Yeni Kasa Tanımla")
        p.geometry("350x200")
        p.grab_set()

        ctk.CTkLabel(p, text="Kasa Adı:").pack(pady=(15,0))
        h_adi = ctk.CTkEntry(p, width=200)
        h_adi.pack(pady=5)

        def kayit():
            with self.master.master.islem_bekle():
                if self.db.kasa_ekle(h_adi.get().strip()):
                    messagebox.showinfo("Başarılı", "Kasa eklendi!")
                    self.tabloyu_guncelle()
                    p.destroy()
                else: messagebox.showerror("Hata", "Eklenemedi.")

        ctk.CTkButton(p, text="Kaydet", command=kayit).pack(pady=20)

    def kasa_duzenle_modal(self):
        selected = self.tree_kasa.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen düzenlemek istediğiniz kasayı seçin.")
            return
        
        k_id, k_adi, bakiye = self.tree_kasa.item(selected[0])['values']
        p = ctk.CTkToplevel(self)
        p.title("Kasa Düzenle")
        p.geometry("350x200")
        p.grab_set()

        ctk.CTkLabel(p, text="Kasa Adı:").pack(pady=(15,0))
        h_adi = ctk.CTkEntry(p, width=200)
        h_adi.insert(0, str(k_adi))
        h_adi.pack(pady=5)

        def guncelle():
            with self.master.master.islem_bekle():
                if self.db.kasa_guncelle(k_id, h_adi.get().strip()):
                    messagebox.showinfo("Başarılı", "Kasa güncellendi!")
                    self.tabloyu_guncelle()
                    p.destroy()
                else: messagebox.showerror("Hata", "Güncellenemedi.")

        ctk.CTkButton(p, text="Güncelle", command=guncelle).pack(pady=20)

    def kasa_sil_aksiyon(self):
        selected = self.tree_kasa.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen silmek istediğiniz kasayı seçin.")
            return
        
        k_id = self.tree_kasa.item(selected[0])['values'][0]
        if messagebox.askyesno("Onay", "Bu kasayı silmek istediğinize emin misiniz?"):
            with self.master.master.islem_bekle():
                if self.db.kasa_sil(k_id):
                    messagebox.showinfo("Başarılı", "Kasa silindi.")
                    self.tabloyu_guncelle()
                else:
                    messagebox.showerror("Hata", "Kasa silinemedi.")

    def kasa_hareket_sil_aksiyon(self):
        selected = self.tree_har.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen silmek istediğiniz hareketi seçin.")
            return
        
        h_id = self.tree_har.item(selected[0])['values'][0]
        if messagebox.askyesno("Onay", "Bu hareketi silmek istediğinize emin misiniz? (Kasa bakiyesi geri düzeltilecektir)"):
            with self.master.master.islem_bekle():
                if self.db.kasa_hareket_sil(h_id):
                    messagebox.showinfo("Başarılı", "Hareket silindi ve bakiye güncellendi.")
                    self.tabloyu_guncelle()
                else:
                    messagebox.showerror("Hata", "Silme işlemi başarısız.")

    def hareket_ekle_modal(self):
        kasalar = self.db.tum_kasalari_getir()
        if not kasalar:
            messagebox.showerror("Hata", "Önce bir kasa tanımlayınız.")
            return
            
        kasa_dict = {f"{k[1]} - {k[2]} TL": k[0] for k in kasalar}
        
        cariler = self.db.tum_carileri_getir()
        cari_dict = {"Boş (Cari Yok)": None}
        for c in cariler:
            cari_dict[f"{c[1]} (Bakiye: {c[4]} TL)"] = c[0]

        p = ctk.CTkToplevel(self)
        p.title("Nakit Giriş / Çıkış")
        p.geometry("380x560")
        p.grab_set()

        ctk.CTkLabel(p, text="İşlem Yapılacak Kasa:").pack(pady=(15,0))
        combo_kasa = ctk.CTkComboBox(p, values=list(kasa_dict.keys()), width=250)
        combo_kasa.pack(pady=5)
        
        ctk.CTkLabel(p, text="İlgili Cari (Opsiyonel):").pack(pady=(10,0))
        combo_cari = ctk.CTkComboBox(p, values=list(cari_dict.keys()), width=250)
        combo_cari.pack(pady=5)

        ctk.CTkLabel(p, text="İşlem Türü:").pack(pady=(10,0))
        combo_tur = ctk.CTkComboBox(p, values=["Giriş", "Çıkış"], width=250)
        combo_tur.pack(pady=5)

        ctk.CTkLabel(p, text="Tarih (YYYY-AA-GG SS:DD:SS):").pack(pady=(10,0))
        e_tarih = ctk.CTkEntry(p, width=250)
        e_tarih.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        e_tarih.pack(pady=5)

        ctk.CTkLabel(p, text="Tutar (TL):").pack(pady=(10,0))
        e_tutar = ctk.CTkEntry(p, width=250)
        e_tutar.pack(pady=5)

        ctk.CTkLabel(p, text="Açıklama (Makbuz vs.):").pack(pady=(10,0))
        e_acik = ctk.CTkEntry(p, width=250)
        e_acik.pack(pady=5)

        def kayit():
            try:
                kid = kasa_dict[combo_kasa.get()]
                cid = cari_dict[combo_cari.get()]
                t = combo_tur.get()
                tutar = float(e_tutar.get().replace(",","."))
                acik = e_acik.get()
                tarih = e_tarih.get()
                if tutar <= 0: raise ValueError
                
                with self.master.master.islem_bekle():
                    if self.db.kasa_hareketi_ekle(kid, tutar, t, acik, tarih, cid):
                        messagebox.showinfo("Başarılı", "Kasa işlemi kaydedildi!")
                        self.tabloyu_guncelle()
                        p.destroy()
                    else: messagebox.showerror("Hata", "İşlem hatası.")
            except:
                messagebox.showerror("Hata", "Tutar veya tarih hatalı!")

        ctk.CTkButton(p, text="Kaydet", command=kayit).pack(pady=20)

    def hareket_duzenle_modal(self):
        selected = self.tree_har.selection()
        if not selected:
             messagebox.showwarning("Uyarı", "Lütfen düzenlemek istediğiniz hareketi seçin.")
             return
        
        h_id, k_adi, c_unvan, tarih, tutar, tur, aciklama = self.tree_har.item(selected[0])['values']
        
        kasalar = self.db.tum_kasalari_getir()
        kasa_dict = {f"{k[1]} - {k[2]} TL": k[0] for k in kasalar}
        
        cariler = self.db.tum_carileri_getir()
        cari_dict = {"Boş (Cari Yok)": None}
        for c in cariler:
            cari_dict[f"{c[1]} (Bakiye: {c[4]} TL)"] = c[0]

        p = ctk.CTkToplevel(self)
        p.title("Kasa Hareketini Düzenle")
        p.geometry("380x560")
        p.grab_set()

        ctk.CTkLabel(p, text="Kasa:").pack(pady=(15,0))
        combo_kasa = ctk.CTkComboBox(p, values=list(kasa_dict.keys()), width=250)
        # Mevcut kasayı seç
        for item in kasa_dict.keys():
            if k_adi in item:
                combo_kasa.set(item)
                break
        combo_kasa.pack(pady=5)
        
        ctk.CTkLabel(p, text="İlgili Cari:").pack(pady=(10,0))
        combo_cari = ctk.CTkComboBox(p, values=list(cari_dict.keys()), width=250)
        # Mevcut cariyi seç
        if c_unvan == "-":
            combo_cari.set("Boş (Cari Yok)")
        else:
            for item in cari_dict.keys():
                if c_unvan in item:
                    combo_cari.set(item)
                    break
        combo_cari.pack(pady=5)

        ctk.CTkLabel(p, text="İşlem Türü:").pack(pady=(10,0))
        combo_tur = ctk.CTkComboBox(p, values=["Giriş", "Çıkış"], width=250)
        combo_tur.set(tur)
        combo_tur.pack(pady=5)

        ctk.CTkLabel(p, text="Tarih:").pack(pady=(10,0))
        e_tarih = ctk.CTkEntry(p, width=250)
        e_tarih.insert(0, str(tarih))
        e_tarih.pack(pady=5)

        ctk.CTkLabel(p, text="Tutar (TL):").pack(pady=(10,0))
        e_tutar = ctk.CTkEntry(p, width=250)
        e_tutar.insert(0, str(tutar))
        e_tutar.pack(pady=5)

        ctk.CTkLabel(p, text="Açıklama:").pack(pady=(10,0))
        e_acik = ctk.CTkEntry(p, width=250)
        e_acik.insert(0, str(aciklama))
        e_acik.pack(pady=5)

        def guncelle():
            try:
                kid = kasa_dict[combo_kasa.get()]
                cid = cari_dict[combo_cari.get()]
                t_tur = combo_tur.get()
                t_tutar = float(e_tutar.get().replace(",","."))
                t_acik = e_acik.get()
                t_tarih = e_tarih.get()
                
                with self.master.master.islem_bekle():
                    if self.db.kasa_hareket_guncelle(h_id, kid, t_tutar, t_tur, t_acik, t_tarih, cid):
                        messagebox.showinfo("Başarılı", "Hareket güncellendi!")
                        self.tabloyu_guncelle()
                        p.destroy()
                    else: messagebox.showerror("Hata", "Güncelleme başarısız.")
            except:
                messagebox.showerror("Hata", "Tutar veya tarih hatalı!")

        ctk.CTkButton(p, text="Güncelle", command=guncelle).pack(pady=20)
