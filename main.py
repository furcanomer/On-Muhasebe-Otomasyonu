import customtkinter as ctk
from tkinter import ttk, messagebox
import logging
import os
import sys
from contextlib import contextmanager
from database import AppDatabase, MasterDatabase
from datetime import datetime, timedelta

def resource_path(relative_path):
    """ PyInstaller için dosya yolu yardımcısı """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Ayrı Dosyalardaki Arayüz Sınıflarını Dahil Etmek
from views.cari_view import CariView
from views.stok_view import StokView
from views.kasa_view import KasaView
from views.banka_view import BankaView
from views.fatura_view import FaturaView
from views.rapor_view import RaporView
from views.ayarlar_view import AyarlarView
from views.sirket_view import SirketSecimView
from views.calculator_view import CalculatorView
from views.takvim_view import TakvimView
from views.personel_view import PersonelView

# Log mekanizması
logging.basicConfig(
    filename='app_errors.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- MODERN UI AYARLARI ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class MuhasebeUygulamasi(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Ön Muhasebe Otomasyonu 1.6")
        self.geometry("1200x800")
        self.minsize(900, 600)
        
        # Uygulama ikonunu ayarla
        icon_path = resource_path(os.path.join("ikon", "app_icon.ico"))
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)
        
        self.master_db = MasterDatabase()
        
        # Kayıtlı temayı yükle
        current_theme = self.master_db.ayar_getir("tema", "Dark")
        ctk.set_appearance_mode(current_theme)
        
        # Tema için tablo stillerinin temaya uyarlanması
        self.after(100, self.apply_table_style)
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        self.sirket_secim_frame = None
        self.show_sirket_secim()
        
        # Global Kısayollar
        self.bind_all("<F2>", self._on_f2)
        self.bind_all("<F3>", self._on_f3)
        self.bind_all("<F4>", self._on_f4)
        self.bind_all("<Escape>", self._on_esc)
        self.bind_all("<Return>", self._on_enter)
        
        # Kapanışta Yedekleme
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _on_f2(self, event=None):
        frame = self.get_active_frame()
        if frame and hasattr(frame, "kaydet"): frame.kaydet()

    def _on_f3(self, event=None):
        frame = self.get_active_frame()
        if frame and hasattr(frame, "yeni_kayit"): frame.yeni_kayit()

    def _on_f4(self, event=None):
        frame = self.get_active_frame()
        if frame and hasattr(frame, "satir_ekle"): frame.satir_ekle()

    def _on_esc(self, event=None):
        # Eğer bir modal vs varsa kapatılabilir, şimdilik aktif sayfadaki kapat/iptal varsa çalıştır
        frame = self.get_active_frame()
        if frame and hasattr(frame, "kapat"): frame.kapat()

    def _on_enter(self, event):
        # Entry veya ComboBox ise bir sonraki widget'a odaklan
        widget = event.widget
        if isinstance(widget, (ctk.CTkEntry, ctk.CTkComboBox)):
            widget.tk_focusNext().focus()
            return "break" # Event'in yayılmasını durdur

    def get_active_frame(self):
        if hasattr(self, 'frames'):
            for name, frame in self.frames.items():
                if frame.winfo_viewable():
                    return frame
        return None

    def on_closing(self):
        if hasattr(self, 'db'):
            print("Yedekleme yapılıyor...")
            self.db.yedekle()
        self.destroy()

    @contextmanager
    def islem_bekle(self, mesaj="İşlem yapılıyor, lütfen bekleyin..."):
        # Kullanıcı isteği üzerine bekleme ekranı devre dışı bırakıldı
        try:
            yield
        finally:
            pass

    def show_sirket_secim(self):
        if hasattr(self, 'sidebar_frame') and self.sidebar_frame: 
            self.sidebar_frame.grid_forget()
        if hasattr(self, 'main_frame') and self.main_frame: 
            self.main_frame.grid_forget()
        
        self.sirket_secim_frame = SirketSecimView(self, self.master_db, self.on_sirket_secildi)
        self.sirket_secim_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")

    def on_sirket_secildi(self, sirket_adi, db_kodu):
        if self.sirket_secim_frame:
            self.sirket_secim_frame.grid_forget()
            
        self.title(f"Ön Muhasebe Otomasyonu 1.6 - {sirket_adi}")
        self.db = AppDatabase(db_kodu)
        
        self.create_sidebar()
        self.create_main_content_area()
        self.show_frame("Cari")
        
        # Akıllı Takvim Kontrolü (Açılışta)
        self.after(1000, self.takvim_kontrol_et)

    def takvim_kontrol_et(self):
        try:
            bugun = datetime.now().strftime("%Y-%m-%d")
            yarin = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            etkinlikler = self.db.etkinlikleri_getir()
            # Sütun sırası: id=0, baslik=1, aciklama=2, tarih=3, saat=4, oncelik=5
            bugun_liste = [e for e in etkinlikler if str(e[3]) == bugun]
            yarin_liste  = [e for e in etkinlikler if str(e[3]) == yarin]
            
            if bugun_liste:
                msg = "Bugün için hatırlatmalarınız var:\n"
                for e in bugun_liste:
                    msg += f"- {e[1]} ({e[4]})\n"
                messagebox.showinfo("📌 Günlük Hatırlatıcı", msg)
                
            if yarin_liste:
                n = len(yarin_liste)
                self.after(2000, lambda: messagebox.showinfo("📅 Yarın İçin Not", f"Yarın için {n} adet planlanmış işiniz var."))
        except Exception as e:
            logging.error(f"Takvim kontrolü hatası: {e}")
    def show_calculator(self):
        CalculatorView(self)

    def apply_table_style(self):
        """Standart tkinter tablolarını (Treeview) seçili temaya uyarlar."""
        appearance = ctk.get_appearance_mode() # "Dark" veya "Light"
        
        # customtkinter.get_appearance_mode() bazen geç güncellenebilir, 
        # bu yüzden doğrudan sistem ayarını kontrol etmek daha güvenlidir ama ctk üzerinden ilerleyelim.
        
        bg_color = "#333333" if appearance == "Dark" else "#FFFFFF"
        fg_color = "white" if appearance == "Dark" else "black"
        head_bg = "#222222" if appearance == "Dark" else "#E5E5E5"
        head_fg = "white" if appearance == "Dark" else "black"
        selected_bg = "#1f538d" if appearance == "Dark" else "#0078d4"
        
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview",
                        background=bg_color,
                        foreground=fg_color,
                        rowheight=35,
                        fieldbackground=bg_color,
                        borderwidth=0)
        style.map('Treeview', background=[('selected', selected_bg)])
        
        style.configure("Treeview.Heading",
                        background=head_bg,
                        foreground=head_fg,
                        font=("Segoe UI Emoji", 11, "bold"),
                        relief="flat")
        style.map("Treeview.Heading", background=[('active', selected_bg)])

        style.configure("Treeview", font=("Segoe UI Emoji", 11))

    def create_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        # Satır 10 (Hesap Makinesi ve Şirket Değiştir arası boşluk) ağırlıklı genişlesin
        self.sidebar_frame.grid_rowconfigure(10, weight=1)
        
        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Ön Muhasebe\nOtomasyonu 1.6", 
            font=ctk.CTkFont(family="Segoe UI Emoji", size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 20))
        
        btn_params = {
            "corner_radius": 8, "height": 50, "border_spacing": 15,
            "fg_color": "transparent", "text_color": ("gray10", "gray90"),
            "hover_color": ("gray70", "gray30"), "anchor": "w",
            "font": ctk.CTkFont(family="Segoe UI Emoji", size=17)
        }
        
        ctk.CTkButton(self.sidebar_frame, text="👥 Cari Yönetimi", command=lambda: self.show_frame("Cari"), **btn_params).grid(row=1, column=0, padx=15, pady=5, sticky="ew")
        ctk.CTkButton(self.sidebar_frame, text="📦 Stok/Envanter", command=lambda: self.show_frame("Stok"), **btn_params).grid(row=2, column=0, padx=15, pady=5, sticky="ew")
        ctk.CTkButton(self.sidebar_frame, text="💰 Kasa Yönetimi", command=lambda: self.show_frame("Kasa"), **btn_params).grid(row=3, column=0, padx=15, pady=5, sticky="ew")
        ctk.CTkButton(self.sidebar_frame, text="🏦 Banka Yönetimi", command=lambda: self.show_frame("Banka"), **btn_params).grid(row=4, column=0, padx=15, pady=5, sticky="ew")
        ctk.CTkButton(self.sidebar_frame, text="📄 Merkezi Evrak", command=lambda: self.show_frame("Fatura"), **btn_params) .grid(row=5, column=0, padx=15, pady=5, sticky="ew")
        ctk.CTkButton(self.sidebar_frame, text="📊 Raporlama", command=lambda: self.show_frame("Rapor"), **btn_params).grid(row=6, column=0, padx=15, pady=5, sticky="ew")
        
        # Yeni Modüller
        ctk.CTkButton(self.sidebar_frame, text="📅 Akıllı Takvim", command=lambda: self.show_frame("Takvim"), **btn_params).grid(row=7, column=0, padx=15, pady=5, sticky="ew")
        ctk.CTkButton(self.sidebar_frame, text="👤 Personel Takibi", command=lambda: self.show_frame("Personel"), **btn_params).grid(row=8, column=0, padx=15, pady=5, sticky="ew")
        ctk.CTkButton(self.sidebar_frame, text="🧮 Hesap Makinesi", command=self.show_calculator, 
                      fg_color="#34495e", hover_color="#2c3e50", height=40, font=ctk.CTkFont(size=14)).grid(row=9, column=0, padx=15, pady=(20, 5), sticky="ew")
        
        # Şirket Değiştir
        ctk.CTkButton(self.sidebar_frame, text="🔄 Şirket Değiştir", command=self.show_sirket_secim, **btn_params).grid(row=11, column=0, padx=15, pady=(20, 5), sticky="ew")
        
        # Ayarlar butonu en altta
        ctk.CTkButton(self.sidebar_frame, text="⚙️ Ayarlar", command=lambda: self.show_frame("Ayarlar"), **btn_params).grid(row=12, column=0, padx=15, pady=(5, 20), sticky="ew")

    def create_main_content_area(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        self.frames = {
            "Cari": CariView(self.main_frame, self.db),
            "Stok": StokView(self.main_frame, self.db),
            "Kasa": KasaView(self.main_frame, self.db),
            "Banka": BankaView(self.main_frame, self.db),
            "Fatura": FaturaView(self.main_frame, self.db),
            "Rapor": RaporView(self.main_frame, self.db),
            "Takvim": TakvimView(self.main_frame, self.db),
            "Personel": PersonelView(self.main_frame, self.db),
            "Ayarlar": AyarlarView(self.main_frame, self.master_db, self)
        }

    def show_frame(self, frame_name):
        for frame in self.frames.values():
            frame.grid_forget()
            
        self.frames[frame_name].grid(row=0, column=0, sticky="nsew")
        
        # Sayfa değiştiğinde verilerin yenilenmesini sağla (Dinamik güncelleme için)
        if hasattr(self.frames[frame_name], 'tabloyu_guncelle'):
            self.frames[frame_name].tabloyu_guncelle()
        elif hasattr(self.frames[frame_name], 'gosterge_paneli_guncelle'):
            self.frames[frame_name].gosterge_paneli_guncelle()

if __name__ == "__main__":
    try:
        app = MuhasebeUygulamasi()
        app.mainloop()
    except Exception as e:
        logging.critical(f"Kritik Arayüz Hatası (UI): {str(e)}")
        print(f"Uygulama başlatılırken hata oluştu: {e}")
