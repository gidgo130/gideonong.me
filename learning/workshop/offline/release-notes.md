Reading Your Fits for offline use: the interactive modules, slides and Python scripts from
[gideonong.me/learning](https://gideonong.me/learning/), on your own computer, no internet
needed. *Español abajo.*

### Which file?

| File | What you get |
| --- | --- |
| `ReadingYourFits-Setup.exe` | Windows 10/11: every module. You can still untick modules, slides or scripts. |
| `ReadingYourFits-<module>-Setup.exe` | Windows 10/11: one module. Run more of them to add modules; they share one install. |
| `ReadingYourFits.zip` | Any system: everything. Unzip it, then open `Reading Your Fits.html`. |
| `SHA256SUMS.txt` | Checksums, to confirm a download is intact. |

### Installing on Windows

- The installer is **not signed yet**, so Windows SmartScreen may say "Windows protected your
  PC". Click **More info**, then **Run anyway**. Your browser may also ask you to keep the file.
- It installs for your user only, with no administrator prompt, to
  `%LOCALAPPDATA%\Programs\Reading Your Fits`, and adds a Start Menu shortcut that opens the
  pages in your default browser.
- To remove it: Settings → Apps → Installed apps → Reading Your Fits → Uninstall.
- The pages fall back to your system fonts without internet; everything else works offline.
  Links to papers, Colab and gideonong.me need internet.
- To check a download: `Get-FileHash <file>` in PowerShell must match its line in
  `SHA256SUMS.txt` (upper or lower case doesn't matter).

---

Cómo leer tus ajustes de curvas, para usar sin conexión: los módulos interactivos, las
diapositivas y los scripts de Python de [gideonong.me/learning](https://gideonong.me/learning/),
en tu computadora, sin internet.

### ¿Qué archivo?

| Archivo | Qué incluye |
| --- | --- |
| `ReadingYourFits-Setup.exe` | Windows 10/11: todos los módulos. Igual puedes quitar módulos, diapositivas o scripts. |
| `ReadingYourFits-<módulo>-Setup.exe` | Windows 10/11: un módulo. Ejecuta varios para agregar módulos; comparten una misma instalación. |
| `ReadingYourFits.zip` | Cualquier sistema: todo. Descomprímelo y abre `Reading Your Fits.html`. |
| `SHA256SUMS.txt` | Sumas de verificación, para confirmar que la descarga llegó completa. |

### Instalar en Windows

- El instalador **todavía no está firmado**, así que Windows SmartScreen puede decir "Windows
  protegió tu PC". Haz clic en **Más información** y luego en **Ejecutar de todas formas**. Tu
  navegador también puede pedirte que confirmes la descarga.
- Se instala solo para tu usuario, sin pedir permisos de administrador, en
  `%LOCALAPPDATA%\Programs\Reading Your Fits`, y agrega un acceso directo en el menú Inicio que
  abre las páginas en tu navegador.
- Para quitarlo: Configuración → Aplicaciones → Aplicaciones instaladas → Reading Your Fits →
  Desinstalar.
- Sin internet, las páginas usan las fuentes de tu sistema; todo lo demás funciona sin
  conexión. Los enlaces a artículos, a Colab y a gideonong.me necesitan internet.
- Para verificar una descarga: `Get-FileHash <archivo>` en PowerShell debe coincidir con su
  línea en `SHA256SUMS.txt` (sin importar mayúsculas o minúsculas).
