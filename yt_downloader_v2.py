import os
import sys
import threading
import tkinter as tk
from tkinter import messagebox, filedialog
import webbrowser
import subprocess
import tempfile
import time
import hashlib
import hmac
import platform
import json
import requests

# ============================================================
# KONFIGURACJA APLIKACJI
# ============================================================

LOG_FILE = os.path.join(tempfile.gettempdir(), "ytdownloader_debug.log")
CURRENT_VERSION = "3.0.0"  # Wersja z architekturą Klient-Serwer

# Adres URL serwera API. Zmienna środowiskowa lub domyślny lokalny serwer.
API_BASE_URL = os.environ.get("LICENSE_API_URL", "http://127.0.0.1:8000")

SECRET = "wzkL258k0tPdIAfpu1nwBKoLQQv+dZHby9tvrth7xI8="

def log_message(message):
    """Zapisuje wiadomość do pliku logów."""
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
    except Exception:
        pass

log_message("Application starting...")

# ============================================================
# FUNKCJE POMOCNICZE LICENCJI
# ============================================================

def get_machine_id():
    """Generuje unikalny identyfikator maszyny."""
    machine_info = f"{platform.node()}-{platform.machine()}-{platform.processor()}"
    return hashlib.md5(machine_info.encode()).hexdigest()[:16]

def get_local_license_path():
    """Zwraca ścieżkę do lokalnego pliku z kluczem licencji."""
    app_data = os.getenv("APPDATA") or os.path.expanduser("~")
    dir_path = os.path.join(app_data, "YTDownloaderMCP")
    os.makedirs(dir_path, exist_ok=True)
    return os.path.join(dir_path, "license.key")

def save_license_key(license_string):
    """Zapisuje klucz licencji lokalnie."""
    try:
        with open(get_local_license_path(), "w") as f:
            f.write(license_string)
        return True
    except Exception as e:
        log_message(f"Error saving license key: {e}")
        return False

def load_license_key():
    """Wczytuje klucz licencji z lokalnego pliku."""
    path = get_local_license_path()
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read().strip()
    return None

def verify_license_with_server(license_string, machine_id):
    """Wysyła prośbę o weryfikację licencji do serwera API."""
    url = f"{API_BASE_URL}/api/verify"
    try:
        signature, expires_str = license_string.split('.')
        expires = int(expires_str)
        
        payload = {'license_key': signature, 'machine_id': machine_id, 'expires': expires}
        response = requests.post(url, json=payload, timeout=15)
        
        if response.status_code == 200:
            return response.json()
        return {'valid': False, 'reason': f'server_status_{response.status_code}'}
    except requests.RequestException as e:
        log_message(f"API verification request failed: {e}")
        return {'valid': False, 'reason': 'connection_error'}
    except (ValueError, IndexError):
        return {'valid': False, 'reason': 'invalid_key_format'}

def get_trial_license_from_server(machine_id):
    """Prosi serwer o wygenerowanie licencji próbnej."""
    url = f"{API_BASE_URL}/api/generate_trial"
    try:
        payload = {'machine_id': machine_id, 'metadata': {'client_version': CURRENT_VERSION}}
        response = requests.post(url, json=payload, timeout=15)
        if response.status_code == 200:
            return response.json()
        return {'success': False, 'reason': f'server_status_{response.status_code}'}
    except requests.RequestException as e:
        log_message(f"API trial generation request failed: {e}")
        return {'success': False, 'reason': 'connection_error'}

