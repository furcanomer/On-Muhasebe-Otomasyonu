import customtkinter as ctk
import os
import shutil
import re
from tkinter import messagebox, filedialog

class VeriYonetimiModal(ctk.CTkToplevel):
    def __init__(self, master_db, parent_view):
        super().__init__()
        self.title("⚙️ Yedekleme ve Veri Yönetimi")
        self.geometry("500x480")
        self.master_db = master_db
        self.parent_view = parent_view
        self.attributes("-topmost", True)
        
        lbl = ctk.CTkLabel(self, text="Veri İçe ve Dışa Aktarma", font=ctk.CTkFont(size=20, weight="bold"))
        lbl.pack(pady=20)
        
        self.guncelle()
        
    def guncelle(self):
        for widget in self.winfo_children():
            if widget.winfo_class() != 'CTkLabel':
                widget.destroy()
                
        self.sirketler = self.master_db.tum_sirketleri_getir()
        self.sirket_dict = {s_adi: db_kodu for s_id, s_adi, db_kodu in self.sirketler}
        self.sirket_isimleri = list(self.sirket_dict.keys())
        
        self.cmb_sirket = ctk.CTkComboBox(self, values=self.sirket_isimleri if self.sirket_isimleri else ["Şirket Yok"])
        self.cmb_sirket.pack(pady=10)
        
        btn_ice = ctk.CTkButton(self, text="📥 Seçili Şirkete İçe Aktar", fg_color="orange", hover_color="darkorange", command=self.secili_ice_aktar)
        btn_ice.pack(pady=10)
        
        btn_disa = ctk.CTkButton(self, text="💾 Seçili Şirketi Dışa Aktar", fg_color="green", hover_color="darkgreen", command=self.secili_disa_aktar)
        btn_disa.pack(pady=10)
        
        ctk.CTkFrame(self, height=2, fg_color="gray").pack(fill="x", padx=40, pady=20)
        
        btn_tum_disa = ctk.CTkButton(self, text="🗂️ Tüm Şirketleri Dışa Aktar", command=self.tumunu_disa_aktar)
        btn_tum_disa.pack(pady=10)
        
        btn_toplu = ctk.CTkButton(self, text="🔄 Genel / Toplu İçe Aktarma", command=self.toplu_ice_aktar)
        btn_toplu.pack(pady=10)
        
    def secili_disa_aktar(self):
        secim = self.cmb_sirket.get()
        if secim not in self.sirket_dict: return
        kaynak = self.sirket_dict[secim]
        if not os.path.exists(kaynak):
            messagebox.showerror("Hata", "Veri dosyası bulunamadı!")
            return
        hedef = filedialog.asksaveasfilename(defaultextension=".db", initialfile=f"{secim}_yedek.db", title=f"'{secim}' Verisini Kaydet", filetypes=(("SQLite", "*.db"), ("Tüm", "*.*")))
        if hedef:
            shutil.copy2(kaynak, hedef)
            messagebox.showinfo("Başarılı", "Yedek başarıyla alındı.")
            self.attributes("-topmost", True)

    def secili_ice_aktar(self):
        secim = self.cmb_sirket.get()
        if secim not in self.sirket_dict: return
        hedef = self.sirket_dict[secim]
        
        dosya = filedialog.askopenfilename(title=f"'{secim}' İçin Yedek Seç", filetypes=(("SQLite", "*.db"), ("Tüm", "*.*")))
        if dosya:
            self.attributes("-topmost", False)
            if messagebox.askyesno("Uyarı", f"'{secim}' şirketinin tüm verileri silinip, seçtiğiniz bu dosyanın verileriyle değiştirilecek.\nEmin misiniz?"):
                shutil.copy2(dosya, hedef)
                messagebox.showinfo("Başarılı", "Veri başarıyla içe aktarıldı.")
            self.attributes("-topmost", True)

    def tumunu_disa_aktar(self):
        if not self.sirket_dict: return
        klasor = filedialog.askdirectory(title="Dışa Aktarılacak Klasörü Seçin")
        if klasor:
            basarili = 0
            for adi, db_kodu in self.sirket_dict.items():
                if os.path.exists(db_kodu):
                    hedef = os.path.join(klasor, f"{adi}_yedek.db")
                    shutil.copy2(db_kodu, hedef)
                    basarili += 1
            if basarili > 0:
                messagebox.showinfo("Başarılı", f"{basarili} adet şirketin yedeği başarıyla klasöre çıkarıldı.")
            self.attributes("-topmost", True)

    def toplu_ice_aktar(self):
        dosyalar = filedialog.askopenfilenames(title="İçe Aktarılacak Şirket Yedeklerini Seçin", filetypes=(("SQLite", "*.db"), ("Tüm", "*.*")))
        if not dosyalar: return
        
        basarili = 0
        self.attributes("-topmost", False)
        for ds in dosyalar:
            isim = os.path.basename(ds).replace("_yedek.db", "").replace(".db", "")
            
            var_mi = False
            hedef_kodu = None
            for s_id, s_adi, db_kodu in self.master_db.tum_sirketleri_getir():
                if s_adi == isim:
                    var_mi = True
                    hedef_kodu = db_kodu
                    break
                    
            if var_mi:
                if messagebox.askyesno("Şirket Zaten Var", f"'{isim}' adında bir şirket sistemde zaten var.\nMevcut verileri tamamen silip yedeğin üzerine yazılmasını onaylıyor musunuz?"):
                    shutil.copy2(ds, hedef_kodu)
                    basarili += 1
            else:
                db_kodu = f"{re.sub(r'[\\/*?:\"<>|]', '', isim).strip()}.db"
                if self.master_db.sirket_ekle(isim, db_kodu):
                    shutil.copy2(ds, db_kodu)
                    basarili += 1
        
        if basarili > 0:
            messagebox.showinfo("Başarılı", f"{basarili} adet yedek başarıyla sisteme aktarıldı.")
            self.parent_view.sirketleri_listele()
            self.guncelle()
        self.attributes("-topmost", True)

