import customtkinter as ctk
from tkinter import ttk, messagebox

class BankaView(ctk.CTkFrame):
    def __init__(self, master, db):
        super().__init__(master, corner_radius=10, fg_color="transparent")
        self.db = db
        
        # Üst Panel
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=10, pady=10)
        
        lbl = ctk.CTkLabel(top_frame, text="🏦 Banka Yönetimi", font=ctk.CTkFont(family="Segoe UI Emoji", size=24, weight="bold"))
        lbl.pack(side="left")
        
        btn_ekle = ctk.CTkButton(top_frame, text="+ Yeni Banka Ekle", command=self.banka_tanimla_modal)
        btn_ekle.pack(side="right", padx=5)

        btn_banka_duzenle = ctk.CTkButton(top_frame, text="✏️ Banka Düzenle", command=self.banka_duzenle_modal, fg_color="orange", hover_color="darkorange")
        btn_banka_duzenle.pack(side="right", padx=5)

        btn_hareket = ctk.CTkButton(top_frame, text="↕ Havale/EFT İşlemi", command=self.hareket_ekle_modal)
        btn_hareket.pack(side="right", padx=5)
        
        btn_sil = ctk.CTkButton(top_frame, text="🗑️ Banka Hesabı Sil", command=self.banka_sil_aksiyon, fg_color="red", hover_color="darkred")
        btn_sil.pack(side="right", padx=5)

        btn_yenile = ctk.CTkButton(top_frame, text="🔄 Yenile", command=self.tabloyu_guncelle, fg_color="gray", hover_color="darkgray")
        btn_yenile.pack(side="right", padx=5)

        # Orta: Bankalar Tablosu
        orta_frame = ctk.CTkFrame(self)
        orta_frame.pack(fill="both", expand=True, padx=10, pady=(10,5))
        
        ctk.CTkLabel(orta_frame, text="Banka Hesapları Durumu", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=5)
        
        self.tree_banka = ttk.Treeview(orta_frame, columns=("id", "hesap_adi", "iban", "bakiye"), show="headings", height=5)
        self.tree_banka.heading("id", text="ID")
        self.tree_banka.heading("hesap_adi", text="Banka Adı")
        self.tree_banka.heading("iban", text="IBAN No")
        self.tree_banka.heading("bakiye", text="Güncel Bakiye (TL)")
        self.tree_banka.column("id", width=50, anchor="center")
        self.tree_banka.pack(fill="both", expand=True, padx=5, pady=5)

        # Alt: Banka Hareketleri
        alt_frame = ctk.CTkFrame(self)
        alt_frame.pack(fill="both", expand=True, padx=10, pady=(5,10))

        alt_baslik_frame = ctk.CTkFrame(alt_frame, fg_color="transparent")
        alt_baslik_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(alt_baslik_frame, text="Banka Hesap Hareketleri Defteri", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        
        btn_har_sil = ctk.CTkButton(alt_baslik_frame, text="🗑️ Seçili Hareketi Sil", command=self.banka_hareket_sil_aksiyon, fg_color="red", hover_color="darkred", height=25, font=ctk.CTkFont(size=12))
        btn_har_sil.pack(side="right")

        btn_har_duzenle = ctk.CTkButton(alt_baslik_frame, text="✏️ Seçili Hareketi Düzenle", command=self.banka_hareket_duzenle_modal, fg_color="orange", hover_color="darkorange", height=25, font=ctk.CTkFont(size=12))
        btn_har_duzenle.pack(side="right", padx=5)

        self.tree_har = ttk.Treeview(alt_frame, columns=("id", "banka", "cari", "tarih", "tutar", "tur", "aciklama"), show="headings", height=10)
        self.tree_har.heading("id", text="ID")
        self.tree_har.heading("banka", text="İlgili Banka")
        self.tree_har.heading("cari", text="İlgili Cari")
        self.tree_har.heading("tarih", text="Tarih")
        self.tree_har.heading("tutar", text="Tutar (TL)")
        self.tree_har.heading("tur", text="Tür")
        self.tree_har.heading("aciklama", text="Açıklama / Dekont No")
        self.tree_har.column("id", width=50, anchor="center")
        self.tree_har.pack(fill="both", expand=True, padx=5, pady=5)

        self.tabloyu_guncelle()

    def tabloyu_guncelle(self):
        for row in self.tree_banka.get_children(): self.tree_banka.delete(row)
        for b in self.db.tum_bankalari_getir(): self.tree_banka.insert("", "end", values=b)

        for row in self.tree_har.get_children(): self.tree_har.delete(row)
        for h in self.db.tum_banka_hareketleri(): self.tree_har.insert("", "end", values=h)

    def banka_tanimla_modal(self):
        p = ctk.CTkToplevel(self)
        p.title("Yeni Banka Tanımla")
        p.geometry("350x250")
        p.grab_set()

        ctk.CTkLabel(p, text="Banka & Hesap Adı:").pack(pady=(15,0))
        h_adi = ctk.CTkEntry(p, width=200)
        h_adi.pack(pady=5)

        ctk.CTkLabel(p, text="IBAN No:").pack(pady=(10,0))
        h_iban = ctk.CTkEntry(p, width=200)
        h_iban.pack(pady=5)

        def kayit():
            with self.master.master.islem_bekle():
                if self.db.banka_ekle(h_adi.get().strip(), h_iban.get().strip()):
                    messagebox.showinfo("Başarılı", "Banka eklendi!")
                    self.tabloyu_guncelle()
                    p.destroy()
                else: messagebox.showerror("Hata", "Eklenemedi.")

        ctk.CTkButton(p, text="Kaydet", command=kayit).pack(pady=20)

    def banka_duzenle_modal(self):
        selected = self.tree_banka.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen düzenlemek istediğiniz hesabı seçin.")
            return
        
        b_id, b_adi, iban, bakiye = self.tree_banka.item(selected[0])['values']
        
        p = ctk.CTkToplevel(self)
        p.title("Banka Düzenle")
        p.geometry("350x250")
        p.grab_set()

        ctk.CTkLabel(p, text="Banka & Hesap Adı:").pack(pady=(15,0))
        h_adi = ctk.CTkEntry(p, width=200)
        h_adi.insert(0, str(b_adi))
        h_adi.pack(pady=5)

        ctk.CTkLabel(p, text="IBAN No:").pack(pady=(10,0))
        h_iban = ctk.CTkEntry(p, width=200)
        h_iban.insert(0, str(iban))
        h_iban.pack(pady=5)

        def guncelle():
            with self.master.master.islem_bekle():
                if self.db.banka_guncelle(b_id, h_adi.get().strip(), h_iban.get().strip()):
                    messagebox.showinfo("Başarılı", "Banka güncellendi!")
                    self.tabloyu_guncelle()
                    p.destroy()
                else: messagebox.showerror("Hata", "Güncellenemedi.")

        ctk.CTkButton(p, text="Güncelle", command=guncelle).pack(pady=20)

    def banka_sil_aksiyon(self):
        selected = self.tree_banka.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen silmek istediğiniz hesabı seçin.")
            return
        
        b_id = self.tree_banka.item(selected[0])['values'][0]
        if messagebox.askyesno("Onay", "Bu banka hesabını silmek istediğinize emin misiniz?"):
            with self.master.master.islem_bekle():
                if self.db.banka_sil(b_id):
                    messagebox.showinfo("Başarılı", "Banka hesabı silindi.")
                    self.tabloyu_guncelle()
                else:
                    messagebox.showerror("Hata", "Silinemedi.")

    def banka_hareket_sil_aksiyon(self):
        selected = self.tree_har.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen silmek istediğiniz hareketi seçin.")
            return
        
        h_id = self.tree_har.item(selected[0])['values'][0]
        if messagebox.askyesno("Onay", "Bu hareketi silmek istediğinize emin misiniz? (Banka bakiyesi geri düzeltilecektir)"):
            with self.master.master.islem_bekle():
                if self.db.banka_hareket_sil(h_id):
                    messagebox.showinfo("Başarılı", "Hareket silindi ve bakiye güncellendi.")
                    self.tabloyu_guncelle()
                else:
                    messagebox.showerror("Hata", "Silme işlemi başarısız.")

    def hareket_ekle_modal(self):
        bankalar = self.db.tum_bankalari_getir()
        if not bankalar:
            messagebox.showerror("Hata", "Önce bir banka tanımlayınız.")
            return
            
        banka_dict = {f"{b[1]} - {b[3]} TL": b[0] for b in bankalar}

        cariler = self.db.tum_carileri_getir()
        cari_dict = {"Boş (Cari Yok)": None}
        for c in cariler:
            cari_dict[f"{c[1]} (Bakiye: {c[4]} TL)"] = c[0]

        p = ctk.CTkToplevel(self)
        p.title("Banka Giriş / Çıkış İşlemi")
        p.geometry("380x560")
        p.grab_set()

        ctk.CTkLabel(p, text="İşlem Yapılacak Banka:").pack(pady=(15,0))
        combo_banka = ctk.CTkComboBox(p, values=list(banka_dict.keys()), width=250)
        combo_banka.pack(pady=5)
        
        ctk.CTkLabel(p, text="İlgili Cari (Opsiyonel):").pack(pady=(10,0))
        combo_cari = ctk.CTkComboBox(p, values=list(cari_dict.keys()), width=250)
        combo_cari.pack(pady=5)

        ctk.CTkLabel(p, text="İşlem Türü:").pack(pady=(10,0))
        combo_tur = ctk.CTkComboBox(p, values=["Giriş", "Çıkış"], width=250)
        combo_tur.pack(pady=5)

        from datetime import datetime
        ctk.CTkLabel(p, text="Tarih:").pack(pady=(10,0))
        e_tarih = ctk.CTkEntry(p, width=250)
        e_tarih.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        e_tarih.pack(pady=5)

        ctk.CTkLabel(p, text="Tutar (TL):").pack(pady=(10,0))
        e_tutar = ctk.CTkEntry(p, width=250)
        e_tutar.pack(pady=5)

        ctk.CTkLabel(p, text="Açıklama (Dekont vb.):").pack(pady=(10,0))
        e_acik = ctk.CTkEntry(p, width=250)
        e_acik.pack(pady=5)

        def kayit():
            try:
                bid = banka_dict[combo_banka.get()]
                cid = cari_dict[combo_cari.get()]
                t = combo_tur.get()
                tutar = float(e_tutar.get().replace(",","."))
                acik = e_acik.get()
                tarih = e_tarih.get()
                if tutar <= 0: raise ValueError
                
                with self.master.master.islem_bekle():
                    if self.db.banka_hareketi_ekle(bid, tutar, t, acik, tarih, cid):
                        messagebox.showinfo("Başarılı", "Banka işlemi kaydedildi!")
                        self.tabloyu_guncelle()
                        p.destroy()
                    else: messagebox.showerror("Hata", "İşlem hatası.")
            except:
                messagebox.showerror("Hata", "Tutar veya tarih hatalı!")

        ctk.CTkButton(p, text="Kaydet", command=kayit).pack(pady=20)

    def banka_hareket_duzenle_modal(self):
        selected = self.tree_har.selection()
        if not selected:
             messagebox.showwarning("Uyarı", "Lütfen düzenlemek istediğiniz hareketi seçin.")
             return
        
        h_id, b_adi, c_unvan, tarih, tutar, tur, aciklama = self.tree_har.item(selected[0])['values']
        
        bankalar = self.db.tum_bankalari_getir()
        banka_dict = {f"{b[1]} - {b[3]} TL": b[0] for b in bankalar}
        
        cariler = self.db.tum_carileri_getir()
        cari_dict = {"Boş (Cari Yok)": None}
        for c in cariler:
            cari_dict[f"{c[1]} (Bakiye: {c[4]} TL)"] = c[0]

        p = ctk.CTkToplevel(self)
        p.title("Banka Hareketini Düzenle")
        p.geometry("380x560")
        p.grab_set()

        ctk.CTkLabel(p, text="Banka:").pack(pady=(15,0))
        combo_banka = ctk.CTkComboBox(p, values=list(banka_dict.keys()), width=250)
        for item in banka_dict.keys():
            if b_adi in item:
                combo_banka.set(item)
                break
        combo_banka.pack(pady=5)
        
        ctk.CTkLabel(p, text="İlgili Cari:").pack(pady=(10,0))
        combo_cari = ctk.CTkComboBox(p, values=list(cari_dict.keys()), width=250)
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
                bid = banka_dict[combo_banka.get()]
                cid = cari_dict[combo_cari.get()]
                t_tur = combo_tur.get()
                t_tutar = float(e_tutar.get().replace(",","."))
                t_acik = e_acik.get()
                t_tarih = e_tarih.get()
                
                with self.master.master.islem_bekle():
                    if self.db.banka_hareket_guncelle(h_id, bid, t_tutar, t_tur, t_acik, t_tarih, cid):
                        messagebox.showinfo("Başarılı", "Banka hareketi güncellendi!")
                        self.tabloyu_guncelle()
                        p.destroy()
                    else: messagebox.showerror("Hata", "Güncelleme başarısız.")
            except:
                messagebox.showerror("Hata", "Tutar veya tarih hatalı!")

        ctk.CTkButton(p, text="Güncelle", command=guncelle).pack(pady=20)
