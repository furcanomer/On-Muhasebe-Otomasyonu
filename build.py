
import os
import shutil
import subprocess
import sys

def build_app():
    # 1. Klasör Yapısını Hazırla
    build_dir = "derlenmiş dosyalar"
    icon_dir = "ikon"
    icon_name = "app_icon.ico"
    icon_path = os.path.join(icon_dir, icon_name)
    
    print("--- Ön Muhasebe Otomasyonu 1.6 Build Süreci Başladı ---")
    
    # 2. Temizlik
    if os.path.exists(build_dir):
        print(f"'{build_dir}' klasörü temizleniyor...")
        shutil.rmtree(build_dir)
    os.makedirs(build_dir)
    
    # 3. PyInstaller Komutunu Hazırla
    # --onefile: Tek EXE
    # --windowed: Konsolsuz
    # --icon: Uygulama ikonu
    # --distpath: Final EXE'nin gideceği yer
    # --workpath: Geçici build dosyalarının gideceği yer
    # --specpath: .spec dosyasının gideceği yer
    
    separator = ";" if sys.platform == "win32" else ":"
    
    work_dir = os.path.abspath(os.path.join(build_dir, "build_temp"))
    abs_icon_dir = os.path.abspath(icon_dir)
    
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        f"--icon={os.path.abspath(icon_path)}",
        f"--distpath={os.path.abspath(build_dir)}",
        f"--workpath={work_dir}",
        f"--specpath={os.path.abspath(build_dir)}",
        f"--add-data={abs_icon_dir}{separator}{icon_dir}",
        "--name=On_Muhasebe_1.6",
        "--noconfirm", # Onay bekleme
        "main.py"
    ]
    
    print("Derleme işlemi yapılıyor (PyInstaller)...")
    try:
        subprocess.run(cmd, check=True)
        print("\nSUCCESS: Derleme başarıyla tamamlandı.")
        print(f"Bütün çıktılar '{build_dir}' klasöründedir.")
    except subprocess.CalledProcessError as e:
        print(f"\nERROR: Derleme sırasında hata oluştu: {e}")
    except FileNotFoundError:
        print("\nERROR: PyInstaller bulunamadı. Lütfen 'pip install pyinstaller' komutu ile yükleyin.")

if __name__ == "__main__":
    build_app()