class SirketSecimView(ctk.CTkFrame):
    def __init__(self, master, master_db, on_sirket_secildi):
        super().__init__(master, corner_radius=15, fg_color="transparent")
        self.master_db = master_db
        self.on_sirket_secildi = on_sirket_secildi
        
        # Ekranı Merkeze Alma Çerçevesi
        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.pack(expand=True)
        
        lbl = ctk.CTkLabel(center_frame, text="Hoş Geldiniz", font=ctk.CTkFont(family="Segoe UI Emoji", size=32, weight="bold"))
        lbl.pack(pady=(0, 10))
        
        lbl_alt = ctk.CTkLabel(center_frame, text="Devam etmek için bir şirket seçin veya yeni oluşturun", font=ctk.CTkFont(family="Segoe UI Emoji", size=14), text_color="gray")
        lbl_alt.pack(pady=(0, 30))

        self.init_ui(center_frame)

    def init_ui(self, center_frame):
        # Şirketler Listesi (Scrollable)
        self.scroll_frame = ctk.CTkScrollableFrame(center_frame, width=400, height=300, corner_radius=15)
        self.scroll_frame.pack(pady=10)
        
        self.sirketleri_listele()

        # Yeni Şirket Ekleme Formu
        add_frame = ctk.CTkFrame(center_frame, corner_radius=15)
        add_frame.pack(fill="x", pady=20)
        
        self.e_yeni_sirket = ctk.CTkEntry(add_frame, placeholder_text="Yeni Şirket Adı", width=250)
        self.e_yeni_sirket.pack(side="left", padx=20, pady=20)
        
        btn_ekle = ctk.CTkButton(add_frame, text="+ Şirket Oluştur", command=self.yeni_sirket_olustur, width=100)
        btn_ekle.pack(side="right", padx=20, pady=20)

        # Alt Butonlar (Yedek İşlemleri)
        action_frame = ctk.CTkFrame(center_frame, fg_color="transparent")
        action_frame.pack(fill="x", pady=10)
        
        btn_veri = ctk.CTkButton(action_frame, text="⚙️ Yedekleme / Veri Yönetimi", command=self.ac_veri_yonetimi, fg_color="gray")
        btn_veri.pack(expand=True, padx=5, pady=10)

    def ac_veri_yonetimi(self):
        modal = VeriYonetimiModal(self.master_db, self)
        modal.grab_set()

    def sirketleri_listele(self):
        # Mevcut butonları temizle
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
            
        sirketler = self.master_db.tum_sirketleri_getir()
        
        if not sirketler:
            ctk.CTkLabel(self.scroll_frame, text="Henüz bir şirket tanımlanmamış.", text_color="gray").pack(pady=30)
            return

        for s in sirketler:
            s_id, s_adi, db_kodu = s
            
            row_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=10, pady=5)
            
            # Şirket Butonu
            btn = ctk.CTkButton(
                row_frame, 
                text=f"🏢 {s_adi}", 
                font=ctk.CTkFont(family="Segoe UI Emoji", size=16, weight="bold"),
                height=50,
                anchor="w",
                command=lambda adi=s_adi, db_file=db_kodu: self.on_sirket_secildi(adi, db_file)
            )
            btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
            
            # Düzenleme Butonu
            btn_duz = ctk.CTkButton(
                row_frame,
                text="✏️",
                width=40,
                height=50,
                fg_color="orange",
                hover_color="darkorange",
                command=lambda sid=s_id, sad=s_adi: self.sirket_duzenle_modal(sid, sad)
            )
            btn_duz.pack(side="left", padx=(0, 5))
            
            # Silme Butonu
            btn_sil = ctk.CTkButton(
                row_frame,
                text="❌",
                width=40,
                height=50,
                fg_color="#A02020",
                hover_color="#801010",
                command=lambda sid=s_id: self.sirket_sil_onayi(sid)
            )
            btn_sil.pack(side="right")

    def sirket_sil_onayi(self, sirket_id):
        if messagebox.askyesno("Onay", "Bu şirketi listeden silmek istediğinize emin misiniz? (Veritabanı dosyası silinmez, sadece listeden kaldırılır)"):
            if self.master_db.sirket_sil(sirket_id):
                self.sirketleri_listele()
            else:
                messagebox.showerror("Hata", "Silme işlemi başarısız.")

    def yeni_sirket_olustur(self):
        sirket_adi = self.e_yeni_sirket.get().strip()
        if not sirket_adi:
            messagebox.showwarning("Uyarı", "Lütfen bir şirket adı girin.")
            return
            
        import re
        safe_name = re.sub(r'[\\/*?:"<>|]', "", sirket_adi).strip()
        db_kodu = f"{safe_name}.db"
        if self.master_db.sirket_ekle(sirket_adi, db_kodu):
            self.e_yeni_sirket.delete(0, 'end')
            self.sirketleri_listele()
        else:
            messagebox.showerror("Hata", "Bu isimde bir şirket zaten var veya hata oluştu.")

    def sirket_duzenle_modal(self, sirket_id, eski_ad):
        p = ctk.CTkToplevel(self)
        p.title("Şirket İsmini Düzenle")
        p.geometry("350x180")
        p.grab_set()
        p.attributes("-topmost", True)

        ctk.CTkLabel(p, text="Yeni Şirket Adı:").pack(pady=(15,0))
        e_ad = ctk.CTkEntry(p, width=250)
        e_ad.insert(0, str(eski_ad))
        e_ad.pack(pady=10)

        def guncelle():
            y_ad = e_ad.get().strip()
            if not y_ad:
                messagebox.showerror("Hata", "Şirket adı boş olamaz!")
                return
            
            if self.master_db.sirket_guncelle(sirket_id, y_ad):
                messagebox.showinfo("Başarılı", "Şirket ismi güncellendi.")
                self.sirketleri_listele()
                p.destroy()
            else:
                messagebox.showerror("Hata", "Güncelleme sırasında sorun oluştu.")

        ctk.CTkButton(p, text="💾 Güncelle", command=guncelle).pack(pady=10)
