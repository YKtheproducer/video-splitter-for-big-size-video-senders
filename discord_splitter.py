import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os, sys, math, threading, pathlib, subprocess, glob, re, shutil

# ─── Tema ───────────────────────────────────────────────────────
BG      = "#0d0d1a"
CARD    = "#16213e"
BORDER  = "#1a1a3e"
ACCENT  = "#5865f2"
ACCENT2 = "#7289da"
SUCCESS = "#57f287"
DANGER  = "#ed4245"
WARN    = "#fee75c"
TEXT    = "#dcddde"
SUB     = "#8e9297"
HOVER   = "#4752c4"
WHITE   = "#ffffff"

DISCORD_LIMIT_MB = 49

# Çözünürlük merdiveni: (genişlik, yükseklik, etiket, min_kbps)
RES_LADDER = [
    (3840, 2160, "4K",    15000),
    (2560, 1440, "1440p",  8000),
    (1920, 1080, "1080p",  4000),
    (1280,  720, "720p",   2000),
    ( 854,  480, "480p",    800),
    ( 640,  360, "360p",    400),
    ( 426,  240, "240p",      0),
]


class DiscordBolucu:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("🎮 Discord Dosya Bölücü & Birleştirici")
        self.root.geometry("560x590")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        self.secili_dosyalar: list[str] = []
        self.birlestir_dosya: str | None = None
        self.res_dosyalar: list[str] = []
        self.is_running = False

        # FFmpeg kontrolü
        self.ffmpeg_path = shutil.which("ffmpeg")
        self.ffmpeg_ok   = self.ffmpeg_path is not None

        self._style()
        self._ui()

    # ════════════════════════════════════════════════════════════
    #  STİL
    # ════════════════════════════════════════════════════════════
    def _style(self):
        s = ttk.Style()
        s.theme_use("clam")
        for name, color in [("Split", ACCENT), ("Merge", SUCCESS), ("Res", WARN)]:
            s.configure(f"{name}.Horizontal.TProgressbar",
                        troughcolor=BORDER, background=color,
                        borderwidth=0, thickness=16, relief="flat")
        s.configure("TNotebook", background=BG, borderwidth=0)
        s.configure("TNotebook.Tab",
                    background=CARD, foreground=SUB,
                    font=("Segoe UI", 11, "bold"), padding=(14, 8))
        s.map("TNotebook.Tab",
              background=[("selected", ACCENT)],
              foreground=[("selected", WHITE)])

    # ════════════════════════════════════════════════════════════
    #  ANA UI
    # ════════════════════════════════════════════════════════════
    def _ui(self):
        tk.Label(self.root,
                 text="🎮  Discord Dosya Bölücü & Birleştirici",
                 font=("Segoe UI", 15, "bold"),
                 bg=BG, fg=TEXT).pack(pady=(20, 8))

        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        self.tab_bol = tk.Frame(nb, bg=BG)
        nb.add(self.tab_bol, text="✂️  Böl")
        self._tab_bol()

        self.tab_bir = tk.Frame(nb, bg=BG)
        nb.add(self.tab_bir, text="🔗  Birleştir")
        self._tab_birlestir()

        self.tab_res = tk.Frame(nb, bg=BG)
        nb.add(self.tab_res, text="📉  Sıkıştır")
        self._tab_cozunurluk()

    # ════════════════════════════════════════════════════════════
    #  TAB 1 — BÖL
    # ════════════════════════════════════════════════════════════
    def _tab_bol(self):
        p = self.tab_bol

        self.bol_card = self._kart(p)
        self.bol_card.pack(fill="x", padx=16, pady=(16, 0), ipady=12)

        self.bol_icon = tk.Label(self.bol_card, text="📂",
                                 font=("Segoe UI Emoji", 32),
                                 bg=CARD, fg=ACCENT2)
        self.bol_icon.pack(pady=(8, 3))

        self.bol_hint = tk.Label(self.bol_card,
                                 text="Dosya(ları) seçmek için tıklayın",
                                 font=("Segoe UI", 10), bg=CARD, fg=SUB)
        self.bol_hint.pack()

        self.bol_liste_lbl = tk.Label(self.bol_card, text="",
                                      font=("Segoe UI", 9, "bold"),
                                      bg=CARD, fg=SUCCESS,
                                      wraplength=460, justify="center")
        self.bol_liste_lbl.pack(pady=(3, 0))

        self._kart_tikla(self.bol_card,
                         [self.bol_icon, self.bol_hint, self.bol_liste_lbl],
                         self.dosya_sec_bol, ACCENT2)

        # Boyut spinbox
        row = tk.Frame(p, bg=BG)
        row.pack(fill="x", padx=16, pady=(12, 0))
        tk.Label(row, text="Maksimum parça boyutu:",
                 font=("Segoe UI", 10), bg=BG, fg=SUB).pack(side="left")
        self.size_var = tk.IntVar(value=DISCORD_LIMIT_MB)
        tk.Spinbox(row, from_=1, to=999, textvariable=self.size_var, width=5,
                   font=("Segoe UI", 10, "bold"),
                   bg=CARD, fg=TEXT, buttonbackground=BORDER,
                   relief="flat", bd=2).pack(side="left", padx=8)
        tk.Label(row, text="MB  (ücretsiz=25 · Nitro=500)",
                 font=("Segoe UI", 9), bg=BG, fg=SUB).pack(side="left")

        self.bol_prog_lbl, self.bol_prog, self.bol_pct = self._progress_row(p, "Split")
        self.bol_btn = self._buton(p, "✂️  Böl & Kaydet", ACCENT, self.baslat_bol)
        self.bol_btn.pack(pady=16)
        tk.Label(p, text="Parçalar masaüstünde  <isim>_parcalar  klasörüne gider",
                 font=("Segoe UI", 9), bg=BG, fg=SUB).pack()

    # ════════════════════════════════════════════════════════════
    #  TAB 2 — BİRLEŞTİR
    # ════════════════════════════════════════════════════════════
    def _tab_birlestir(self):
        p = self.tab_bir

        self.bir_card = self._kart(p)
        self.bir_card.pack(fill="x", padx=16, pady=(16, 0), ipady=12)

        self.bir_icon = tk.Label(self.bir_card, text="🗂️",
                                 font=("Segoe UI Emoji", 32),
                                 bg=CARD, fg=SUCCESS)
        self.bir_icon.pack(pady=(8, 3))

        self.bir_hint = tk.Label(self.bir_card,
                                 text="Herhangi bir parçayı (.part001) seçin",
                                 font=("Segoe UI", 10), bg=CARD, fg=SUB)
        self.bir_hint.pack()

        self.bir_dosya_lbl = tk.Label(self.bir_card, text="",
                                      font=("Segoe UI", 9, "bold"),
                                      bg=CARD, fg=SUCCESS, wraplength=460)
        self.bir_dosya_lbl.pack(pady=(3, 0))

        self._kart_tikla(self.bir_card,
                         [self.bir_icon, self.bir_hint, self.bir_dosya_lbl],
                         self.dosya_sec_birlestir, SUCCESS)

        self.bir_prog_lbl, self.bir_prog, self.bir_pct = self._progress_row(p, "Merge")
        self.bir_btn = self._buton(p, "🔗  Birleştir", SUCCESS, self.baslat_birlestir)
        self.bir_btn.pack(pady=16)
        tk.Label(p, text="Birleştirilen dosya parçaların bulunduğu klasöre kaydedilir",
                 font=("Segoe UI", 9), bg=BG, fg=SUB).pack()

    # ════════════════════════════════════════════════════════════
    #  TAB 3 — ÇÖZÜNÜRLÜK DÜŞÜR / SIKIŞIR
    # ════════════════════════════════════════════════════════════
    def _tab_cozunurluk(self):
        p = self.tab_res

        # FFmpeg uyarısı
        if not self.ffmpeg_ok:
            uf = tk.Frame(p, bg="#2d1a00")
            uf.pack(fill="x", padx=16, pady=(12, 0))
            tk.Label(uf, text="⚠️  FFmpeg bulunamadı — bu sekme için gerekli!",
                     font=("Segoe UI", 9, "bold"),
                     bg="#2d1a00", fg=WARN).pack(anchor="w", padx=10, pady=(7, 0))
            tk.Label(uf,
                     text="① ffmpeg.org/download.html → indir\n"
                          "② ffmpeg.exe klasörünü PATH'e ekle veya bu .py ile aynı dizine koy",
                     font=("Segoe UI", 9), bg="#2d1a00", fg=TEXT,
                     justify="left").pack(anchor="w", padx=10, pady=(2, 8))

        # Dosya kartı
        self.res_card = self._kart(p)
        self.res_card.pack(fill="x", padx=16, pady=(12, 0), ipady=10)

        self.res_icon = tk.Label(self.res_card, text="🎬",
                                 font=("Segoe UI Emoji", 32),
                                 bg=CARD, fg=WARN)
        self.res_icon.pack(pady=(6, 3))

        self.res_hint = tk.Label(self.res_card, text="Video dosyası(larını) seçin",
                                 font=("Segoe UI", 10), bg=CARD, fg=SUB)
        self.res_hint.pack()

        self.res_dosya_lbl = tk.Label(self.res_card, text="",
                                      font=("Segoe UI", 9, "bold"),
                                      bg=CARD, fg=SUCCESS,
                                      wraplength=460, justify="center")
        self.res_dosya_lbl.pack(pady=(2, 0))

        self.res_info_lbl = tk.Label(self.res_card, text="",
                                     font=("Segoe UI", 9),
                                     bg=CARD, fg=WARN)
        self.res_info_lbl.pack(pady=(2, 0))

        self._kart_tikla(self.res_card,
                         [self.res_icon, self.res_hint,
                          self.res_dosya_lbl, self.res_info_lbl],
                         self.dosya_sec_res, WARN)

        # Hedef boyut
        row2 = tk.Frame(p, bg=BG)
        row2.pack(fill="x", padx=16, pady=(12, 0))
        tk.Label(row2, text="Hedef maksimum boyut:",
                 font=("Segoe UI", 10), bg=BG, fg=SUB).pack(side="left")
        self.res_size_var = tk.IntVar(value=DISCORD_LIMIT_MB)
        tk.Spinbox(row2, from_=1, to=9999,
                   textvariable=self.res_size_var, width=6,
                   font=("Segoe UI", 10, "bold"),
                   bg=CARD, fg=TEXT, buttonbackground=BORDER,
                   relief="flat", bd=2).pack(side="left", padx=8)
        tk.Label(row2, text="MB",
                 font=("Segoe UI", 10), bg=BG, fg=SUB).pack(side="left")

        self.res_prog_lbl, self.res_prog, self.res_pct = self._progress_row(p, "Res")

        self.res_btn = self._buton(p, "📉  Sıkıştır", WARN, self.baslat_res)
        self.res_btn.config(fg="#000000", activeforeground="#000000")
        self.res_btn.pack(pady=14)
        tk.Label(p,
                 text="Çıktı masaüstüne  <isim>_siki.mp4  olarak kaydedilir",
                 font=("Segoe UI", 9), bg=BG, fg=SUB).pack()

    # ════════════════════════════════════════════════════════════
    #  DOSYA SEÇİM
    # ════════════════════════════════════════════════════════════
    def dosya_sec_bol(self, _=None):
        if self.is_running:
            return
        d = filedialog.askopenfilenames(title="Dosya(ları) Seç")
        if not d:
            return
        self.secili_dosyalar = list(d)
        isimler = "\n".join(
            f"• {os.path.basename(x)}  ({os.path.getsize(x)/1e6:.1f} MB)"
            for x in self.secili_dosyalar)
        self.bol_icon.config(text="✅")
        self.bol_hint.config(text=f"{len(self.secili_dosyalar)} dosya seçildi:")
        self.bol_liste_lbl.config(text=isimler)
        self._sifirla_prog(self.bol_prog, self.bol_prog_lbl, self.bol_pct)

    def dosya_sec_birlestir(self, _=None):
        if self.is_running:
            return
        d = filedialog.askopenfilename(
            title="Herhangi bir parçayı seç",
            filetypes=[("Parça dosyaları", "*.part*"), ("Tüm dosyalar", "*.*")])
        if not d:
            return
        self.birlestir_dosya = d
        self.bir_icon.config(text="✅")
        self.bir_hint.config(text="Seçilen parça:")
        self.bir_dosya_lbl.config(text=os.path.basename(d))
        self._sifirla_prog(self.bir_prog, self.bir_prog_lbl, self.bir_pct)

    def dosya_sec_res(self, _=None):
        if self.is_running:
            return
        d = filedialog.askopenfilenames(
            title="Video Seç",
            filetypes=[
                ("Video", "*.mp4 *.mkv *.avi *.mov *.wmv *.flv *.webm *.m4v"),
                ("Tüm dosyalar", "*.*")])
        if not d:
            return
        self.res_dosyalar = list(d)
        isimler = "\n".join(
            f"• {os.path.basename(x)}  ({os.path.getsize(x)/1e6:.1f} MB)"
            for x in self.res_dosyalar)
        self.res_icon.config(text="✅")
        self.res_hint.config(text=f"{len(self.res_dosyalar)} video seçildi:")
        self.res_dosya_lbl.config(text=isimler)

        # Tek dosyaysa bilgi göster
        if self.ffmpeg_ok and len(self.res_dosyalar) == 1:
            info = self._video_bilgisi(self.res_dosyalar[0])
            if info:
                dur, w, h = info
                self.res_info_lbl.config(
                    text=f"📐 {w}×{h}  ⏱ {int(dur//60)}:{int(dur%60):02d}  "
                         f"📦 {os.path.getsize(self.res_dosyalar[0])/1e6:.1f} MB")
        else:
            self.res_info_lbl.config(text="")
        self._sifirla_prog(self.res_prog, self.res_prog_lbl, self.res_pct)

    # ════════════════════════════════════════════════════════════
    #  BÖLME
    # ════════════════════════════════════════════════════════════
    def baslat_bol(self):
        if self.is_running:
            return
        if not self.secili_dosyalar:
            messagebox.showwarning("Uyarı", "Önce dosya seçin!")
            return
        self._kilit(self.bol_btn, "⏳  İşleniyor…")
        threading.Thread(target=self._bol_worker, daemon=True).start()

    def _bol_worker(self):
        try:
            max_bytes  = self.size_var.get() * 1024 * 1024
            masaustu   = self._masaustu()
            toplam_d   = len(self.secili_dosyalar)

            for di, dosya in enumerate(self.secili_dosyalar):
                isim = pathlib.Path(dosya).name
                stem = pathlib.Path(dosya).stem
                klasor = masaustu / f"{stem}_parcalar"
                klasor.mkdir(parents=True, exist_ok=True)

                boyut = os.path.getsize(dosya)
                parca_n = math.ceil(boyut / max_bytes)

                with open(dosya, "rb") as f:
                    for i in range(parca_n):
                        veri = f.read(max_bytes)
                        with open(klasor / f"{isim}.part{i+1:03d}", "wb") as pf:
                            pf.write(veri)
                        pct = ((di + (i+1)/parca_n) / toplam_d) * 100
                        self._prog_set(self.bol_prog, self.bol_prog_lbl, self.bol_pct,
                                       pct, f"[{di+1}/{toplam_d}] Parça {i+1}/{parca_n}")

            self.root.after(0, lambda: self._bol_tamam(masaustu))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Hata", str(e)))
            self.root.after(0, lambda: self._serbest(self.bol_btn, "✂️  Böl & Kaydet"))

    def _bol_tamam(self, masaustu):
        self._prog_set(self.bol_prog, self.bol_prog_lbl, self.bol_pct,
                       100, f"✅ {len(self.secili_dosyalar)} dosya bölündü!")
        self._serbest(self.bol_btn, "✂️  Böl & Kaydet")
        stem = pathlib.Path(self.secili_dosyalar[0]).stem
        klasor = str(masaustu / f"{stem}_parcalar")
        messagebox.showinfo("Tamamlandı",
                            f"Bölme tamamlandı! 🎉\n\n📁  {klasor}\n\n"
                            "Karşı taraf 'Birleştir' sekmesiyle birleştirebilir.")
        self._klasor_ac(klasor)

    # ════════════════════════════════════════════════════════════
    #  BİRLEŞTİRME
    # ════════════════════════════════════════════════════════════
    def baslat_birlestir(self):
        if self.is_running:
            return
        if not self.birlestir_dosya:
            messagebox.showwarning("Uyarı", "Önce parça dosyası seçin!")
            return
        self._kilit(self.bir_btn, "⏳  Birleştiriliyor…")
        threading.Thread(target=self._bir_worker, daemon=True).start()

    def _bir_worker(self):
        try:
            secili  = pathlib.Path(self.birlestir_dosya)
            klasor  = secili.parent
            adi     = secili.name
            taban   = adi[:adi.rfind(".part")] if ".part" in adi else adi
            parcalar = sorted(glob.glob(str(klasor / f"{taban}.part*")))

            if not parcalar:
                raise FileNotFoundError(f"Parça bulunamadı: {taban}.part*")

            toplam  = len(parcalar)
            cikti   = klasor / taban

            with open(cikti, "wb") as out:
                for i, p in enumerate(parcalar):
                    with open(p, "rb") as pf:
                        out.write(pf.read())
                    self._prog_set(self.bir_prog, self.bir_prog_lbl, self.bir_pct,
                                   ((i+1)/toplam)*100, f"Parça {i+1}/{toplam}")

            self.root.after(0, lambda: self._bir_tamam(str(cikti), toplam))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Hata", str(e)))
            self.root.after(0, lambda: self._serbest(self.bir_btn, "🔗  Birleştir"))

    def _bir_tamam(self, cikti, toplam):
        self._prog_set(self.bir_prog, self.bir_prog_lbl, self.bir_pct,
                       100, f"✅ {toplam} parça birleştirildi!")
        self._serbest(self.bir_btn, "🔗  Birleştir")
        messagebox.showinfo("Tamamlandı", f"Dosya birleştirildi! 🎉\n\n📄  {cikti}")
        self._klasor_ac(str(pathlib.Path(cikti).parent))

    # ════════════════════════════════════════════════════════════
    #  ÇÖZÜNÜRLÜK / SIKISTIRMA
    # ════════════════════════════════════════════════════════════
    def baslat_res(self):
        if self.is_running:
            return
        if not self.ffmpeg_ok:
            messagebox.showerror("FFmpeg Gerekli",
                                 "FFmpeg kurulu değil.\n\n"
                                 "ffmpeg.org/download.html → indir → PATH'e ekle")
            return
        if not self.res_dosyalar:
            messagebox.showwarning("Uyarı", "Önce video seçin!")
            return
        self._kilit(self.res_btn, "⏳  İşleniyor…")
        threading.Thread(target=self._res_worker, daemon=True).start()

    def _res_worker(self):
        try:
            target_mb = self.res_size_var.get()
            masaustu  = self._masaustu()
            toplam    = len(self.res_dosyalar)

            for idx, dosya in enumerate(self.res_dosyalar):
                isim  = pathlib.Path(dosya).stem
                cikti = masaustu / f"{isim}_siki.mp4"

                self._prog_set(self.res_prog, self.res_prog_lbl, self.res_pct,
                               0, f"[{idx+1}/{toplam}] Video analiz ediliyor…")

                info = self._video_bilgisi(dosya)
                if not info:
                    self.root.after(0, lambda d=dosya: messagebox.showerror(
                        "Hata", f"Video bilgisi alınamadı:\n{d}"))
                    continue

                duration, orig_w, orig_h = info

                if duration <= 0:
                    self.root.after(0, lambda: messagebox.showerror(
                        "Hata", "Video süresi okunamadı!"))
                    continue

                # ── Hedef bitrate hesapla ──────────────────────
                # %92 güvenlik marjı bırak (ffmpeg tam tutturamayabilir)
                target_bytes   = target_mb * 1024 * 1024 * 0.92
                total_kbps     = (target_bytes * 8) / duration / 1000
                audio_kbps     = 128
                video_kbps     = max(int(total_kbps - audio_kbps), 80)

                # ── En uygun çözünürlüğü seç ──────────────────
                chosen_w, chosen_h, label = self._sec_cozunurluk(
                    video_kbps, orig_w, orig_h)

                self._prog_set(self.res_prog, self.res_prog_lbl, self.res_pct,
                               2,
                               f"[{idx+1}/{toplam}] {label} @ {video_kbps} kbps — kodlanıyor…")

                ok = self._encode(dosya, str(cikti), chosen_w, video_kbps, duration,
                                  idx, toplam)

                if ok and cikti.exists():
                    final_mb = cikti.stat().st_size / 1e6
                    msg = (f"✅ Sıkıştırma tamamlandı!\n\n"
                           f"📹  {os.path.basename(dosya)}\n"
                           f"📐  {orig_w}×{orig_h}  →  {chosen_w}×{chosen_h} ({label})\n"
                           f"📦  {os.path.getsize(dosya)/1e6:.1f} MB  →  {final_mb:.1f} MB\n\n"
                           f"💾  {cikti}")
                    self.root.after(0, lambda m=msg: messagebox.showinfo("Tamamlandı", m))
                else:
                    self.root.after(0, lambda: messagebox.showerror(
                        "Hata", "FFmpeg kodlaması başarısız oldu."))

            self.root.after(0, lambda: self._res_bitti(masaustu))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Hata", str(e)))
            self.root.after(0, lambda: self._serbest(self.res_btn, "📉  Sıkıştır"))

    def _sec_cozunurluk(self, video_kbps: int,
                        orig_w: int, orig_h: int) -> tuple[int, int, str]:
        """Bitrate'e ve orijinal çözünürlüğe göre en uygun hedefi seç."""
        for w, h, label, min_kbps in RES_LADDER:
            # Orijinalden büyük ölçekleme yok
            if w > orig_w or h > orig_h:
                continue
            if video_kbps >= min_kbps:
                return w, h, label
        # En küçük seçenek
        return min(426, orig_w), min(240, orig_h), "240p"

    # ── FFmpeg ile kodla ──────────────────────────────────────
    def _encode(self, input_f: str, output_f: str,
                width: int, video_kbps: int, duration_s: float,
                idx: int, toplam: int) -> bool:
        cmd = [
            self.ffmpeg_path, "-y", "-i", input_f,
            "-vf", f"scale={width}:-2",
            "-c:v", "libx264", "-preset", "fast",
            "-b:v", f"{video_kbps}k",
            "-maxrate", f"{int(video_kbps * 1.5)}k",
            "-bufsize", f"{video_kbps * 2}k",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            output_f,
        ]
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True, encoding="utf-8", errors="replace",
            )
            for line in proc.stderr:
                m = re.search(r"time=(\d+):(\d+):(\d+\.?\d*)", line)
                if m:
                    cur = int(m.group(1))*3600 + int(m.group(2))*60 + float(m.group(3))
                    pct = min((cur / duration_s) * 100, 99) if duration_s else 0
                    self._prog_set(
                        self.res_prog, self.res_prog_lbl, self.res_pct,
                        pct,
                        f"[{idx+1}/{toplam}] Kodlanıyor… "
                        f"{cur:.0f}s / {duration_s:.0f}s")
            proc.wait()
            return proc.returncode == 0
        except Exception:
            return False

    def _res_bitti(self, masaustu):
        self._prog_set(self.res_prog, self.res_prog_lbl, self.res_pct,
                       100, f"✅ {len(self.res_dosyalar)} video sıkıştırıldı!")
        self._serbest(self.res_btn, "📉  Sıkıştır")
        self._klasor_ac(str(masaustu))

    # ── Video bilgisi (ffmpeg stderr) ────────────────────────
    def _video_bilgisi(self, yol: str):
        try:
            r = subprocess.run(
                [self.ffmpeg_path, "-i", yol],
                capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=15,
            )
            t = r.stderr
            dm = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", t)
            if not dm:
                return None
            duration = int(dm.group(1))*3600 + int(dm.group(2))*60 + float(dm.group(3))
            rm = re.search(r",\s*(\d{2,5})x(\d{2,5})", t)
            if not rm:
                return None
            return duration, int(rm.group(1)), int(rm.group(2))
        except Exception:
            return None

    # ════════════════════════════════════════════════════════════
    #  YARDIMCI — UI
    # ════════════════════════════════════════════════════════════
    def _kart(self, parent) -> tk.Frame:
        return tk.Frame(parent, bg=CARD,
                        highlightbackground=BORDER,
                        highlightthickness=2)

    def _kart_tikla(self, kart, widgetler, komut, hover_renk):
        def _on_enter(e): kart.config(highlightbackground=hover_renk)
        def _on_leave(e): kart.config(highlightbackground=BORDER)
        for w in [kart] + widgetler:
            w.bind("<Button-1>", komut)
            w.bind("<Enter>", _on_enter)
            w.bind("<Leave>", _on_leave)

    def _progress_row(self, parent, stil_prefix):
        lbl = tk.Label(parent, text="Hazır",
                       font=("Segoe UI", 9), bg=BG, fg=SUB, anchor="w")
        lbl.pack(fill="x", padx=16, pady=(14, 2))

        bar = ttk.Progressbar(parent,
                              style=f"{stil_prefix}.Horizontal.TProgressbar",
                              maximum=100, length=520, mode="determinate")
        bar.pack(padx=16)

        pct = tk.Label(parent, text="",
                       font=("Segoe UI", 9), bg=BG, fg=SUB, anchor="e")
        pct.pack(fill="x", padx=16)
        return lbl, bar, pct

    def _buton(self, parent, metin, renk, komut) -> tk.Button:
        darker = self._darken(renk)
        btn = tk.Button(parent, text=metin,
                        font=("Segoe UI", 12, "bold"),
                        bg=renk, fg=WHITE,
                        activebackground=darker, activeforeground=WHITE,
                        relief="flat", cursor="hand2",
                        padx=30, pady=10, bd=0, command=komut)
        btn.bind("<Enter>", lambda e: btn.config(bg=darker))
        btn.bind("<Leave>", lambda e: btn.config(bg=renk))
        return btn

    # ════════════════════════════════════════════════════════════
    #  YARDIMCI — İŞLEM
    # ════════════════════════════════════════════════════════════
    def _prog_set(self, bar, lbl, pct_lbl, pct: float, metin: str):
        def _do():
            bar.config(value=pct)
            lbl.config(text=metin, fg=TEXT if pct < 100 else SUCCESS)
            pct_lbl.config(text=f"%{pct:.1f}" if pct > 0 else "")
        self.root.after(0, _do)

    def _sifirla_prog(self, bar, lbl, pct_lbl):
        bar.config(value=0)
        lbl.config(text="Hazır", fg=SUB)
        pct_lbl.config(text="")

    def _kilit(self, btn, metin):
        self.is_running = True
        btn.config(state="disabled", text=metin)

    def _serbest(self, btn, orijinal_metin):
        self.is_running = False
        btn.config(state="normal", text=orijinal_metin)

    @staticmethod
    def _masaustu() -> pathlib.Path:
        ev = pathlib.Path.home()
        for a in ("Desktop", "Masaüstü", "Masaustu"):
            p = ev / a
            if p.exists():
                return p
        return ev

    @staticmethod
    def _klasor_ac(yol: str):
        try:
            if sys.platform == "win32":
                os.startfile(yol)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", yol])
            else:
                subprocess.Popen(["xdg-open", yol])
        except Exception:
            pass

    @staticmethod
    def _darken(hex_col: str) -> str:
        r = max(0, int(hex_col[1:3], 16) - 30)
        g = max(0, int(hex_col[3:5], 16) - 30)
        b = max(0, int(hex_col[5:7], 16) - 30)
        return f"#{r:02x}{g:02x}{b:02x}"


# ── Başlat ────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    DiscordBolucu(root)
    root.mainloop()