def verify_license_local(machine_id, license_string):
    """Weryfikacja licencji offline przy użyciu HMAC-SHA256."""
    try:
        signature, expires_str = license_string.split('.')
        expires = int(expires_str)
    except (ValueError, IndexError):
        log_message("Offline license verification failed: invalid format")
        return False

    payload = f"{machine_id}|{expires}"
    expected_signature = hmac.new(
        SECRET.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    # Używamy hmac.compare_digest dla bezpieczeństwa
    if hmac.compare_digest(expected_signature, signature) and time.time() < expires:
        return True
    else:
        log_message("Offline license verification failed: signature or expiry mismatch")
        return False

# ============================================================
# GŁÓWNA FUNKCJA WERYFIKACJI LICENCJI
# ============================================================

def run_license_check():
    """Główna funkcja sprawdzająca licencję przy starcie."""
    machine_id = get_machine_id()
    print("--- Weryfikacja Licencji ---")
    print(f"Identyfikator maszyny: {machine_id}")
    print(f"Serwer API: {API_BASE_URL}")

    stored_key = load_license_key()
    
    if stored_key:
        print("Znaleziono zapisany klucz licencji. Weryfikuję...")
        result = verify_license_with_server(stored_key, machine_id)
        
        if result.get('valid'):
            print("✅ Licencja jest aktywna. Uruchamiam aplikację.")
            log_message("License verified successfully with stored key.")
            time.sleep(2)
            return True
        else:
            print(f"Weryfikacja serwerowa nie powiodła się (powód: {result.get('reason', 'nieznany')}).")
            log_message(f"Stored key validation failed via server: {result.get('reason')}")

            # 🔁 Fallback offline
            print("⚠️ Próbuję weryfikacji w trybie offline...")
            if verify_license_local(machine_id, stored_key):
                print("✅ Licencja poprawna (tryb offline). Uruchamiam aplikację.")
                log_message("License verified offline with stored key.")
                time.sleep(2)
                return True
            print("❌ Weryfikacja offline również nie powiodła się.")

    # Jeśli nie ma klucza lub jest nieprawidłowy, prosimy o nowy lub generujemy trial
    print("\nNie znaleziono aktywnej licencji lub istniejąca jest nieprawidłowa.")
    choice = input("Wpisz 'TRIAL' aby aktywować licencję próbną lub wklej swój klucz licencji: ").strip()

    if choice.upper() == 'TRIAL':
        print("Kontaktuję się z serwerem, aby uzyskać licencję próbną...")
        trial_result = get_trial_license_from_server(machine_id)
        if trial_result.get('success') and trial_result.get('license_key'):
            new_key = trial_result.get('license_key')
            save_license_key(new_key)
            print("✅ Licencja próbna aktywowana pomyślnie!")
            log_message(f"Trial license obtained and saved: {new_key}")
            time.sleep(2)
            return True
        else:
            print(f"❌ Nie udało się uzyskać licencji próbnej (powód: {trial_result.get('reason', 'nieznany')}).")
            log_message(f"Failed to get trial license: {trial_result.get('reason')}")
            time.sleep(4)
            return False
    else:
        # Użytkownik wkleił klucz
        if not choice:
            print("❌ Nie wprowadzono klucza. Zamykanie.")
            time.sleep(2)
            return False

        print("Weryfikuję podany klucz...")
        verify_result = verify_license_with_server(choice, machine_id)
        
        if verify_result.get('valid'):
            save_license_key(choice)
            print("✅ Licencja aktywowana pomyślnie!")
            log_message(f"New license validated and saved: {choice}")
            time.sleep(2)
            return True
        else:
            print(f"❌ Podany klucz jest nieprawidłowy lub serwer go odrzucił (powód: {verify_result.get('reason', 'nieznany')}).")
            log_message(f"User-provided key was invalid: {verify_result.get('reason')}")

            # 🔁 Fallback offline dla nowo wprowadzonego klucza
            print("⚠️ Próbuję weryfikacji w trybie offline...")
            if verify_license_local(machine_id, choice):
                save_license_key(choice)
                print("✅ Licencja poprawna (tryb offline). Aktywowano.")
                log_message("User-provided key verified offline and saved.")
                time.sleep(2)
                return True
            
            print("❌ Klucz nieprawidłowy również w trybie offline. Zamykanie aplikacji.")
            time.sleep(4)
            return False

# ============================================================
# GŁÓWNA APLIKACJA (GUI - bez zmian)
# ============================================================
import customtkinter

customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("blue")

class App(customtkinter.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Michal Code Project Downloader YT (mp3)")
        self.geometry("700x450")
        self.minsize(600, 400)

        main_frame = customtkinter.CTkFrame(self, corner_radius=10)
        main_frame.pack(expand=True, fill="both", padx=15, pady=15)

        license_label = customtkinter.CTkLabel(main_frame, text="🔓 Licencja Aktywna", font=("Helvetica", 10), text_color="gray60")
        license_label.pack(anchor="ne", padx=10, pady=5)

        url_frame = customtkinter.CTkFrame(main_frame, fg_color="transparent")
        url_frame.pack(fill="x", padx=10, pady=10)
        
        self.url_label = customtkinter.CTkLabel(url_frame, text="Link do wideo:")
        self.url_label.pack(side="left", padx=(0, 10))
        
        self.url_entry = customtkinter.CTkEntry(url_frame, placeholder_text="Wklej link do YouTube tutaj...")
        self.url_entry.pack(side="left", expand=True, fill="x")

        action_frame = customtkinter.CTkFrame(main_frame, fg_color="transparent")
        action_frame.pack(pady=20)
        
        self.download_button = customtkinter.CTkButton(action_frame, text="⬇ Pobierz MP3", command=self.start_download, height=45, width=200, font=("Helvetica", 15, "bold"), fg_color="purple", hover_color="#6b2c91")
        self.download_button.pack()

        self.progress_bar = customtkinter.CTkProgressBar(main_frame, height=15)
        self.progress_bar.pack(fill="x", padx=20, pady=10)
        self.progress_bar.set(0)

        self.progress_status_label = customtkinter.CTkLabel(main_frame, text="Gotowy do pobierania", text_color="gray60")
        self.progress_status_label.pack(pady=5)

        footer_frame = customtkinter.CTkFrame(main_frame, fg_color="transparent")
        footer_frame.pack(side="bottom", fill="x", padx=10, pady=5)
        
        facebook_url = "https://www.facebook.com/michal30081995"
        signature_label = customtkinter.CTkLabel(footer_frame, text="👤 Odwiedź mój profil na Facebooku", text_color="#4a90e2", font=("Helvetica", 11), cursor="hand2")
        signature_label.pack(side="right")
        signature_label.bind("<Button-1>", lambda e: self.open_link(facebook_url))

        version_label = customtkinter.CTkLabel(footer_frame, text=f"v{CURRENT_VERSION}", text_color="gray50", font=("Helvetica", 10))
        version_label.pack(side="left")

    def start_download(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Brak linku", "Proszę wkleić link do wideo YouTube.")
            return

        if "youtube.com" not in url and "youtu.be" not in url:
            messagebox.showwarning("Nieprawidłowy link", "Proszę wkleić prawidłowy link do YouTube.")
            return

        download_path = filedialog.askdirectory(title="Wybierz folder do zapisu pliku")
        if not download_path:
            return

        self.download_button.configure(state="disabled")
        self.progress_bar.set(0)
        self.progress_status_label.configure(text="Rozpoczynam pobieranie...")

        threading.Thread(target=self.download_audio_thread, args=(url, download_path), daemon=True).start()

    def download_audio_thread(self, url, download_path):
        try:
            self.update_status("Pobieranie informacji o wideo...", 0.1)
            
            try:
                import yt_dlp
            except ImportError:
                self.update_status("Błąd: Brak biblioteki yt-dlp!", 0)
                self.after(0, lambda: messagebox.showerror("Błąd", "Brak biblioteki yt-dlp."))
                self.after(0, lambda: self.download_button.configure(state="normal"))
                return

            def progress_hook(d):
                if d['status'] == 'downloading':
                    try:
                        percent = d.get('_percent_str', '0%').strip().replace('%', '')
                        progress = float(percent) / 100
                        self.update_status(f"Pobieranie: {d['_percent_str']}", progress)
                    except:
                        pass
                elif d['status'] == 'finished':
                    self.update_status("Konwertowanie do MP3...", 0.9)

            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
                'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
                'progress_hooks': [progress_hook],
                'quiet': True,
                'no_warnings': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            self.update_status("✓ Pobieranie zakończone!", 1.0)
            self.after(0, lambda: messagebox.showinfo("Sukces", f"Plik MP3 został zapisany w:\n{download_path}"))
            log_message(f"Download successful: {url}")

        except Exception as e:
            error_msg = str(e)
            log_message(f"Download error: {error_msg}")
            self.update_status(f"Błąd: {error_msg[:50]}...", 0)
            self.after(0, lambda: messagebox.showerror("Błąd pobierania", f"Nie udało się pobrać pliku:\n{error_msg}"))

        finally:
            self.after(0, lambda: self.download_button.configure(state="normal"))

    def update_status(self, text, progress):
        self.after(0, lambda: self.progress_status_label.configure(text=text))
        self.after(0, lambda: self.progress_bar.set(progress))

    def open_link(self, url):
        webbrowser.open_new(url)

# ============================================================
# PUNKT WEJŚCIA
# ============================================================

if __name__ == "__main__":
    if run_license_check():
        log_message("License check passed. Starting GUI.")
        app = App()
        app.mainloop()
    else:
        log_message("Application terminated - license check failed.")
        print("Weryfikacja licencji nie powiodła się. Aplikacja zostanie zamknięta.")
        sys.exit(1)
