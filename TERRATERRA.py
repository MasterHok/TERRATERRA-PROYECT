"""
TERRARIA + tModLoader LAUNCHER
═══════════════════════════════════════════════════════════
Launcher para arrancar Terraria vanilla o tModLoader,
tanto en cliente como en servidor.

Estructura esperada:
  terra_project/
  ├── tModLoader/         (tModLoader, con sus .bat)
  ├── Terraria/           (vanilla GOG, con start-server.bat y Terraria.exe)
  ├── Worlds/
  │   ├── tModLoader/     (mundos de tModLoader, .wld + .twld)
  │   └── Vanilla/        (mundos de vanilla, .wld)
  ├── mods/               (opcional)
  ├── assets/             (iconos, música, style.qss)
  ├── config/             (settings.json, se crea solo)
  └── TERRATERRA.py       (este archivo)

Requisitos: Python 3.8+ · PySide6 · pywinpty
Autor: Sailor_Rei_Zora_Covennant_Cock_Master_64.
Versión: 3.0
═══════════════════════════════════════════════════════════
"""

import sys
import os
import re
import json
import shutil
import subprocess
import time
from typing import Optional

import urllib.request
import urllib.error

try:
    import winpty
    WINPTY_OK = True
except ImportError:
    WINPTY_OK = False

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QLineEdit, QComboBox, QPushButton,
    QFrame, QTabWidget, QPlainTextEdit, QMessageBox, QListWidget,
    QListWidgetItem, QDialog, QScrollArea, QSizePolicy, QToolTip,
    QSlider, QCheckBox,
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QSoundEffect
from PySide6.QtCore import (
    Qt, QThread, Signal, QUrl, QObject, QTimer,
    QRunnable, QThreadPool, Slot, QSize,
)
from PySide6.QtGui import (
    QIcon, QMovie, QPainter, QColor, QLinearGradient, QPixmap,
    QDesktopServices, QCursor,
)


# ═══════════════════════════════════════════════════════════
#  CONSTANTES
# ═══════════════════════════════════════════════════════════
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) TerrariaLauncher/3.0"
LAUNCHER_NAME = "TERRARIA LAUNCHER"
LAUNCHER_VERSION = "1.1"
LAUNCHER_AUTHOR = "Sailor_Rei_Zora_Covennant_Cock_Master_64."
DEFAULT_PORT = "7777"
SERVER_READER_LINES = 3000

WEBSITE_URL = "https://www.terrarianos.uk"
GITHUB_URL = "https://github.com/MasterHok/TERRACRAFT-PROYECT"
DISCORD_URL = "https://discord.gg/3KgY7d4ZSW"

IP_LOOKUP_DELAY_MS = 300
SERVER_STOP_TIMEOUT_MS = 8000

MODE_TMODLOADER = "tModLoader"
MODE_VANILLA = "Vanilla"

# Señal de mundo terminado de crear
WORLD_DONE_MARKER = "Finalizing world"

_ANSI_RE = re.compile(r'\x1b\[[0-9;?]*[A-Za-z]|\x1b[78]|\x1b\[0m')


def strip_ansi(text: str) -> str:
    """Elimina códigos de escape ANSI y limpia líneas de relleno."""
    if not text:
        return text
    text = _ANSI_RE.sub("", text)
    if text.strip() == "" and len(text) > 40:
        return ""
    return text


# ═══════════════════════════════════════════════════════════
#  RUTAS Y UTILIDADES
# ═══════════════════════════════════════════════════════════
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def get_working_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(".")


def http_get_text(url: str, timeout: int = 8) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode().strip()


# ═══════════════════════════════════════════════════════════
#  HILO: lector del PTY del servidor
# ═══════════════════════════════════════════════════════════
class ServerReaderThread(QThread):
    line_received = Signal(str)
    process_ended = Signal(int)

    def __init__(self, pty_process):
        super().__init__()
        self.pty = pty_process
        self._buffer = ""

    def run(self):
        try:
            while True:
                try:
                    chunk = self.pty.read(1024)
                except EOFError:
                    break
                if not chunk:
                    break

                self._buffer += chunk

                while "\n" in self._buffer:
                    line, self._buffer = self._buffer.split("\n", 1)
                    clean = strip_ansi(line.rstrip("\r"))
                    if clean.strip():
                        self.line_received.emit(clean)

                if self._buffer:
                    clean = strip_ansi(self._buffer.rstrip("\r"))
                    if clean.strip():
                        self.line_received.emit(clean)
                        self._buffer = ""

        except Exception:
            pass
        try:
            self.pty.wait()
        except Exception:
            pass
        self.process_ended.emit(0)


# ═══════════════════════════════════════════════════════════
#  TAREA: vigilar proceso del cliente
# ═══════════════════════════════════════════════════════════
class ProcessWatcherSignals(QObject):
    finished = Signal()


class ProcessWatcherTask(QRunnable):
    def __init__(self, process):
        super().__init__()
        self.process = process
        self.signals = ProcessWatcherSignals()

    @Slot()
    def run(self):
        try:
            if hasattr(self.process, "poll"):
                while self.process.poll() is None:
                    time.sleep(0.5)
            elif hasattr(self.process, "isalive"):
                while self.process.isalive():
                    time.sleep(0.5)
        except Exception:
            pass
        self.signals.finished.emit()


# ═══════════════════════════════════════════════════════════
#  TAREA: consultar IPs públicas
# ═══════════════════════════════════════════════════════════
class IPLookupSignals(QObject):
    result_ready = Signal(str, str)
    error_occurred = Signal(str)


class IPLookupTask(QRunnable):
    def __init__(self):
        super().__init__()
        self.signals = IPLookupSignals()

    @Slot()
    def run(self):
        ipv4 = self._fetch("https://api.ipify.org")
        ipv6 = self._fetch("https://api64.ipify.org")
        if ipv4 is None and ipv6 is None:
            self.signals.error_occurred.emit("No se pudo obtener ninguna IP pública")
            return
        if ipv6 and ipv4 and ipv6 == ipv4:
            ipv6 = None
        self.signals.result_ready.emit(
            ipv4 or "(no disponible)",
            ipv6 or "(solo IPv4)"
        )

    def _fetch(self, url: str) -> Optional[str]:
        try:
            data = http_get_text(url, timeout=6)
            return data if data else None
        except Exception:
            return None


