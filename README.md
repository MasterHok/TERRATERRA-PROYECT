# 🌳 TERRARIA LAUNCHER

Launcher todo-en-uno para **Terraria vanilla (GOG)** y **tModLoader**, con soporte tanto para cliente como para servidor, gestión de mods y configuración de red IPv4/IPv6.

![Terraria](https://img.shields.io/badge/Terraria-1.4.5-red)
![tModLoader](https://img.shields.io/badge/tModLoader-2026.08.3.0-purple)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Licencia](https://img.shields.io/badge/Licencia-Free%20%26%20Open%20Source-green)

---

## 🎯 Propósito del proyecto

Este proyecto tiene **dos objetivos principales**:

1. **Facilitar al usuario final una copia legal DRM-free de Terraria** junto con un **gestor completo** para montar y administrar un servidor, sin necesidad de conocimientos técnicos ni de herramientas de terceros.

2. **Ofrecer una solución a usuarios con CGNAT** que solo cuentan con **IPv6**, mediante el mod `IPv6Remapper` y la configuración dual (IPv4/IPv6) del launcher. Esto permite jugar con amigos aunque el operador no asigne una IPv4 pública.

> ⚖️ **Aviso legal**: Terraria es propiedad de Re-Logic. Este launcher **no redistribuye el juego**, solo facilita el uso de la copia DRM-free de GOG que el usuario ya posee legalmente.

---

## ✨ Características

### 🎮 Cliente
- Arranca **Terraria vanilla** (`Terraria.exe`) o **tModLoader** con un solo clic.
- Selección de modo (Vanilla / tModLoader) desde la interfaz.
- Mensaje de confirmación al lanzar el juego.
- Detección automática del cierre del cliente.

### 🖥️ Servidor
- Arranca el servidor dedicado en **modo Vanilla** o **tModLoader**.
- Configuración completa desde la interfaz:
  - Modo (Vanilla / tModLoader)
  - Mundo (crear nuevo o cargar existente)
  - Máximo de jugadores
  - Puerto
  - Contraseña
  - Reenvío automático de puertos (UPnP)
  - Overlay de Steam (solo tModLoader)
- **Consola interactiva en vivo**: responde a las preguntas del servidor desde la pestaña Log.
- **Detección automática de creación de mundo**: al terminar de generarse, el servidor se detiene y el mundo aparece en la lista.
- Botón `?` con documentación integrada sobre IPv4, IPv6, CGNAT e IPv6Remapper.

### 🧩 Mods (solo tModLoader)
- Lista de mods `.tmod` en `tModLoader/Mods/`.
- Activar/desactivar con un clic.
- Los cambios se escriben en `enabled.json`.

### 🌐 Red
- Consulta tu IP pública (IPv4 e IPv6).
- Copia al portapapeles con un clic.
- Aviso específico para modo Vanilla (solo IPv4).

### 🎨 Interfaz
- Diseño con temática roja de Terraria.
- Fondo animado (GIF) configurable.
- Música de fondo con control de volumen.
- Estilos editables desde `assets/style.qss`.
- Iconos de acceso rápido: web, GitHub, Discord, carpeta del launcher.

---

## 📁 Estructura del proyecto

```
terra_project/
├── tModLoader/           # Instalación de tModLoader (descargada por el instalador)
├── Terraria/             # Instalación de Terraria vanilla (GOG)
├── Worlds/               # Mundos guardados por modo
│   ├── tModLoader/       # Mundos de tModLoader (.wld + .twld)
│   └── Vanilla/          # Mundos de vanilla (.wld)
├── assets/               # Recursos del launcher
│   ├── icon.ico
│   ├── banner.png
│   ├── fondo.gif
│   ├── fondo_info.gif
│   ├── style.qss
│   ├── web.png
│   ├── github.png
│   ├── discord.png
│   ├── author.png
│   ├── music.mp3
│   ├── click_yes.wav
│   ├── click_no.wav
│   └── dialog_intro.wav
├── config/               # Configuración (se crea sola)
│   └── settings.json
├── TERRATERRA.py         # Launcher principal
├── instalador.bat        # Instalador automático
└── README.md
```

---

## 🚀 Instalación

### Requisitos
- **Windows** 10 o superior
- **Python 3.8+** ([descargar aquí](https://www.python.org/downloads/))
- Conexión a Internet para la descarga inicial

### Instalación rápida (recomendada)

1. Descarga el `instalador.bat` de este repositorio.
2. Colócalo en una carpeta vacía (por ejemplo, `terra_project/`).
3. Doble clic en `instalador.bat`.
4. Sigue las instrucciones en pantalla.
5. El instalador hará automáticamente:
   - Verificar que Python está instalado.
   - Instalar `PySide6` y `pywinpty`.
   - Crear toda la estructura de carpetas.
   - Descargar **tModLoader v2026.08.3.0** desde GitHub.
   - Descargar el mod **IPv6Remapper-1.4.5.tmod** desde Codeberg.
   - Abrir el navegador para descargar **Terraria GOG** desde Google Drive.
   - Abrir un selector de archivos para que indiques dónde se descargó.
   - Ejecutar el instalador de Terraria con instrucciones paso a paso.

### Instalación manual (alternativa)

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/terraria-launcher.git
cd terraria-launcher

# Instalar dependencias
pip install PySide6 pywinpty

# Colocar los recursos manualmente en las carpetas correspondientes
# (tModLoader, Terraria, assets, etc.)

# Arrancar el launcher
python TERRATERRA.py
```

---

## 🎮 Uso

### Cliente
1. Abre el launcher.
2. Ve a la pestaña **🎮 Cliente**.
3. Selecciona el modo (tModLoader o Vanilla).
4. Pulsa **▶ JUGAR**.

### Servidor
1. Ve a la pestaña **🖥️ Servidor**.
2. Selecciona el modo (Vanilla o tModLoader).
3. Configura:
   - **Mundo**: elige uno existente o "Crear mundo nuevo".
   - **Max players**, **Puerto**, **Contraseña**.
   - **Overlay de Steam** (solo tModLoader).
4. Pulsa **▶ ARRANCAR SERVIDOR**.
5. Si creas un mundo nuevo, ve a la pestaña **📜 Log** y responde a las preguntas del servidor.

### Mods (tModLoader)
1. Ve a la pestaña **🧩 Mods**.
2. Los mods en `tModLoader/Mods/*.tmod` aparecen listados.
3. Haz clic en un mod para activarlo/desactivarlo.

### Red
1. Ve a la pestaña **🌐 Red**.
2. Copia tu IP pública (IPv4 o IPv6) + puerto.
3. Compártela con tus amigos.

---

## 🔧 Tecnologías usadas

| Componente | Función |
|------------|---------|
| **PySide6** | Interfaz gráfica (Qt6) |
| **pywinpty** | Pseudo-terminal para interactuar con el servidor |
| **urllib** | Consultas HTTP (IP pública, manifiestos) |
| **subprocess** | Ejecución de procesos (cliente, servidor) |
| **json** | Configuración y `enabled.json` |
| **shutil** | Gestión de archivos |

---

## 📦 Recursos externos

| Recurso | Fuente |
|---------|--------|
| **Terraria GOG** | [Google Drive](https://drive.google.com/file/d/1rp9Z_--9oLadQBjxjO0BFPyy38-aJ0U3/view) |
| **tModLoader** | [GitHub Releases](https://github.com/tModLoader/tModLoader/releases) |
| **IPv6Remapper** | [Codeberg](https://codeberg.org/EatDatPie_445/IPv6Remapper/releases) |

---

## ❓ Preguntas frecuentes

### ¿Por qué el servidor Vanilla solo acepta IPv4?
Es una limitación del servidor original de Terraria. Solo escucha en IPv4. Para IPv6, usa tModLoader con el mod `IPv6Remapper`.

### ¿Qué es CGNAT y por qué me afecta?
CGNAT (Carrier-Grade NAT) es cuando tu operador no te asigna una IPv4 pública propia. Esto significa que tus amigos **no pueden conectarse a tu servidor por IPv4**. La solución es usar **IPv6 + IPv6Remapper**.

### ¿Necesito tener Terraria en Steam?
No. Este launcher está pensado para la versión **DRM-free de GOG**. Si tienes Steam, también funciona, pero las invitaciones de Steam requieren que todos tengan Steam.

### ¿El launcher descarga el juego por mí?
**No.** El launcher facilita la instalación, pero **tú debes descargar el instalador de Terraria GOG** desde el enlace oficial. Esto es por motivos legales.

### ¿Cómo añado más mods?
Copia los archivos `.tmod` a `tModLoader/Mods/` y actívalos desde la pestaña **Mods**.

---

## 🤝 Contribuir

Las contribuciones son bienvenidas. Si encuentras un bug o quieres añadir una función:

1. Haz un fork del repositorio.
2. Crea una rama (`git checkout -b feature/nueva-funcion`).
3. Haz commit de tus cambios (`git commit -m 'Añade nueva función'`).
4. Haz push a la rama (`git push origin feature/nueva-funcion`).
5. Abre un Pull Request.

---

## 📜 Licencia

Este proyecto es **libre y sin fines de lucro**. Puedes usarlo, modificarlo y distribuirlo libremente.

> **Aviso legal**: Terraria es una marca registrada de Re-Logic. Este launcher no está afiliado con Re-Logic ni con GOG. No redistribuye el juego.

---

## 💖 Agradecimientos

- **Re-Logic** por crear Terraria.
- **tModLoader Team** por el excelente framework de mods.
- **EatDatPie_445** por el mod IPv6Remapper.
- **Comunidad de Terraria** por el soporte continuo.

---

## 📞 Contacto

- **Web**: [terrarianos.uk](https://www.terrarianos.uk)
- **Discord**: [Únete al servidor](https://discord.gg/3KgY7d4ZSW)
- **GitHub**: [MasterHok](https://github.com/MasterHok)
