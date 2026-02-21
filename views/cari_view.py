import customtkinter as ctk
from tkinter import ttk, messagebox

class CariView(ctk.CTkFrame):
    def __init__(self, master, db):
        super().__init__(master, corner_radius=10, fg_color="transparent")
        self.db = db
        
        # Başlık ve Butonlar
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=10, pady=10)
        
        lbl = ctk.CTkLabel(top_frame, text="👥 Cari Yönetimi", font=ctk.CTkFont(family="Segoe UI Emoji", size=24, weight="bold"))
        lbl.pack(side="left")
        
        btn_ekle = ctk.CTkButton(top_frame, text="+ Yeni Cari Ekle", command=self.cari_ekle_modal)
        btn_ekle.pack(side="right", padx=5)
        
        btn_duzenle = ctk.CTkButton(top_frame, text="✏️ Seçili Cariyi Düzenle", command=self.cari_duzenle_modal, fg_color="orange", hover_color="darkorange")
        btn_duzenle.pack(side="right", padx=5)
        
        btn_sil = ctk.CTkButton(top_frame, text="🗑️ Seçili Cariyi Sil", command=self.cari_sil_aksiyon, fg_color="red", hover_color="darkred")
        btn_sil.pack(side="right", padx=5)
        
        btn_yenile = ctk.CTkButton(top_frame, text="🔄 Yenile", command=self.tabloyu_guncelle, fg_color="gray", hover_color="darkgray")
        btn_yenile.pack(side="right", padx=5)

        btn_ekstre = ctk.CTkButton(top_frame, text="📋 Cari Ekstresi", command=self.cari_ekstresi_modal, fg_color="#8e44ad", hover_color="#6c3483")
        btn_ekstre.pack(side="right", padx=5)

        btn_notlar = ctk.CTkButton(top_frame, text="📝 Notlar", command=self.cari_notlar_modal, fg_color="#34495e", hover_color="#2c3e50")
        btn_notlar.pack(side="right", padx=5)

        # Tablo Çerçevesi
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Treeview (Tablo)
        columns = ("id", "unvan", "vergi_no", "telefon", "bakiye", "tarih")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        self.tree.heading("id", text="ID")
        self.tree.heading("unvan", text="Cari Ünvan")
        self.tree.heading("vergi_no", text="Vergi / TC No")
        self.tree.heading("telefon", text="Telefon")
        self.tree.heading("bakiye", text="Bakiye (TL)")
        self.tree.heading("tarih", text="Kayıt Tarihi")

        self.tree.column("id", width=50, anchor="center")
        self.tree.column("bakiye", width=100, anchor="e")
        
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.tabloyu_guncelle()

    def tabloyu_guncelle(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        cariler = self.db.tum_carileri_getir()
        for c in cariler:
            self.tree.insert("", "end", values=c)

    def cari_sil_aksiyon(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen silmek istediğiniz cariyi seçin.")
            return
        
        c_id = self.tree.item(selected[0])['values'][0]
        if messagebox.askyesno("Onay", "Bu cariyi silmek istediğinize emin misiniz?"):
            if self.db.cari_sil(c_id):
                messagebox.showinfo("Başarılı", "Cari silindi.")
                self.tabloyu_guncelle()
            else:
                messagebox.showerror("Hata", "Cari silinemedi.")

    def cari_ekle_modal(self):
        pencere = ctk.CTkToplevel(self)
        pencere.title("Yeni Cari Ekle")
        pencere.geometry("450x550")
        pencere.grab_set()
        
        ctk.CTkLabel(pencere, text="Ünvan:").pack(pady=(10,0))
        entry_unvan = ctk.CTkEntry(pencere, width=250)
        entry_unvan.pack(pady=2)
        
        ctk.CTkLabel(pencere, text="Cari Türü:").pack(pady=(5,0))
        cmb_turu = ctk.CTkComboBox(pencere, values=["Hibrit", "Müşteri", "Tedarikçi"], width=250)
        cmb_turu.pack(pady=2)

        ctk.CTkLabel(pencere, text="Özel İskonto (%):").pack(pady=(5,0))
        entry_isk = ctk.CTkEntry(pencere, width=250)
        entry_isk.insert(0, "0.0")
        entry_isk.pack(pady=2)

        ctk.CTkLabel(pencere, text="Fiyat Grubu:").pack(pady=(5,0))
        cmb_grup = ctk.CTkComboBox(pencere, values=["Liste Fiyatı", "Özel Fiyat 1", "Özel Fiyat 2"], width=250)
        cmb_grup.pack(pady=2)

        ctk.CTkLabel(pencere, text="Vergi No:").pack(pady=(5,0))
        entry_vergi = ctk.CTkEntry(pencere, width=250)
        entry_vergi.pack(pady=2)
        
        ctk.CTkLabel(pencere, text="Telefon:").pack(pady=(5,0))
        entry_tel = ctk.CTkEntry(pencere, width=250)
        entry_tel.pack(pady=2)

        from datetime import datetime
        ctk.CTkLabel(pencere, text="Kayıt Tarihi:").pack(pady=(5,0))
        entry_tarih = ctk.CTkEntry(pencere, width=250)
        entry_tarih.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        entry_tarih.pack(pady=2)
        
        def kaydet():
            u = entry_unvan.get().strip()
            v = entry_vergi.get().strip()
            t = entry_tel.get().strip()
            tur = cmb_turu.get()
            isk = float(entry_isk.get() or 0.0)
            grp = cmb_grup.get()
            tar = entry_tarih.get().strip()
            if not u:
                messagebox.showerror("Hata", "Ünvan boş bırakılamaz!")
                return
            with self.master.master.islem_bekle():
                if self.db.cari_ekle(u, v, t, tur, isk, grp, tar):
                    messagebox.showinfo("Başarılı", "Cari eklendi!")
                    self.tabloyu_guncelle()
                    pencere.destroy()
                else:
                    messagebox.showerror("Hata", "Eklenirken bir sorun oluştu.")

        ctk.CTkButton(pencere, text="Kaydet", command=kaydet).pack(pady=15)

    def cari_duzenle_modal(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen düzenlemek istediğiniz cariyi seçin.")
            return
        
        item = self.tree.item(selected[0])['values']
        # id, unvan, vergi, tel, bakiye, tarih, tur, isk, grup
        c_id, unvan, vergi, tel, bakiye, tarih, tur, isk, grup = item
        
        pencere = ctk.CTkToplevel(self)
        pencere.title("Cariyi Düzenle")
        pencere.geometry("450x500")
        pencere.grab_set() 
        
        ctk.CTkLabel(pencere, text="Ünvan:").pack(pady=(10,0))
        entry_unvan = ctk.CTkEntry(pencere, width=250)
        entry_unvan.insert(0, str(unvan))
        entry_unvan.pack(pady=2)
        
        ctk.CTkLabel(pencere, text="Cari Türü:").pack(pady=(5,0))
        cmb_turu = ctk.CTkComboBox(pencere, values=["Hibrit", "Müşteri", "Tedarikçi"], width=250)
        cmb_turu.set(str(tur))
        cmb_turu.pack(pady=2)

        ctk.CTkLabel(pencere, text="Özel İskonto (%):").pack(pady=(5,0))
        entry_isk = ctk.CTkEntry(pencere, width=250)
        entry_isk.insert(0, str(isk))
        entry_isk.pack(pady=2)

        ctk.CTkLabel(pencere, text="Fiyat Grubu:").pack(pady=(5,0))
        cmb_grup = ctk.CTkComboBox(pencere, values=["Liste Fiyatı", "Özel Fiyat 1", "Özel Fiyat 2"], width=250)
        cmb_grup.set(str(grup) if grup else "Liste Fiyatı")
        cmb_grup.pack(pady=2)

        ctk.CTkLabel(pencere, text="Vergi No:").pack(pady=(5,0))
        entry_vergi = ctk.CTkEntry(pencere, width=250)
        entry_vergi.insert(0, str(vergi))
        entry_vergi.pack(pady=2)
        
        ctk.CTkLabel(pencere, text="Telefon:").pack(pady=(5,0))
        entry_tel = ctk.CTkEntry(pencere, width=250)
        entry_tel.insert(0, str(tel))
        entry_tel.pack(pady=2)
        
        def guncelle():
            u = entry_unvan.get().strip()
            v = entry_vergi.get().strip()
            t = entry_tel.get().strip()
            tur_v = cmb_turu.get()
            isk_v = float(entry_isk.get() or 0.0)
            grp_v = cmb_grup.get()
            if not u:
                messagebox.showerror("Hata", "Ünvan boş bırakılamaz!")
                return
            with self.master.master.islem_bekle():
                if self.db.cari_guncelle(c_id, u, v, t, tur_v, isk_v, grp_v):
                    messagebox.showinfo("Başarılı", "Cari güncellendi!")
                    self.tabloyu_guncelle()
                    pencere.destroy()
                else:
                    messagebox.showerror("Hata", "Güncellenirken sorun oluştu.")

        ctk.CTkButton(pencere, text="Güncelle", command=guncelle).pack(pady=15)

    def cari_ekstresi_modal(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen ekstreyi görüntülemek istediğiniz cariyi seçin.")
            return
        item = self.tree.item(selected[0])['values']
        c_id, unvan = item[0], item[1]

        p = ctk.CTkToplevel(self)
        p.title(f"📋 Cari Ekstresi: {unvan}")
        p.geometry("1000x620")
        p.grab_set()

        # Filtre Satırı
        filtre_frame = ctk.CTkFrame(p, fg_color="transparent")
        filtre_frame.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(filtre_frame, text="Başlangıç Tarihi (YYYY-AA-GG):").pack(side="left", padx=5)
        e_bas = ctk.CTkEntry(filtre_frame, width=130)
        e_bas.pack(side="left", padx=5)

        ctk.CTkLabel(filtre_frame, text="Bitiş:").pack(side="left", padx=5)
        e_bit = ctk.CTkEntry(filtre_frame, width=130)
        e_bit.pack(side="left", padx=5)

        def yukle():
            for row in tree_e.get_children(): tree_e.delete(row)
            bas = e_bas.get().strip() or None
            bit = e_bit.get().strip() or None
            rows = self.db.cari_ekstresi_getir(c_id, bas, bit)
            bakiye = 0.0
            for r in rows:
                tarih, aciklama, tur, borc, alacak, tutar, kaynak = r
                bakiye += float(borc) - float(alacak)
                tree_e.insert("", "end", values=(
                    str(tarih)[:10] if tarih else "",
                    tur,
                    aciklama,
                    kaynak,
                    f"{borc:.2f}" if borc else "",
                    f"{alacak:.2f}" if alacak else "",
                    f"{bakiye:.2f}"
                ))
            # Bakiye özeti
            toplam_borc = sum(float(r[3]) for r in rows)
            toplam_alacak = sum(float(r[4]) for r in rows)
            lbl_ozet.configure(text=f"Borç Toplamı: {toplam_borc:.2f} TL  |  Ödeme/Alacak: {toplam_alacak:.2f} TL  |  Net Bakiye: {toplam_borc - toplam_alacak:.2f} TL")

        btn_goster = ctk.CTkButton(filtre_frame, text="🔍 Listele", command=yukle)
        btn_goster.pack(side="left", padx=10)

        # Tablo
        tree_frame = ctk.CTkFrame(p)
        tree_frame.pack(fill="both", expand=True, padx=15, pady=5)

        cols = ("tarih", "tur", "aciklama", "kaynak", "borc", "alacak", "bakiye")
        tree_e = ttk.Treeview(tree_frame, columns=cols, show="headings")
        tree_e.heading("tarih", text="Tarih")
        tree_e.heading("tur", text="Tür")
        tree_e.heading("aciklama", text="Açıklama / Evrak No")
        tree_e.heading("kaynak", text="Kaynak")
        tree_e.heading("borc", text="Borç (TL)")
        tree_e.heading("alacak", text="Tahsilat (TL)")
        tree_e.heading("bakiye", text="Kümülatif Bakiye")
        tree_e.column("tarih", width=90, anchor="center")
        tree_e.column("tur", width=100, anchor="center")
        tree_e.column("kaynak", width=90, anchor="center")
        tree_e.column("borc", width=90, anchor="e")
        tree_e.column("alacak", width=90, anchor="e")
        tree_e.column("bakiye", width=110, anchor="e")
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree_e.yview)
        tree_e.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        tree_e.pack(fill="both", expand=True)

        # Özet satırı
        lbl_ozet = ctk.CTkLabel(p, text="——", font=ctk.CTkFont(size=13, weight="bold"))
        lbl_ozet.pack(pady=8)

        # İlk yükleme
        yukle()

    def cari_notlar_modal(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen bir cari seçin.")
            return
        c_id = self.tree.item(selected[0])['values'][0]
        unvan = self.tree.item(selected[0])['values'][1]

        p = ctk.CTkToplevel(self)
        p.title(f"📝 Cari Notlar: {unvan}")
        p.geometry("500x400")
        p.grab_set()

        txt_not = ctk.CTkTextbox(p, font=("Arial", 13))
        txt_not.pack(fill="both", expand=True, padx=20, pady=20)

        # Mevcut notu getir
        esk_not = self.db.cari_not_getir(c_id)
        if esk_not:
            txt_not.insert("0.0", esk_not[0])

        def kaydet():
            yeni_not = txt_not.get("0.0", "end").strip()
            if self.db.cari_not_kaydet(c_id, yeni_not):
                messagebox.showinfo("Başarılı", "Not kaydedildi.")
                p.destroy()

        ctk.CTkButton(p, text="💾 Notu Kaydet", command=kaydet).pack(pady=(0, 20))