# ═══════════════════════════════════════════════════════════
#  FONDO ANIMADO
# ═══════════════════════════════════════════════════════════
class AnimatedBackground(QWidget):
    def __init__(self, parent=None, gif_name="fondo.gif", allow_static_fallback=False):
        super().__init__(parent)
        self.movie = None
        self._static_pixmap = None

        gif_path = resource_path(os.path.join("assets", gif_name))

        if allow_static_fallback and not os.path.exists(gif_path):
            png_path = gif_path.rsplit(".", 1)[0] + ".png"
            if os.path.exists(png_path):
                self._static_pixmap = QPixmap(png_path)
                return

        if os.path.exists(gif_path) and gif_path.lower().endswith(".gif"):
            self.movie = QMovie(gif_path)
            self.movie.setCacheMode(QMovie.CacheAll)
            self.movie.frameChanged.connect(self.update)
            self.movie.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.movie and self.movie.currentPixmap():
            scaled = self.movie.currentPixmap().scaled(
                self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            painter.drawPixmap(0, 0, scaled)
        elif self._static_pixmap and not self._static_pixmap.isNull():
            scaled = self._static_pixmap.scaled(
                self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            painter.drawPixmap(0, 0, scaled)
        else:
            gradient = QLinearGradient(0, 0, 0, self.height())
            gradient.setColorAt(0, QColor(26, 26, 46))
            gradient.setColorAt(0.5, QColor(42, 22, 38))
            gradient.setColorAt(1, QColor(90, 30, 50))
            painter.fillRect(self.rect(), gradient)
        painter.end()

    def resizeEvent(self, event):
        super().resizeEvent(event)


# ═══════════════════════════════════════════════════════════
#  MÚSICA DE FONDO
# ═══════════════════════════════════════════════════════════
class BackgroundMusic(QObject):
    def __init__(self):
        super().__init__()
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.3)
        self.is_playing = False
        self.was_playing_before_pause = False
        self.player.mediaStatusChanged.connect(self.handle_media_status)

    def handle_media_status(self, status):
        if status == QMediaPlayer.EndOfMedia:
            self.player.setPosition(0)
            self.player.play()

    def play(self, file_path):
        if not os.path.exists(file_path):
            return
        try:
            self.stop()
            self.player.setSource(QUrl.fromLocalFile(file_path))
            self.player.play()
            self.is_playing = True
        except Exception as e:
            print(f"Error audio: {e}")

    def stop(self):
        if self.is_playing:
            self.player.stop()
            self.is_playing = False

    def pause_for_launch(self):
        if self.is_playing:
            self.was_playing_before_pause = True
            self.player.pause()
            self.is_playing = False

    def resume_after_launch(self):
        if self.was_playing_before_pause:
            self.player.play()
            self.is_playing = True
            self.was_playing_before_pause = False

    def set_volume(self, volume):
        self.audio_output.setVolume(max(0.0, min(1.0, volume)))

    def toggle(self):
        if self.is_playing:
            self.player.pause()
            self.is_playing = False
        else:
            self.player.play()
            self.is_playing = True


# ═══════════════════════════════════════════════════════════
#  DIÁLOGO DE BIENVENIDA
# ═══════════════════════════════════════════════════════════
class FirstRunDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bienvenido a TERRARIA LAUNCHER")
        self.setModal(True)
        self.setMinimumSize(640, 640)
        self.resultado = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.fondo = AnimatedBackground(
            self,
            gif_name="fondo_info.gif",
            allow_static_fallback=True,
        )
        layout.addWidget(self.fondo, stretch=1)

        inner = QVBoxLayout(self.fondo)
        inner.setContentsMargins(30, 30, 30, 30)
        inner.setSpacing(16)

        titulo = QLabel("¡Bienvenido a TERRARIA LAUNCHER!")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet(
            "color: #e94560; font-size: 22px; font-weight: bold; "
            "background: rgba(10, 10, 26, 0.85); "
            "border-radius: 8px; padding: 12px;"
        )
        inner.addWidget(titulo)

        cuerpo = QLabel(
            "<div style='text-align: center;'>"

            "<p style='margin: 0 0 14px 0;'>"
            "Este launcher arranca <b>Terraria vanilla</b> y "
            "<b>tModLoader</b>, tanto en cliente como en servidor."
            "</p>"

            "<p style='color: #e94560; font-weight: bold; margin: 12px 0 4px 0;'>"
            "📦 ¿Qué hace el launcher?"
            "</p>"
            "<p style='margin: 0;'>"
            "• Arranca el cliente (Terraria.exe o tModLoader)<br>"
            "• Arranca el servidor (Vanilla o tModLoader)<br>"
            "• Gestiona mundos en subcarpetas por modo<br>"
            "• Activa/desactiva mods en <b>enabled.json</b><br>"
            "• Muestra tu IP pública para que se conecten tus amigos"
            "</p>"

            "<p style='color: #e94560; font-weight: bold; margin: 12px 0 4px 0;'>"
            "🌐 Vanilla · tModLoader · Crossplay"
            "</p>"
            "<p style='margin: 0;'>"
            "El servidor <b>Vanilla</b> solo acepta conexiones por <b>IPv4</b>.<br>"
            "El servidor <b>tModLoader</b> acepta IPv4 e IPv6, y puede usar "
            "las funciones de Steam (overlay, invitaciones) o no.<br>"
            "El crossplay entre GOG y Steam funciona en ambos modos "
            "por conexión directa IP."
            "</p>"

            "<p style='color: #e94560; font-weight: bold; margin: 12px 0 4px 0;'>"
            "🔒 Privacidad"
            "</p>"
            "<p style='margin: 0 0 10px 0;'>"
            "Solo se consulta tu IP pública desde api.ipify.org para mostrártela "
            "en la pestaña Red."
            "</p>"

            "<p style='color: #7fff7f; font-weight: bold; margin: 14px 0 0 0;'>"
            "¿Aceptas arrancar el launcher?"
            "</p>"
            "</div>"
        )
        cuerpo.setWordWrap(True)
        cuerpo.setStyleSheet(
            "color: #e0e0e0; font-size: 13px; line-height: 160%; "
            "background: rgba(10, 10, 26, 0.85); "
            "border-radius: 8px; padding: 16px;"
        )
        inner.addWidget(cuerpo, stretch=1)

        botones = QHBoxLayout()
        botones.setSpacing(20)
        botones.addStretch()

        self.btn_si = QPushButton("✔  Sí, continuar")
        self.btn_si.setObjectName("dialog_yes")
        self.btn_si.setFixedHeight(44)
        self.btn_si.setMinimumWidth(160)
        self.btn_si.setCursor(Qt.PointingHandCursor)
        self.btn_si.clicked.connect(self._on_yes)
        botones.addWidget(self.btn_si)

        self.btn_no = QPushButton("✖  No, salir")
        self.btn_no.setObjectName("dialog_no")
        self.btn_no.setFixedHeight(44)
        self.btn_no.setMinimumWidth(160)
        self.btn_no.setCursor(Qt.PointingHandCursor)
        self.btn_no.clicked.connect(self._on_no)
        botones.addWidget(self.btn_no)

        botones.addStretch()
        inner.addLayout(botones)

        self.setStyleSheet("""
            QDialog { background-color: #1a1a2e; }
            QPushButton#dialog_yes {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e94560, stop:1 #b0304a);
                color: white; border: none; border-radius: 8px;
                font-weight: bold; font-size: 14px; padding: 8px 20px;
            }
            QPushButton#dialog_yes:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff5773, stop:1 #e94560);
            }
            QPushButton#dialog_no {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #444, stop:1 #222);
                color: white; border: none; border-radius: 8px;
                font-weight: bold; font-size: 14px; padding: 8px 20px;
            }
            QPushButton#dialog_no:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #666, stop:1 #444);
            }
        """)

        self._sound_yes = self._load_sound("click_yes.wav")
        self._sound_no = self._load_sound("click_no.wav")
        self._sound_intro = self._load_sound("dialog_intro.wav")
        if self._sound_intro:
            QTimer.singleShot(100, self._sound_intro.play)

    def _load_sound(self, filename):
        path = resource_path(os.path.join("assets", filename))
        if not os.path.exists(path):
            return None
        try:
            effect = QSoundEffect()
            effect.setSource(QUrl.fromLocalFile(path))
            effect.setVolume(1.0)
            return effect
        except Exception:
            return None

    def _on_yes(self):
        if self._sound_intro:
            self._sound_intro.stop()
        self.btn_si.setEnabled(False)
        self.btn_no.setEnabled(False)
        if self._sound_yes:
            self._sound_yes.play()
            QTimer.singleShot(1900, self._accept)
        else:
            self._accept()

    def _on_no(self):
        if self._sound_intro:
            self._sound_intro.stop()
        self.btn_si.setEnabled(False)
        self.btn_no.setEnabled(False)
        if self._sound_no:
            self._sound_no.play()
            QTimer.singleShot(900, self._reject)
        else:
            self._reject()

    def _accept(self):
        self.resultado = True
        self.accept()

    def _reject(self):
        self.resultado = False
        self.reject()


# ═══════════════════════════════════════════════════════════
#  LAUNCHER PRINCIPAL
# ═══════════════════════════════════════════════════════════
class TerrariaLauncher(QMainWindow):
    def __init__(self):
        super().__init__()

        # Rutas
        self.base_dir = get_working_dir()
        self.assets_dir = os.path.join(self.base_dir, "assets")
        self.config_dir = os.path.join(self.base_dir, "config")
        self.tmod_dir = os.path.join(self.base_dir, "tModLoader")
        self.tmod_mods_dir = os.path.join(self.tmod_dir, "Mods")
        self.vanilla_dir = os.path.join(self.base_dir, "Terraria")
        self.worlds_root = os.path.join(self.base_dir, "Worlds")
        self.settings_file = os.path.join(self.config_dir, "settings.json")

        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(os.path.join(self.worlds_root, "tModLoader"), exist_ok=True)
        os.makedirs(os.path.join(self.worlds_root, "Vanilla"), exist_ok=True)
        
        # Settings
        self.settings = {
            "accepted_downloads": False,
            "music_volume": 0.3,
            "last_mode": MODE_TMODLOADER,
            "seen_server_info": False,
        }
        self.load_settings()

        # Estado
        self.thread_pool = QThreadPool.globalInstance()
        self.client_process = None
        self.client_watcher = None
        self.server_process = None
        self.server_reader = None
        self.server_running = False
        self._creating_new_world = False
        self._new_world_name = ""

        self.init_ui()

        if not self.check_first_run():
            QTimer.singleShot(0, self.close)
            return

        self.init_background_music()

        QTimer.singleShot(IP_LOOKUP_DELAY_MS, self._load_ip_once)
        QTimer.singleShot(400, self.refresh_mods_list)

    # ─────────────────────────────────────────────
    #  SETTINGS
    # ─────────────────────────────────────────────
    def check_first_run(self) -> bool:
        if self.settings.get("accepted_downloads", False):
            return True
        dlg = FirstRunDialog(self)
        dlg.exec()
        if dlg.resultado:
            self.settings["accepted_downloads"] = True
            self.save_settings()
            return True
        return False

    def load_settings(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    self.settings.update(json.load(f))
        except Exception as e:
            print(f"Error cargando settings: {e}")

    def save_settings(self):
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error guardando settings: {e}")

    def closeEvent(self, event):
        if self.server_running and self.server_process:
            reply = QMessageBox.question(
                self, "Cerrar launcher",
                "El servidor está corriendo.\n\n"
                "Si cierras ahora, se detendrá y se guardará el mundo.\n\n"
                "¿Continuar?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                event.ignore()
                return
            self._force_kill_server()

        if self.client_process:
            try:
                if hasattr(self.client_process, "poll") and self.client_process.poll() is None:
                    self.client_process.kill()
                elif hasattr(self.client_process, "isalive") and self.client_process.isalive():
                    self.client_process.terminate(force=True)
            except Exception:
                pass

        event.accept()

    # ─────────────────────────────────────────────
    #  MÚSICA
    # ─────────────────────────────────────────────
    def init_background_music(self):
        self.music = BackgroundMusic()
        for name in ("music.mp3", "music.wav", "background.mp3", "theme.mp3"):
            p = resource_path(os.path.join("assets", name))
            if os.path.exists(p):
                self.music.play(p)
                self.music.set_volume(self.settings.get("music_volume", 0.3))
                break
        self._update_volume_icon()

    def _update_volume_icon(self):
        if not hasattr(self, "volume_icon"):
            return
        if not self.music.is_playing:
            self.volume_icon.setText("🔇")
            return
        vol = self.volume_slider.value() / 100.0
        if vol == 0:
            self.volume_icon.setText("🔇")
        elif vol < 0.3:
            self.volume_icon.setText("🔈")
        elif vol < 0.7:
            self.volume_icon.setText("🔉")
        else:
            self.volume_icon.setText("🔊")

    def toggle_music_click(self, event):
        if not hasattr(self, "music"):
            return
        self.music.toggle()
        self.music.was_playing_before_pause = False
        self._update_volume_icon()

    def change_volume(self, value):
        vol = value / 100.0
        if hasattr(self, "music"):
            self.music.set_volume(vol)
            self.settings["music_volume"] = vol
            self.save_settings()
            self._update_volume_icon()

    def _is_anything_running(self) -> bool:
        client_alive = False
        if self.client_process:
            if hasattr(self.client_process, "poll"):
                client_alive = self.client_process.poll() is None
            elif hasattr(self.client_process, "isalive"):
                client_alive = self.client_process.isalive()
        return client_alive or self.server_running

    def _update_music_state(self):
        if self._is_anything_running():
            self.music.pause_for_launch()
        else:
            self.music.resume_after_launch()
        self._update_volume_icon()

    # ─────────────────────────────────────────────
    #  UI
    # ─────────────────────────────────────────────
    def init_ui(self):
        self.setWindowTitle("TERRARIA LAUNCHER")
        self.setMinimumSize(800, 600)

        screen = QApplication.primaryScreen().availableGeometry()
        w = min(900, int(screen.width() * 0.8))
        h = min(850, int(screen.height() * 0.9))
        self.resize(w, h)

        icon_path = resource_path(os.path.join("assets", "icon.ico"))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            png = resource_path(os.path.join("assets", "icon.png"))
            if os.path.exists(png):
                self.setWindowIcon(QIcon(png))

        self.background = AnimatedBackground(self)
        self.setCentralWidget(self.background)

        main_layout = QVBoxLayout(self.background)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(18, 18, 18, 18)

        self.apply_stylesheet()

        # Banner
        title_layout = QHBoxLayout()
        banner_path = resource_path(os.path.join("assets", "banner.png"))
        title_label = QLabel()
        title_label.setObjectName("title_label")
        title_label.setAlignment(Qt.AlignCenter)

        if os.path.exists(banner_path):
            pixmap = QPixmap(banner_path)
            if not pixmap.isNull():
                title_label.setPixmap(pixmap.scaledToHeight(130, Qt.SmoothTransformation))
        else:
            title_label.setText("✦ TERRARIA LAUNCHER ✦")

        title_layout.addWidget(title_label)

        # Volumen + iconos
        volume_widget = QWidget()
        volume_widget.setFixedWidth(320)
        vlayout = QHBoxLayout(volume_widget)
        vlayout.setContentsMargins(0, 0, 0, 0)
        vlayout.setSpacing(8)

        self.folder_button = QPushButton("📁")
        self.folder_button.setObjectName("folder_button")
        self.folder_button.setFixedSize(34, 34)
        self.folder_button.setToolTip("Abrir carpeta del launcher")
        self.folder_button.clicked.connect(self.open_launcher_folder)
        vlayout.addWidget(self.folder_button)

        self.web_button = self._make_icon_button(
            "web.png", "🌐", "Visitar sitio web", self.open_web_link
        )
        vlayout.addWidget(self.web_button)

        self.github_icon_button = self._make_icon_button(
            "github.png", "🐙", "Ver código en GitHub", self.open_github_link
        )
        vlayout.addWidget(self.github_icon_button)

        self.discord_button = self._make_icon_button(
            "discord.png", "💬", "Unirse al Discord",
            lambda: self.open_discord_link(None), size=40
        )
        vlayout.addWidget(self.discord_button)

        self.volume_icon = QLabel("🔊")
        self.volume_icon.setFixedSize(30, 30)
        self.volume_icon.setAlignment(Qt.AlignCenter)
        self.volume_icon.setStyleSheet("color: #e94560; font-size: 20px;")
        self.volume_icon.mousePressEvent = self.toggle_music_click
        vlayout.addWidget(self.volume_icon)

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(int(self.settings.get("music_volume", 0.3) * 100))
        self.volume_slider.setFixedWidth(60)
        self.volume_slider.valueChanged.connect(self.change_volume)
        vlayout.addWidget(self.volume_slider)

        title_layout.addWidget(volume_widget)
        main_layout.addLayout(title_layout)

        # Tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.client_tab = QWidget()
        self.build_client_tab(self.client_tab)
        self.tabs.addTab(self.client_tab, "🎮 Cliente")

        self.server_tab = QWidget()
        self.build_server_tab(self.server_tab)
        self.tabs.addTab(self.server_tab, "🖥️ Servidor")
        self.tabs.currentChanged.connect(self._on_tab_changed)

        self.log_tab = QWidget()
        self.build_log_tab(self.log_tab)
        self.tabs.addTab(self.log_tab, "📜 Log")

        self.network_tab = QWidget()
        self.build_network_tab(self.network_tab)
        self.tabs.addTab(self.network_tab, "🌐 Red")

        self.mods_tab = QWidget()
        self.build_mods_tab(self.mods_tab)
        self.tabs.addTab(self.mods_tab, "🧩 Mods")

        self.info_tab = QWidget()
        self.build_info_tab(self.info_tab)
        self.tabs.addTab(self.info_tab, "ℹ️ Info")

    def _make_icon_button(self, filename, fallback, tooltip, callback, size=30):
        btn = QLabel()
        btn.setFixedSize(size, size)
        btn.setAlignment(Qt.AlignCenter)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.PointingHandCursor)

        path = resource_path(os.path.join("assets", filename))
        if os.path.exists(path):
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                btn.setPixmap(pixmap.scaled(
                    size - 2, size - 2, Qt.KeepAspectRatio, Qt.SmoothTransformation
                ))
                btn.mousePressEvent = lambda e: callback()
                return btn

        btn.setText(fallback)
        btn.setStyleSheet("color: #e94560; font-size: 20px;")
        btn.mousePressEvent = lambda e: callback()
        return btn

    def apply_stylesheet(self):
        qss_path = resource_path(os.path.join("assets", "style.qss"))
        try:
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            print(f"[Stylesheet] No se pudo cargar style.qss: {e}")

    def make_panel(self, title_text):
        frame = QFrame()
        frame.setObjectName("panel")
        outer = QVBoxLayout(frame)
        outer.setContentsMargins(14, 12, 14, 14)
        outer.setSpacing(10)

        title = QLabel(title_text)
        title.setObjectName("panel_title")
        outer.addWidget(title)

        content = QVBoxLayout()
        content.setSpacing(10)
        outer.addLayout(content)

        return frame, content

    def _field(self, text):
        lbl = QLabel(text)
        lbl.setObjectName("field_label")
        return lbl

    def _on_tab_changed(self, index):
        """Muestra el aviso de primera visita a la pestaña Servidor."""
        if index != self.tabs.indexOf(self.server_tab):
            return
        if self.settings.get("seen_server_info", False):
            return

        # Marcar como visto y mostrar el aviso
        self.settings["seen_server_info"] = True
        self.save_settings()
        QTimer.singleShot(200, self.show_server_info)

    # ─────────────────────────────────────────────
    #  CLIENTE
    # ─────────────────────────────────────────────
    def build_client_tab(self, parent):
        layout = QVBoxLayout(parent)
        layout.setSpacing(10)
        layout.setContentsMargins(14, 14, 14, 14)

        panel, _ = self.make_panel("Cliente")

        info = QLabel(
            "Elige el modo y pulsa JUGAR.<br><br>"
            "• <b>tModLoader</b>: abre tModLoader con los mods activados "
            "en la pestaña Mods.<br>"
            "• <b>Vanilla</b>: abre Terraria original (GOG), sin mods."
        )
        info.setWordWrap(True)
        panel.layout().addWidget(info)

        mode_row = QHBoxLayout()
        mode_row.setSpacing(6)
        mode_label = QLabel("Modo:")
        mode_label.setObjectName("field_label")
        mode_row.addWidget(mode_label)

        self.client_mode_combo = QComboBox()
        self.client_mode_combo.addItems([MODE_TMODLOADER, MODE_VANILLA])
        self.client_mode_combo.setCurrentText(self.settings.get("last_mode", MODE_TMODLOADER))
        self.client_mode_combo.currentTextChanged.connect(self.on_client_mode_changed)
        mode_row.addWidget(self.client_mode_combo, stretch=1)
        panel.layout().addLayout(mode_row)

        layout.addWidget(panel)

        self.client_status = QLabel("✅ Listo para jugar")
        self.client_status.setAlignment(Qt.AlignCenter)
        self.client_status.setStyleSheet(
            "font-size: 13px; font-weight: bold; color: #e94560;"
            "padding: 8px; background: rgba(0,0,0,0.4);"
            "border-radius: 6px; min-height: 34px;"
        )
        layout.addWidget(self.client_status)

        self.start_button = QPushButton("▶ JUGAR")
        self.start_button.setObjectName("start_button")
        self.start_button.clicked.connect(self.start_client)
        layout.addWidget(self.start_button)

        layout.addStretch()

    def on_client_mode_changed(self, mode):
        self.settings["last_mode"] = mode
        self.save_settings()
        self.refresh_mods_list()

    def start_client(self):
        if self.client_process and hasattr(self.client_process, "poll") and self.client_process.poll() is None:
            QMessageBox.warning(self, "Aviso", "El juego ya está en ejecución.")
            return

        mode = self.client_mode_combo.currentText()

        try:
            self.start_button.setEnabled(False)
            self.start_button.setText("⏳ INICIANDO...")
            self.client_status.setText("🚀 Iniciando...")

            if mode == MODE_TMODLOADER:
                cmd = self._build_client_command(use_steam=False)
                cwd = self.tmod_dir
            else:
                exe_path = os.path.join(self.vanilla_dir, "Terraria.exe")
                if not os.path.exists(exe_path):
                    QMessageBox.critical(
                        self, "Error",
                        f"No se encontró:\n{exe_path}"
                    )
                    self.start_button.setEnabled(True)
                    self.start_button.setText("▶ JUGAR")
                    self.client_status.setText("✅ Listo")
                    return
                cmd = [exe_path]
                cwd = self.vanilla_dir

            creationflags = 0
            if os.name == "nt":
                creationflags = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP

            self.client_process = subprocess.Popen(
                cmd,
                cwd=cwd,
                creationflags=creationflags,
            )

            self._update_music_state()
            self.client_status.setText("🟢 Juego en ejecución")

            QMessageBox.information(
                self,
                "¡Gracias por usar TERRARIA LAUNCHER!",
                "🎮 El juego se abrirá en unos instantes.\n"
                "(Tardará unos segundos).\n\n"
                "El launcher seguirá abierto.\n"
                "Cuando cierres Terraria, el botón volverá a 'JUGAR'.\n\n"
                "✨ ¡Gracias y que lo disfrutes! ✨"
            )

            watcher = ProcessWatcherTask(self.client_process)
            watcher.signals.finished.connect(self.on_client_closed)
            self.client_watcher = watcher
            self.thread_pool.start(watcher)

        except FileNotFoundError as e:
            QMessageBox.critical(self, "Error", f"No se encontraron los archivos:\n\n{e}")
            self.start_button.setEnabled(True)
            self.start_button.setText("▶ JUGAR")
            self.client_status.setText("✅ Listo")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo lanzar el juego:\n{e}")
            self.start_button.setEnabled(True)
            self.start_button.setText("▶ JUGAR")
            self.client_status.setText("✅ Listo")
            self._update_music_state()
            
    def on_client_closed(self):
        self.client_process = None
        self.start_button.setEnabled(True)
        self.start_button.setText("▶ JUGAR")
        self.client_status.setText("✅ Listo")
        self._update_music_state()

    def _build_client_command(self, use_steam: bool = False):
        busybox = os.path.join(self.tmod_dir, "LaunchUtils", "busybox64.exe")
        script_caller = os.path.join(self.tmod_dir, "LaunchUtils", "ScriptCaller.sh")

        if not os.path.exists(busybox):
            raise FileNotFoundError(
                f"No se encontró busybox64.exe en:\n{busybox}"
            )
        if not os.path.exists(script_caller):
            raise FileNotFoundError(
                f"No se encontró ScriptCaller.sh en:\n{script_caller}"
            )

        args = [
            busybox, "bash", script_caller,
            "-steam" if use_steam else "-nosteam",
        ]
        return args

    def show_server_info(self):
        """Muestra un diálogo ancho con scroll explicando el funcionamiento del servidor."""
        dlg = QDialog(self)
        dlg.setWindowTitle("Cómo funciona el servidor")
        dlg.setModal(True)
        dlg.resize(760, 520)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Área con scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical {
                background: rgba(0,0,0,0.3); width: 8px; border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #e94560; border-radius: 4px; min-height: 30px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        contenido = QWidget()
        clayout = QVBoxLayout(contenido)
        clayout.setContentsMargins(6, 6, 6, 6)

        texto = QLabel(
            "<h3 style='color: #e94560;'>🖥️ Servidor de Terraria</h3>"
            "<p>Este launcher puede arrancar dos tipos de servidor:</p>"

            "<p><b>• tModLoader</b><br>"
            "Servidor con mods. Acepta conexiones por <b>IPv4 e IPv6</b>.<br>"
            "Los jugadores pueden conectarse por IP directa o por invitación "
            "de Steam (si está activado el overlay de Steam).</p>"

            "<p><b>• Vanilla</b><br>"
            "Servidor original de Terraria (GOG).<br>"
            "⚠️ <b>Solo acepta conexiones por IPv4.</b><br>"
            "Si tus amigos intentan conectarse usando tu dirección IPv6, "
            "no funcionará. Comparte siempre tu IPv4 + puerto.</p>"

            "<hr>"

            "<h3 style='color: #e94560;'>🌐 Mod IPv6Remapper</h3>"
            "<p>Es un mod de tModLoader que permite a los jugadores "
            "<b>conectarse por IPv6</b> cuando el servidor solo escucha en IPv4, "
            "o viceversa. Es especialmente útil si tu proveedor de Internet "
            "te da solo IPv6 y tus amigos solo tienen IPv4, o al revés.</p>"

            "<p><b>¿Te interesa?</b><br>"
            "Antes de arrancar el servidor de tModLoader, ve a la pestaña "
            "<b>🧩 Mods</b> y activa <code>IPv6Remapper</code>.<br>"
            "Si no tienes el mod todavía, coloca el archivo "
            "<code>.tmod</code> en la carpeta <code>tModLoader/Mods/</code>.</p>"

            "<p><b>Si no lo necesitas</b>, puedes arrancar el servidor "
            "sin él. El servidor funcionará igual por IPv4.</p>"

            "<hr>"

            "<h3 style='color: #e94560;'>📡 IPv4 vs IPv6</h3>"
            "<p><b>IPv4</b> es el sistema clásico de direcciones IP. "
            "Lo soportan todos los routers y operadores. Es lo que se usa "
            "por defecto en Vanilla y en la mayoría de servidores.</p>"

            "<p><b>IPv6</b> es el sistema moderno. Lo usan cada vez más "
            "operadores, sobre todo en móviles y fibra. No todos los routers "
            "lo soportan bien y algunos proveedores solo dan IPv6.</p>"

            "<p>💡 <b>Recomendación:</b> si tus amigos no tienen problemas "
            "para conectarse por IPv4, no necesitas el mod. Si tienen "
            "problemas de conexión y sospechas que es por IPv6, actívalo.</p>"
        )
        texto.setWordWrap(True)
        texto.setTextFormat(Qt.RichText)
        texto.setStyleSheet(
            "color: #e0e0e0; font-size: 13px; line-height: 160%; "
            "padding: 10px;"
        )
        clayout.addWidget(texto)
        clayout.addStretch()

        scroll.setWidget(contenido)
        layout.addWidget(scroll, stretch=1)

        # Botón Cerrar
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setFixedWidth(120)
        btn_cerrar.clicked.connect(dlg.accept)
        btn_row.addWidget(btn_cerrar)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        dlg.exec()
        
    # ─────────────────────────────────────────────
    #  SERVIDOR
    # ─────────────────────────────────────────────
    def build_server_tab(self, parent):
        layout = QVBoxLayout(parent)
        layout.setSpacing(10)
        layout.setContentsMargins(14, 14, 14, 14)

        panel, _ = self.make_panel("Servidor")

        grid = QGridLayout()
        grid.setSpacing(10)
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(12)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)

        # ─── Fila 0: Modo + [?] | Mundo + [🗑] ───
        mode_lbl = QLabel("Modo:")
        mode_lbl.setObjectName("field_label")
        grid.addWidget(mode_lbl, 0, 0)

        mode_row = QHBoxLayout()
        mode_row.setSpacing(6)

        self.server_mode_combo = QComboBox()
        self.server_mode_combo.addItems([MODE_TMODLOADER, MODE_VANILLA])
        self.server_mode_combo.setCurrentText(
            self.settings.get("last_mode", MODE_TMODLOADER)
        )
        self.server_mode_combo.currentTextChanged.connect(self.on_server_mode_changed)
        mode_row.addWidget(self.server_mode_combo, stretch=1)

        self.btn_server_info = QPushButton("?")
        self.btn_server_info.setObjectName("copy_button")
        self.btn_server_info.setFixedSize(34, 34)
        self.btn_server_info.setToolTip("¿Cómo funciona el servidor?")
        self.btn_server_info.clicked.connect(self.show_server_info)
        mode_row.addWidget(self.btn_server_info)

        grid.addLayout(mode_row, 0, 1)

        world_lbl = QLabel("Mundo:")
        world_lbl.setObjectName("field_label")
        grid.addWidget(world_lbl, 0, 2)

        world_row = QHBoxLayout()
        world_row.setSpacing(6)

        self.world_combo = QComboBox()
        self.world_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.world_combo.currentIndexChanged.connect(self.on_world_changed)
        world_row.addWidget(self.world_combo, stretch=1)

        self.btn_delete_world = QPushButton("🗑")
        self.btn_delete_world.setObjectName("delete_button")
        self.btn_delete_world.setFixedSize(46, 34)
        self.btn_delete_world.setStyleSheet("font-size: 16px;")
        self.btn_delete_world.setToolTip("Eliminar el mundo seleccionado (.wld y .twld)")
        self.btn_delete_world.clicked.connect(self.delete_selected_world)
        world_row.addWidget(self.btn_delete_world)

        grid.addLayout(world_row, 0, 3)

        # ─── Fila 1: Max players | Puerto ───
        players_lbl = QLabel("Max players:")
        players_lbl.setObjectName("field_label")
        grid.addWidget(players_lbl, 1, 0)

        self.max_players_input = QLineEdit("16")
        self.max_players_input.setFixedWidth(80)
        grid.addWidget(self.max_players_input, 1, 1)

        port_lbl = QLabel("Puerto:")
        port_lbl.setObjectName("field_label")
        grid.addWidget(port_lbl, 1, 2)

        self.server_port_input = QLineEdit(DEFAULT_PORT)
        self.server_port_input.setFixedWidth(100)
        grid.addWidget(self.server_port_input, 1, 3)

        # ─── Fila 2: Contraseña | Overlay Steam ───
        pass_lbl = QLabel("Contraseña:")
        pass_lbl.setObjectName("field_label")
        grid.addWidget(pass_lbl, 2, 0)

        self.server_pass_input = QLineEdit()
        self.server_pass_input.setEchoMode(QLineEdit.Password)
        self.server_pass_input.setPlaceholderText("(vacío = sin contraseña)")
        grid.addWidget(self.server_pass_input, 2, 1)

        self.steam_lbl = QLabel("Overlay de Steam:")
        self.steam_lbl.setObjectName("field_label")
        grid.addWidget(self.steam_lbl, 2, 2)

        self.steam_checkbox = QCheckBox("Activar")
        self.steam_checkbox.setToolTip(
            "Activa las funciones de Steam (overlay, invitaciones).\n"
            "Si se desactiva, el crossplay por IP sigue funcionando igual."
        )
        grid.addWidget(self.steam_checkbox, 2, 3)

        # ─── Fila 3: Auto port forward ───
        upnp_lbl = QLabel("Auto port forward:")
        upnp_lbl.setObjectName("field_label")
        grid.addWidget(upnp_lbl, 3, 0)

        self.upnp_checkbox = QCheckBox("UPnP (puede no funcionar en algunos routers)")
        self.upnp_checkbox.setToolTip(
            "Solicita al router que abra el puerto automáticamente.\n"
            "⚠️ Puede no funcionar si el router tiene UPnP desactivado."
        )
        grid.addWidget(self.upnp_checkbox, 3, 1, 1, 3)

        panel.layout().addLayout(grid)

        # Aviso IPv4 (solo vanilla)
        self.ipv4_warning = QLabel(
            "⚠️ El servidor Vanilla solo acepta conexiones por <b>IPv4</b>. "
            "Comparte tu IPv4 + puerto con tus amigos."
        )
        self.ipv4_warning.setWordWrap(True)
        self.ipv4_warning.setObjectName("ram_note")
        self.ipv4_warning.setVisible(False)
        panel.layout().addWidget(self.ipv4_warning)

        layout.addWidget(panel)

        self.server_main_button = QPushButton("▶ ARRANCAR SERVIDOR")
        self.server_main_button.setObjectName("server_main_button")
        self.server_main_button.clicked.connect(self.server_action)
        layout.addWidget(self.server_main_button)

        self.server_status = QLabel("Servidor detenido")
        self.server_status.setAlignment(Qt.AlignCenter)
        self.server_status.setStyleSheet(
            "font-size: 12px; font-weight: bold; color: #b19cd9;"
            "padding: 8px; background: rgba(0,0,0,0.4);"
            "border-radius: 6px; min-height: 32px;"
        )
        layout.addWidget(self.server_status)

        layout.addStretch()

        # Cargar mundos y aplicar estado inicial
        self.refresh_worlds_list()
        self.on_server_mode_changed(self.server_mode_combo.currentText())

    def on_server_mode_changed(self, mode):
        self.settings["last_mode"] = mode
        self.save_settings()

        is_tmod = mode == MODE_TMODLOADER
        self.steam_lbl.setVisible(is_tmod)
        self.steam_checkbox.setVisible(is_tmod)
        self.ipv4_warning.setVisible(not is_tmod)

        if hasattr(self, "world_combo"):
            self.refresh_worlds_list()

    # ─────────────────────────────────────────────
    #  MUNDOS (subcarpetas por modo)
    # ─────────────────────────────────────────────
    def get_current_worlds_dir(self):
        """Devuelve la subcarpeta de mundos del modo actual."""
        mode = self.server_mode_combo.currentText()
        subfolder = "tModLoader" if mode == MODE_TMODLOADER else "Vanilla"
        path = os.path.join(self.worlds_root, subfolder)
        os.makedirs(path, exist_ok=True)
        return path

    def _get_user_documents_dir(self):
        return os.path.join(os.path.expanduser("~"), "Documents")

    def _scan_worlds(self):
        """
        Devuelve lista de tuplas (nombre, ruta_completa).
        Busca en la subcarpeta del launcher y, si existe, en Documentos.
        """
        worlds = []
        seen = set()

        base_local = self.get_current_worlds_dir()
        dirs_to_scan = [base_local]

        docs = self._get_user_documents_dir()
        if docs:
            mode = self.server_mode_combo.currentText()
            if mode == MODE_TMODLOADER:
                dirs_to_scan.append(os.path.join(
                    docs, "My Games", "Terraria", "tModLoader", "Worlds"
                ))
            else:
                dirs_to_scan.append(os.path.join(
                    docs, "My Games", "Terraria", "Worlds"
                ))

        for base in dirs_to_scan:
            if not os.path.isdir(base):
                continue
            try:
                for f in sorted(os.listdir(base)):
                    if not f.endswith(".wld"):
                        continue
                    name = f[:-4]
                    full = os.path.join(base, f)
                    if name in seen:
                        continue
                    seen.add(name)
                    worlds.append((name, full))
            except Exception as e:
                print(f"[Worlds] Error leyendo {base}: {e}")

        return worlds

    def refresh_worlds_list(self):
        current = self.world_combo.currentText()
        self.world_combo.blockSignals(True)
        self.world_combo.clear()

        self.world_combo.addItem("➕ Crear mundo nuevo")

        for name, full in self._scan_worlds():
            self.world_combo.addItem(name, userData=full)

        idx = self.world_combo.findText(current)
        if idx >= 0:
            self.world_combo.setCurrentIndex(idx)

        self.world_combo.blockSignals(False)
        self.on_world_changed(self.world_combo.currentIndex())

    def on_world_changed(self, index):
        self.btn_delete_world.setEnabled(index > 0)

    def delete_selected_world(self):
        index = self.world_combo.currentIndex()
        if index <= 0:
            return

        world_path = self.world_combo.itemData(index)
        if not world_path:
            return

        name = os.path.basename(world_path).replace(".wld", "")

        reply = QMessageBox.question(
            self, "Eliminar mundo",
            f"¿Eliminar permanentemente el mundo «{name}»?\n\n"
            f"Ruta:\n{world_path}\n\n"
            "Se borrarán los archivos .wld y .twld.\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        try:
            if os.path.exists(world_path):
                os.remove(world_path)
            twld = world_path[:-4] + ".twld"
            if os.path.exists(twld):
                os.remove(twld)
            self.refresh_worlds_list()
            QMessageBox.information(self, "Eliminado", f"✅ Mundo «{name}» eliminado.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo eliminar:\n{e}")

    def _get_selected_world_path(self):
        index = self.world_combo.currentIndex()
        if index <= 0:
            return ""
        return self.world_combo.itemData(index) or ""

    def _get_selected_world_name(self):
        path = self._get_selected_world_path()
        if not path:
            return ""
        return os.path.basename(path).replace(".wld", "")

    # ─────────────────────────────────────────────
    #  CONSTRUIR COMANDO DEL SERVIDOR
    # ─────────────────────────────────────────────
    def _build_server_command(self, use_steam: bool = False):
        mode = self.server_mode_combo.currentText()
        world_path = self._get_selected_world_path()
        is_new = (world_path == "")

        # ─── Generar serverconfig.txt ───
        config_lines = ["# Generado por TERRARIA LAUNCHER"]

        if not is_new:
            if mode == MODE_VANILLA:
                # Vanilla: ruta absoluta (worldpath no es fiable)
                config_lines.append(f"world={world_path.replace(chr(92), '/')}")
            else:
                # tModLoader: respeta worldpath, basta con el nombre
                config_lines.append(f"world={self._get_selected_world_name()}.wld")
            config_lines.append(f"worldname={self._get_selected_world_name()}")

        # Ruta donde el servidor guardará / buscará los mundos
        # (solo para tModLoader; Vanilla ignora worldpath de forma fiable)
        if mode == MODE_TMODLOADER:
            worlds_dir = self.get_current_worlds_dir().replace("\\", "/")
            config_lines.append(f"worldpath={worlds_dir}")

        config_lines.extend([
            f"maxplayers={self.max_players_input.text() or '16'}",
            f"port={self.server_port_input.text() or DEFAULT_PORT}",
            f"password={self.server_pass_input.text()}",
            f"upnp={'1' if self.upnp_checkbox.isChecked() else '0'}",
            "motd=TERRARIANOS LAUNCHER",
        ])

        # Ruta de mods fija (solo tModLoader)
        if mode == MODE_TMODLOADER:
            modpath = os.path.join(self.tmod_dir, "Mods").replace("\\", "/")
            config_lines.append(f"modpath={modpath}")

        config_lines.append("")

        if mode == MODE_TMODLOADER:
            config_path = os.path.join(self.tmod_dir, "serverconfig.txt")
        else:
            config_path = os.path.join(self.vanilla_dir, "serverconfig.txt")

        try:
            with open(config_path, "w", encoding="utf-8") as f:
                f.write("\n".join(config_lines))
        except Exception as e:
            print(f"[Config] Error escribiendo serverconfig.txt: {e}")

        # ─── Construir comando ───
        if mode == MODE_TMODLOADER:
            busybox = os.path.join(self.tmod_dir, "LaunchUtils", "busybox64.exe")
            script_caller = os.path.join(self.tmod_dir, "LaunchUtils", "ScriptCaller.sh")

            if not os.path.exists(busybox) or not os.path.exists(script_caller):
                raise FileNotFoundError(
                    f"No se encontró busybox64.exe o ScriptCaller.sh en:\n"
                    f"{os.path.join(self.tmod_dir, 'LaunchUtils')}"
                )

            args = [
                busybox, "bash", script_caller,
                "-server",
                "-config", "serverconfig.txt",
                "-steam" if use_steam else "-nosteam",
            ]
            return args, self.tmod_dir
        else:
            bat_path = os.path.join(self.vanilla_dir, "start-server.bat")
            if not os.path.exists(bat_path):
                raise FileNotFoundError(
                    f"No se encontró start-server.bat en:\n{self.vanilla_dir}"
                )
            return [bat_path], self.vanilla_dir

    # ─────────────────────────────────────────────
    #  ACCIONES DEL SERVIDOR
    # ─────────────────────────────────────────────
    def server_action(self):
        if self.server_running:
            self.stop_server()
        else:
            self.start_server()

    def start_server(self):
        if self.server_running:
            return

        if not WINPTY_OK:
            QMessageBox.critical(
                self, "Falta pywinpty",
                "El launcher necesita <b>pywinpty</b> para controlar el servidor.\n\n"
                "Instálalo con:\n"
                "<code>pip install pywinpty</code>"
            )
            return

        world_path = self._get_selected_world_path()
        is_new = (world_path == "")

        if is_new:
            reply = QMessageBox.question(
                self, "Crear mundo nuevo",
                "Has elegido <b>crear un mundo nuevo</b>.\n\n"
                "Ve a la pestaña <b>📜 Log</b> y responde a las preguntas "
                "del servidor:\n"
                "• Nombre del mundo\n"
                "• Tamaño (1=Pequeño, 2=Mediano, 3=Grande)\n"
                "• Dificultad (0=Clásico, 1=Experto, 2=Maestro, 3=Viaje)\n"
                "• Bioma maligno (1=Aleatorio, 2=Corrupción, 3=Carmesí)\n"
                "• Semilla (opcional)\n\n"
                "Cuando el mundo termine de crearse, el servidor se detendrá "
                "automáticamente y el mundo aparecerá en la lista.\n\n"
                "¿Continuar?",
                QMessageBox.Ok | QMessageBox.Cancel,
                QMessageBox.Ok,
            )
            if reply != QMessageBox.Ok:
                return

        self._creating_new_world = is_new

        try:
            use_steam = self.steam_checkbox.isChecked()
            cmd, cwd = self._build_server_command(use_steam=use_steam)
        except FileNotFoundError as e:
            QMessageBox.critical(self, "Error", str(e))
            return

        self.server_log.clear()
        self.server_log.appendPlainText("=== Arrancando servidor ===\n")

        if self._creating_new_world:
            self.server_log.appendPlainText(
                "📝 Modo: CREAR MUNDO NUEVO.\n"
                "Responde a las preguntas del servidor desde la casilla de abajo.\n"
                "Cuando el mundo termine de crearse, el servidor se detendrá "
                "automáticamente.\n"
            )

        try:
            self.server_process = winpty.PtyProcess.spawn(cmd, cwd=cwd)
            self.server_running = True
            self.server_status.setText("🟢 Servidor en ejecución")
            self.server_main_button.setText("⏹ DETENER SERVIDOR")
            self.btn_send_command.setEnabled(True)

            self.server_reader = ServerReaderThread(self.server_process)
            self.server_reader.line_received.connect(self.append_server_log)
            self.server_reader.process_ended.connect(self.on_server_ended)
            self.server_reader.start()

            self._update_music_state()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo arrancar:\n{e}")
            self.server_running = False

    def stop_server(self):
        if not self.server_running or not self.server_process:
            return

        reply = QMessageBox.question(
            self, "Detener servidor",
            "¿Detener el servidor?\n\nSe guardará el mundo.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        self.server_main_button.setEnabled(False)
        self.server_status.setText("⏳ Deteniendo servidor...")

        try:
            self.server_process.write("exit\r\n")
            self.append_server_log("[Launcher] Enviado 'exit'.")
        except Exception:
            pass

        QTimer.singleShot(SERVER_STOP_TIMEOUT_MS, self._force_kill_server)

    def _force_kill_server(self):
        if self.server_process and self.server_process.isalive():
            try:
                self.server_process.terminate(force=True)
                self.append_server_log("[Launcher] Servidor forzado a cerrar.")
            except Exception:
                pass

    def on_server_ended(self, code):
        self.server_running = False
        self.server_process = None
        self.server_status.setText("🔴 Servidor detenido")
        self.server_main_button.setText("▶ ARRANCAR SERVIDOR")
        self.server_main_button.setEnabled(True)
        self.append_server_log("\n=== Servidor terminado ===")
        if hasattr(self, "btn_send_command"):
            self.btn_send_command.setEnabled(False)
        self._update_music_state()

    def append_server_log(self, line):
        if not line.strip():
            return

        self.server_log.appendPlainText(line)

        # Detección de mundo creado
        if getattr(self, "_creating_new_world", False):
            if WORLD_DONE_MARKER in line and "100" in line:
                self._creating_new_world = False
                self.server_log.appendPlainText(
                    "\n✅ Mundo creado. Deteniendo servidor automáticamente...\n"
                )
                QTimer.singleShot(500, self._on_world_created)

    def _on_world_created(self):
        """Envía exit al servidor y espera cierre."""
        try:
            if self.server_process and self.server_process.isalive():
                self.server_process.write("exit\r\n")
        except Exception:
            pass
        QTimer.singleShot(3000, self._force_kill_server)
        QTimer.singleShot(3500, self._finalize_new_world)

    def _finalize_new_world(self):
        """Tras crear un mundo, refresca la lista y pregunta si quiere arrancarlo."""
        # Refrescar la lista para que aparezca el mundo nuevo
        self.refresh_worlds_list()

        # Coger el último mundo creado (el primero de la lista tras "Crear nuevo")
        if self.world_combo.count() <= 1:
            QMessageBox.information(
                self, "Mundo creado",
                "El mundo se ha creado, pero no se ha detectado en la carpeta.\n\n"
                f"Búscalo en:\n{self.get_current_worlds_dir()}"
            )
            return

        # Seleccionar el primer mundo real (índice 1, tras "Crear mundo nuevo")
        self.world_combo.setCurrentIndex(1)
        nuevo_mundo = self.world_combo.currentText()

        # Preguntar si quiere arrancar el servidor con ese mundo
        reply = QMessageBox.question(
            self, "Mundo creado",
            f"✅ Mundo «{nuevo_mundo}» creado correctamente.\n\n"
            "¿Quieres arrancar el servidor ahora con este mundo?\n\n"
            "• Sí → se arranca inmediatamente\n"
            "• No → puedes seleccionarlo en la pestaña Servidor y arrancarlo cuando quieras",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )

        if reply == QMessageBox.Yes:
            # Arrancar el servidor con el mundo recién creado
            QTimer.singleShot(200, self.start_server)
        else:
            QMessageBox.information(
                self, "Mundo guardado",
                f"El mundo «{nuevo_mundo}» está seleccionado en la pestaña Servidor.\n\n"
                "Pulsa ARRANCAR SERVIDOR cuando quieras jugar."
            )

    def send_server_command(self):
        if not self.server_running or not self.server_process:
            return
        texto = self.cmd_input.text().strip()
        try:
            self.server_process.write(texto + "\r\n")
            self.append_server_log(f"> {texto if texto else '(enter)'}")
        except Exception as e:
            self.append_server_log(f"[Launcher] Error enviando comando: {e}")
        self.cmd_input.clear()

    # ─────────────────────────────────────────────
    #  LOG
    # ─────────────────────────────────────────────
    def build_log_tab(self, parent):
        layout = QVBoxLayout(parent)
        layout.setSpacing(10)
        layout.setContentsMargins(14, 14, 14, 14)

        header = QLabel(
            "📜 Consola del servidor — usa esta casilla para responder "
            "a las preguntas del servidor y enviar comandos."
        )
        header.setObjectName("panel_title")
        header.setWordWrap(True)
        layout.addWidget(header)

        self.server_log = QPlainTextEdit()
        self.server_log.setReadOnly(True)
        self.server_log.setMaximumBlockCount(SERVER_READER_LINES)
        self.server_log.setPlaceholderText("Aquí verás el log del servidor...")
        layout.addWidget(self.server_log, stretch=1)

        cmd_row = QHBoxLayout()
        cmd_row.setSpacing(6)

        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText(
            "Escribe aquí y pulsa Enter (responde al servidor o envía comandos)"
        )
        self.cmd_input.returnPressed.connect(self.send_server_command)
        cmd_row.addWidget(self.cmd_input, stretch=1)

        self.btn_send_command = QPushButton("▶ Enviar")
        self.btn_send_command.setObjectName("server_main_button")
        self.btn_send_command.clicked.connect(self.send_server_command)
        self.btn_send_command.setEnabled(False)
        cmd_row.addWidget(self.btn_send_command)

        layout.addLayout(cmd_row)

    # ─────────────────────────────────────────────
    #  RED
    # ─────────────────────────────────────────────
    def build_network_tab(self, parent):
        layout = QVBoxLayout(parent)
        layout.setSpacing(10)
        layout.setContentsMargins(14, 14, 14, 14)

        info = QLabel(
            "🌐 Direcciones para conectarse a tu servidor.\n"
            "El puerto por defecto de Terraria es 7777."
        )
        info.setWordWrap(True)
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("color: #a8d8ea; padding: 4px;")
        layout.addWidget(info)

        panel, content = self.make_panel("Terraria · tModLoader · Vanilla")
        self.java_ipv4_value = self._make_copy_row(
            content, "IPv4:", "Consultando...", self.copy_java_ipv4
        )
        self.java_ipv6_value = self._make_copy_row(
            content, "IPv6:", "Consultando...", self.copy_java_ipv6
        )
        layout.addWidget(panel)

        self.api_status_label = QLabel("")
        self.api_status_label.setObjectName("status_info")
        self.api_status_label.setWordWrap(True)
        layout.addWidget(self.api_status_label)

        footer = QLabel(
            "ℹ️ Las direcciones se consultan al abrir el launcher.<br>"
            "⚠️ El servidor <b>Vanilla</b> solo acepta conexiones <b>IPv4</b>.<br>"
            "Comparte tu IPv4 + puerto con tus amigos."
        )
        footer.setWordWrap(True)
        footer.setObjectName("ram_note")
        footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer)

        layout.addStretch()

    def _make_copy_row(self, parent_layout, label_text, initial, callback):
        row = QHBoxLayout()
        row.setSpacing(8)

        lbl = QLabel(label_text)
        lbl.setObjectName("field_label")
        lbl.setFixedWidth(50)
        row.addWidget(lbl)

        value_lbl = QLabel(initial)
        value_lbl.setObjectName("ip_display")
        value_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        row.addWidget(value_lbl, stretch=1)

        btn = QPushButton("📋")
        btn.setObjectName("copy_button")
        btn.setToolTip("Copiar al portapapeles")
        btn.clicked.connect(callback)
        row.addWidget(btn)

        parent_layout.addLayout(row)
        return value_lbl

    def _copy_to_clipboard(self, text):
        if not text or text in ("Consultando...", "(no disponible)", "(solo IPv4)"):
            QToolTip.showText(QCursor.pos(), "⚠️ Nada que copiar", self)
            return
        QApplication.clipboard().setText(text)
        QToolTip.showText(QCursor.pos(), f"✅ Copiado: {text}", self)

    def copy_java_ipv4(self):
        self._copy_to_clipboard(self.java_ipv4_value.text())

    def copy_java_ipv6(self):
        self._copy_to_clipboard(self.java_ipv6_value.text())

    def _load_ip_once(self):
        for lbl in (self.java_ipv4_value, self.java_ipv6_value):
            lbl.setText("Consultando...")
        task = IPLookupTask()
        task.signals.result_ready.connect(self.on_ip_ready)
        task.signals.error_occurred.connect(self.on_ip_error)
        self.thread_pool.start(task)

    def on_ip_ready(self, ipv4, ipv6):
        if ipv4 and ipv4 not in ("(no disponible)",):
            self.java_ipv4_value.setText(f"{ipv4}:{DEFAULT_PORT}")
        else:
            self.java_ipv4_value.setText("(no disponible)")

        if ipv6 and ipv6 not in ("(solo IPv4)", "(no disponible)"):
            self.java_ipv6_value.setText(f"[{ipv6}]:{DEFAULT_PORT}")
        else:
            self.java_ipv6_value.setText("(no disponible)")

        if not self.api_status_msg if hasattr(self, "api_status_msg") else True:
            self.api_status_label.setText("✅ IPs consultadas correctamente")

    def on_ip_error(self, error_msg):
        for lbl in (self.java_ipv4_value, self.java_ipv6_value):
            lbl.setText("(no disponible)")
        self.api_status_label.setText(f"⚠️ Error de red: {error_msg}")

    # ─────────────────────────────────────────────
    #  MODS
    # ─────────────────────────────────────────────
    def build_mods_tab(self, parent):
        layout = QVBoxLayout(parent)
        layout.setSpacing(10)
        layout.setContentsMargins(14, 14, 14, 14)

        header = QLabel(
            "🧩 Activa o desactiva mods de tModLoader.\n"
            "Los mods activos se escriben en enabled.json.\n"
            "Los archivos .tmod deben estar en tModLoader/Mods/."
        )
        header.setWordWrap(True)
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("color: #a8d8ea; padding: 4px;")
        layout.addWidget(header)

        self.mods_list = QListWidget()
        self.mods_list.itemClicked.connect(self.toggle_mod)
        layout.addWidget(self.mods_list, stretch=1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        btn_refresh = QPushButton("🔄 Refrescar lista")
        btn_refresh.clicked.connect(self.refresh_mods_list)
        btn_row.addWidget(btn_refresh)

        btn_open = QPushButton("📁 Abrir carpeta Mods")
        btn_open.clicked.connect(self.open_mods_folder)
        btn_row.addWidget(btn_open)

        layout.addLayout(btn_row)

        self.mods_status = QLabel("—")
        self.mods_status.setAlignment(Qt.AlignCenter)
        self.mods_status.setStyleSheet(
            "color: #a8d8ea; padding: 6px; background: rgba(0,0,0,0.3);"
            "border-radius: 6px;"
        )
        layout.addWidget(self.mods_status)

    def refresh_mods_list(self):
        self.mods_list.clear()
        mods_dir = self.tmod_mods_dir

        if not os.path.exists(mods_dir):
            self.mods_status.setText("Carpeta tModLoader/Mods/ no existe todavía.")
            return

        try:
            files = [f for f in os.listdir(mods_dir) if f.endswith(".tmod")]
        except Exception as e:
            self.mods_status.setText(f"Error leyendo Mods/: {e}")
            return

        if not files:
            self.mods_status.setText("No hay mods .tmod en la carpeta.")
            return

        enabled = self._load_enabled_mods()

        for f in sorted(files):
            name = f[:-5]
            item = QListWidgetItem()
            is_on = name in enabled
            item.setText(f"{'✅  ACTIVADO' if is_on else '❌  DESACTIVADO'}   —   {name}")
            item.setData(Qt.UserRole, name)
            item.setForeground(QColor("#7fff7f") if is_on else QColor("#888"))
            self.mods_list.addItem(item)

        self.mods_status.setText(
            f"{len(files)} mod(s) · {len(enabled)} activo(s). "
            "Haz clic en un mod para activarlo/desactivarlo."
        )

    def _load_enabled_mods(self):
        enabled_path = os.path.join(self.tmod_mods_dir, "enabled.json")
        if not os.path.exists(enabled_path):
            return []
        try:
            with open(enabled_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception as e:
            print(f"[Mods] Error leyendo enabled.json: {e}")
        return []

    def _save_enabled_mods(self, enabled_list):
        enabled_path = os.path.join(self.tmod_mods_dir, "enabled.json")
        try:
            with open(enabled_path, "w", encoding="utf-8") as f:
                json.dump(sorted(enabled_list), f, indent=2)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar enabled.json:\n{e}")

    def toggle_mod(self, item):
        name = item.data(Qt.UserRole)
        if not name:
            return

        enabled = self._load_enabled_mods()

        if name in enabled:
            enabled.remove(name)
            nuevo_estado = "desactivado"
        else:
            enabled.append(name)
            nuevo_estado = "activado"

        self._save_enabled_mods(enabled)

        is_on = name in enabled
        item.setText(f"{'✅  ACTIVADO' if is_on else '❌  DESACTIVADO'}   —   {name}")
        item.setForeground(QColor("#7fff7f") if is_on else QColor("#888"))

        self.mods_status.setText(f"Mod «{name}» {nuevo_estado}.")

    def open_mods_folder(self):
        path = self.tmod_mods_dir
        os.makedirs(path, exist_ok=True)
        try:
            if os.name == "nt":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo abrir la carpeta:\n{e}")

    # ─────────────────────────────────────────────
    #  INFO
    # ─────────────────────────────────────────────
    def build_info_tab(self, parent):
        outer = QVBoxLayout(parent)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(10)
        layout.setContentsMargins(14, 14, 14, 14)

        panel_a, content_a = self.make_panel("👤 Creador")
        author_row = QHBoxLayout()
        author_row.setSpacing(20)

        photo = QLabel()
        photo.setFixedSize(120, 120)
        photo.setAlignment(Qt.AlignCenter)
        photo.setStyleSheet(
            "background: rgba(0,0,0,0.4); border-radius: 60px;"
            "border: 2px solid rgba(233,69,96,0.6); color: #666;"
        )
        author_path = resource_path(os.path.join("assets", "author.png"))
        if os.path.exists(author_path):
            pixmap = QPixmap(author_path)
            if not pixmap.isNull():
                photo.setPixmap(pixmap.scaled(
                    116, 116, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
                ))
        else:
            photo.setText("🖼️\nSin foto")
        author_row.addWidget(photo)

        info_col = QVBoxLayout()
        info_col.setSpacing(6)
        name_lbl = QLabel(LAUNCHER_AUTHOR)
        name_lbl.setStyleSheet("color: #e94560; font-size: 22px; font-weight: bold;")
        info_col.addWidget(name_lbl)
        role_lbl = QLabel("Desarrollador del proyecto TERRARIA LAUNCHER")
        role_lbl.setStyleSheet("color: #a8d8ea; font-size: 13px;")
        role_lbl.setWordWrap(True)
        info_col.addWidget(role_lbl)
        info_col.addStretch()
        author_row.addLayout(info_col, stretch=1)
        content_a.addLayout(author_row)
        layout.addWidget(panel_a)

        panel_v, content_v = self.make_panel("Terraria Launcher")
        vgrid = QGridLayout()
        vgrid.addWidget(self._field("Versión:"), 0, 0)
        v_lbl = QLabel(f"v{LAUNCHER_VERSION}")
        v_lbl.setStyleSheet("color: #e94560; font-weight: bold; font-size: 13px;")
        vgrid.addWidget(v_lbl, 0, 1)
        vgrid.setColumnStretch(1, 1)
        content_v.addLayout(vgrid)

        desc = QLabel(
            "<h3 style='color: #e94560;'>Terraria Launcher</h3>"
            "<p>El propósito principal de este proyecto es doble:</p>"
            "<p>1. Facilitar al usuario final una <b>copia legal DRM-free "
            "de Terraria</b> junto con un <b>gestor completo</b> para montar "
            "y administrar un servidor.</p>"
            "<p>2. Ofrecer una <b>solución a usuarios con CGNAT</b> que solo "
            "cuentan con <b>IPv6</b>, mediante el mod <code>IPv6Remapper</code> "
            "y la configuración dual del launcher.</p>"

            "<h3 style='color: #e94560;'>🎮 Modos disponibles</h3>"
            "<p><b>• tModLoader</b><br>"
            "Servidor y cliente con mods. Acepta conexiones por IPv4 e IPv6. "
            "Puede usar las funciones de Steam (overlay, invitaciones) o "
            "desactivarlas, sin afectar al crossplay por IP.</p>"

            "<p><b>• Vanilla</b><br>"
            "Servidor y cliente originales de Terraria (GOG). Sin mods, "
            "sin funciones de Steam. ⚠️ Solo acepta conexiones por IPv4.</p>"

            "<h3 style='color: #e94560;'>🖥️ Servidor</h3>"
            "<p>Arranca el servidor dedicado de cada modo con configuración "
            "desde la interfaz:</p>"
            "<p>• Máximo de jugadores, puerto, contraseña<br>"
            "• Reenvío automático de puertos (UPnP)<br>"
            "• Crear mundos nuevos o cargar existentes<br>"
            "• Interacción completa con la consola del servidor en vivo<br>"
            "• Detección automática de la creación del mundo</p>"

            "<h3 style='color: #e94560;'>🌍 Mundos</h3>"
            "<p>Los mundos se guardan en subcarpetas por modo:</p>"
            "<p><code>Worlds/tModLoader/</code> y <code>Worlds/Vanilla/</code></p>"
            "<p>El launcher escanea también las carpetas de Documentos por "
            "si tienes mundos creados desde el cliente.</p>"

            "<h3 style='color: #e94560;'>🧩 Mods (solo tModLoader)</h3>"
            "<p>Activa y desactiva mods desde la pestaña <b>Mods</b>. "
            "Los cambios se escriben en <code>enabled.json</code>.</p>"

            "<h3 style='color: #e94560;'>🌐 Red y CGNAT</h3>"
            "<p>Consulta tu IP pública (IPv4 e IPv6) para compartir con "
            "tus amigos. Puerto por defecto: <b>7777</b>.</p>"
            "<p>Si tu operador te tiene detrás de <b>CGNAT</b> (no tienes "
            "IPv4 pública), el launcher sigue siendo útil: activa el mod "
            "<code>IPv6Remapper</code> y tus amigos podrán conectarse por "
            "IPv6 directamente.</p>"

            "<h3 style='color: #e94560;'>🔒 Privacidad y legalidad</h3>"
            "<p>No se envían datos personales a ningún servidor. Solo se "
            "consulta tu IP pública desde <code>api.ipify.org</code> para "
            "mostrártela en la pestaña Red.</p>"
            "<p>Terraria es propiedad de Re-Logic. Este launcher no "
            "redistribuye el juego, solo facilita su uso mediante la copia "
            "<b>DRM-free de GOG</b> que el usuario ya posee legalmente.</p>"
        )
        desc.setWordWrap(True)
        desc.setTextFormat(Qt.RichText)
        desc.setStyleSheet(
            "color: #e0e0e0; font-size: 12px; padding: 8px 4px; "
            "line-height: 160%;"
        )
        content_v.addWidget(desc)
        layout.addWidget(panel_v)

        btns = QHBoxLayout()
        btns.addStretch()

        btn_gh = QPushButton("  GitHub")
        gh_icon = resource_path(os.path.join("assets", "github.png"))
        if os.path.exists(gh_icon):
            btn_gh.setIcon(QIcon(gh_icon))
            btn_gh.setIconSize(QSize(20, 20))
        btn_gh.clicked.connect(self.open_github_link)
        btns.addWidget(btn_gh)

        btn_dc = QPushButton("💬 Discord")
        btn_dc.clicked.connect(lambda: self.open_discord_link(None))
        btns.addWidget(btn_dc)

        btn_w = QPushButton("🌐 Web")
        btn_w.clicked.connect(self.open_web_link)
        btns.addWidget(btn_w)

        btns.addStretch()
        layout.addLayout(btns)
        layout.addStretch()

        scroll.setWidget(container)
        outer.addWidget(scroll)

    # ─────────────────────────────────────────────
    #  ACCIONES GENERALES
    # ─────────────────────────────────────────────
    def open_launcher_folder(self):
        try:
            if os.name == "nt":
                os.startfile(self.base_dir)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", self.base_dir])
            else:
                subprocess.Popen(["xdg-open", self.base_dir])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo abrir la carpeta:\n{e}")

    def open_web_link(self):
        QDesktopServices.openUrl(QUrl(WEBSITE_URL))

    def open_github_link(self):
        QDesktopServices.openUrl(QUrl(GITHUB_URL))

    def open_discord_link(self, event):
        QDesktopServices.openUrl(QUrl(DISCORD_URL))


# ═══════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════
def main():
    app = QApplication(sys.argv)

    # Silenciar los avisos de sondeo de audio de Qt
    from PySide6.QtCore import QLoggingCategory
    QLoggingCategory.setFilterRules("qt.multimedia.audiodevice.probes=false")

    icon_path = resource_path(os.path.join("assets", "icon.ico"))
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    else:
        png = resource_path(os.path.join("assets", "icon.png"))
        if os.path.exists(png):
            app.setWindowIcon(QIcon(png))

    window = TerrariaLauncher()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
