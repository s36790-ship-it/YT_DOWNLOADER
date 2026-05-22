import os
import sys
import threading
import customtkinter as ctk
import yt_dlp

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FFMPEG_PATH = os.path.join(BASE_DIR, "ffmpeg.exe")

class YTDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Natywny YT Downloader")
        self.geometry("550x450")
        self.resizable(False, False)

        self.available_formats = {}

        self.title_label = ctk.CTkLabel(self, text="YouTube Downloader", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.pack(pady=20)

        self.url_label = ctk.CTkLabel(self, text="Wklej link do filmu:") 
        self.url_label.pack(pady=2)
        
        self.url_var = ctk.StringVar()
        self.url_var.trace_add("write", self.on_url_changed)
        
        self.url_entry = ctk.CTkEntry(self, textvariable=self.url_var, placeholder_text="https://www.youtube.com/watch?v=...", width=450)
        self.url_entry.pack(pady=5)

        self.res_label = ctk.CTkLabel(self, text="Dostępne rozdzielczości (Wklej link, aby załadować):", text_color="gray")
        self.res_label.pack(pady=10)
        
        self.res_combo = ctk.CTkComboBox(self, values=["Wklej link..."], width=220, state="disabled")
        self.res_combo.pack(pady=5)

        self.download_btn = ctk.CTkButton(self, text="Pobierz", command=self.start_download_thread, state="disabled")
        self.download_btn.pack(pady=25)

        self.status_label = ctk.CTkLabel(self, text="Status: Oczekiwanie na link...", text_color="gray", wraplength=500)
        self.status_label.pack(pady=5)

        self.progress_bar = ctk.CTkProgressBar(self, width=400)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)

    def on_url_changed(self, *args):
        """Uruchamia się automatycznie, gdy użytkownik wklei/wpisze coś do pola tekstowego"""
        url = self.url_var.get().strip()
        if "youtube.com/" in url or "youtu.be/" in url:
            self.status_label.configure(text="Status: Sprawdzanie dostępnych rozdzielczości...", text_color="blue")
            self.res_combo.configure(state="disabled", values=["Wczytywanie..."])
            self.res_combo.set("Wczytywanie...")
            self.download_btn.configure(state="disabled")
            
            threading.Thread(target=self.fetch_video_info, args=(url,), daemon=True).start()

    def fetch_video_info(self, url):
        """Pobiera metadane filmu bez ściągania samego wideo"""
        ydl_opts = {
            'ffmpeg_location': FFMPEG_PATH,
            'skip_download': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                formats = info_dict.get('formats', [])
                
                heights = set()
                for f in formats:
                    if f.get('vcodec') != 'none' and f.get('height'):
                        heights.add(f.get('height'))
                
                sorted_heights = sorted(list(heights), reverse=True)
                
                display_options = []
                for h in sorted_heights:
                    if h == 2160: display_options.append("2160p (4K)")
                    elif h == 1440: display_options.append("1440p (2K)")
                    elif h == 1080: display_options.append("1080p (FullHD)")
                    elif h == 720: display_options.append("720p (HD)")
                    elif h == 480: display_options.append("480p")
                    elif h == 360: display_options.append("360p")
                    else: display_options.append(f"{h}p")

                if display_options:
                    self.res_combo.configure(state="readonly", values=display_options)
                    self.res_combo.set(display_options[0])
                    self.download_btn.configure(state="normal")
                    self.res_label.configure(text="Wybierz jakość filmu (wykryto natywne formaty):", text_color="green")
                    self.status_label.configure(text="Status: Gotowy do pobrania.", text_color="green")
                else:
                    self.status_label.configure(text="Nie znaleziono odpowiednich formatów wideo.", text_color="red")

        except Exception as e:
            self.status_label.configure(text="Błąd: Nie udało się pobrać informacji o filmie.", text_color="red")
            self.res_combo.configure(state="disabled", values=["Błąd linku"])
            self.res_combo.set("Błąd linku")
            print(e)

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes', 0)
            if total > 0:
                percent = downloaded / total
                self.progress_bar.set(percent)
                self.status_label.configure(text=f"Pobieranie: {int(percent * 100)}%")
        elif d['status'] == 'finished':
            self.progress_bar.set(1.0)
            self.status_label.configure(text="Status: Łączenie audio i wideo (FFmpeg)...", text_color="orange")

    def download_video(self):
        url = self.url_entry.get().strip()
        selected_res_str = self.res_combo.get()

        target_res = selected_res_str.split()[0][:-1] 

        downloads_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
        
        ydl_opts = {
            'format': f'bestvideo[height={target_res}]+bestaudio/best[height={target_res}]',
            'outtmpl': os.path.join(downloads_dir, '%(title)s_%(height)sp.%(ext)s'),
            'progress_hooks': [self.progress_hook],
            'ffmpeg_location': FFMPEG_PATH,
        }

        try:
            self.status_label.configure(text="Status: Pobieranie filmu...", text_color="blue")
            self.download_btn.configure(state="disabled")
            self.progress_bar.set(0)
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
            self.status_label.configure(text="Sukces! Film zapisano w folderze Pobrane.", text_color="green")
        except Exception as e:
            self.status_label.configure(text="Błąd podczas pobierania!", text_color="red")
            print(e)
        finally:
            self.download_btn.configure(state="normal")

    def start_download_thread(self):
        threading.Thread(target=self.download_video, daemon=True).start()

if __name__ == "__main__":
    app = YTDownloaderApp()
    app.mainloop()