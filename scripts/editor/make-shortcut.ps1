# Creates a desktop shortcut "Site editor" that runs launch.pyw with the real
# pythonw.exe (pythoncore-3.14, not Inkscape's python). Run once, from anywhere:
#   powershell -ExecutionPolicy Bypass -File scripts\editor\make-shortcut.ps1
# Re-running just rewrites the shortcut.

$ErrorActionPreference = "Stop"

$editorDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$launcher  = Join-Path $editorDir "launch.pyw"
$pythonw   = Join-Path $env:LOCALAPPDATA "Python\pythoncore-3.14-64\pythonw.exe"

if (-not (Test-Path $launcher)) { throw "launch.pyw not found next to this script ($launcher)" }
if (-not (Test-Path $pythonw)) {
    throw "pythonw.exe not found at $pythonw. Edit `$pythonw in this script if your Python lives elsewhere."
}

$desktop  = [Environment]::GetFolderPath("Desktop")
$linkPath = Join-Path $desktop "Site editor.lnk"

$shell = New-Object -ComObject WScript.Shell
$lnk = $shell.CreateShortcut($linkPath)
$lnk.TargetPath       = $pythonw
$lnk.Arguments        = '"' + $launcher + '"'
$lnk.WorkingDirectory = $editorDir
$lnk.Description      = "gideonong.me local content editor"
$lnk.WindowStyle      = 7   # minimized (pythonw has no window anyway)
$lnk.IconLocation = "$env:SystemRoot\System32\shell32.dll,70"   # a generic "document + pen" icon
$lnk.Save()

Write-Host "Shortcut written: $linkPath"
Write-Host "  target : $pythonw"
Write-Host "  args   : $($lnk.Arguments)"
