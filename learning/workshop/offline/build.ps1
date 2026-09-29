# build.ps1 - stage learning/ and build the offline Windows installers and zip (Phase D).
#
#   powershell -ExecutionPolicy Bypass -File learning\workshop\offline\build.ps1             # dev build
#   powershell -ExecutionPolicy Bypass -File learning\workshop\offline\build.ps1 -Release    # release build
#   powershell -ExecutionPolicy Bypass -File learning\workshop\offline\build.ps1 -StageOnly  # stage only
#
# 1. Copies <repo>\learning\ into stage\learning\ (git-tracked and new-but-not-ignored files
#    only, so the gitignored papers never ship), minus the dev-only paths in $Exclude, plus the
#    favicon the pages point at (..\assets\glogo.ico), LICENSE, LICENSE-CONTENT and a NOTICE.
# 2. Writes stage\modules.iss and stage\modules-code.iss from learning\assets\modules.js and
#    strings-common.js: one component per ready module with optional Slides and Python parts,
#    and the Pascal that lists what is missing on disk after an install. A new module shows up
#    with no edit here or in the .iss.
# 3. Compiles ReadingYourFits.iss into dist\: the full installer and one per ready module
#    (/DOnlyModule=<slug>), then the zip (whole series, for other systems).
# 4. -Release: refuses a working tree that differs from HEAD, then copies the files under
#    version-free names into dist\release\ (what gets uploaded; the site links
#    releases/latest/download/<name>) with SHA256SUMS.txt.
# The version is read from the #define AppVersion in ReadingYourFits.iss (its only home).
# stage\ and dist\ are gitignored (learning\workshop\.gitignore). Needs git and Inno Setup 6.
[CmdletBinding()]
param([switch]$StageOnly, [switch]$Release)

# ---- Settings ----------------------------------------------------------------------------
# The repo whose learning\ folder gets packaged. Default: the clone this script sits in.
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path

# Paths (relative to the repo, forward slashes, -like wildcards) that never go into the app.
$Exclude = @(
  "learning/workshop/*",      # slide sources, figures, dev tools, this folder
  "*.md",                     # README.md, learning-plan.md
  "*.pdf",                    # papers are never hosted (gitignored anyway; belt and braces)
  "learning/assets/og/*",     # link-preview cards: only scrapers of the live site use them
  "learning/fits/*/play/*"    # marimo notebooks need HTTP and a CDN; the pages hide the link from disk
)
# Files outside learning\ that ship too (and so must be committed for a release).
$Extra = @("assets/glogo.ico", "LICENSE", "LICENSE-CONTENT")
# ------------------------------------------------------------------------------------------

$ErrorActionPreference = "Stop"
$Here  = $PSScriptRoot
$Stage = Join-Path $Here "stage"
$Dist  = Join-Path $Here "dist"
$Iss   = Join-Path $Here "ReadingYourFits.iss"
$Utf8Bom = New-Object System.Text.UTF8Encoding $true

function Fail($msg) { Write-Host "build.ps1: $msg" -ForegroundColor Red; exit 1 }

if (-not (Test-Path (Join-Path $RepoRoot "learning\assets\modules.js"))) { Fail "no learning\ folder under $RepoRoot" }
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# ---- Version and commit ------------------------------------------------------------------
$m = [regex]::Match((Get-Content $Iss -Raw -Encoding UTF8), '(?m)^#define AppVersion "([^"]+)"')
if (-not $m.Success) { Fail "no #define AppVersion in ReadingYourFits.iss" }
$Version = $m.Groups[1].Value
$Commit = (& git -C $RepoRoot rev-parse --short HEAD).Trim()
if ($LASTEXITCODE -ne 0) { Fail "git rev-parse failed (is git on PATH?)" }
$dirty = & git -C $RepoRoot status --porcelain -- learning @Extra
if ($dirty) {
  if ($Release) { Fail ("-Release needs a clean tree; uncommitted:`n" + ($dirty -join "`n")) }
  $Commit += "-dirty"
}
Write-Host "Reading Your Fits $Version ($Commit)"

# ---- 1. Stage ----------------------------------------------------------------------------
if (Test-Path $Stage) { Remove-Item $Stage -Recurse -Force }
New-Item -ItemType Directory -Path $Stage | Out-Null

$tracked = & git -C $RepoRoot -c core.quotepath=off ls-files --cached --others --exclude-standard -- learning
if ($LASTEXITCODE -ne 0) { Fail "git ls-files failed" }

$copied = 0
foreach ($rel in ($tracked | Sort-Object -Unique)) {
  $skip = $false
  foreach ($pat in $Exclude) { if ($rel -like $pat) { $skip = $true; break } }
  if ($skip) { continue }
  $src = Join-Path $RepoRoot $rel
  if (-not (Test-Path -LiteralPath $src -PathType Leaf)) { continue }   # deleted in the working tree
  $dst = Join-Path $Stage $rel
  New-Item -ItemType Directory -Path (Split-Path $dst) -Force | Out-Null
  Copy-Item -LiteralPath $src -Destination $dst
  $copied++
}

New-Item -ItemType Directory -Path (Join-Path $Stage "assets") -Force | Out-Null
Copy-Item (Join-Path $RepoRoot "assets\glogo.ico") (Join-Path $Stage "assets\glogo.ico")
Copy-Item (Join-Path $RepoRoot "LICENSE") (Join-Path $Stage "LICENSE.txt")
Copy-Item (Join-Path $RepoRoot "LICENSE-CONTENT") (Join-Path $Stage "LICENSE-CONTENT.txt")

# Keep in step with README.md -> Licensing (the standard license texts carry no scope notes).
$notice = @"
Reading Your Fits - offline copy, version $Version ($Commit)
Online: https://gideonong.me/learning/
Source and updates: https://github.com/gidgo130/gideonong.me/releases

To open it: learning\index.html (in the installed app, also the Start Menu shortcut).

Licenses
- Code (HTML, CSS, JavaScript, Python): MIT, see LICENSE.txt.
- Teaching content under learning\ (module text, strings, slides, figures, the companion
  scripts and notebooks): CC BY-SA 4.0, see LICENSE-CONTENT.txt. Share and adapt it with
  credit to "Gideon A. Ong, gideonong.me/learning", and keep adaptations under the same
  license.
- Not licensed, all rights reserved: Gideon A. Ong's name and likeness.
- Cited papers are linked by DOI and are not included.
"@
[System.IO.File]::WriteAllText((Join-Path $Stage "NOTICE.txt"), ($notice -replace "`r?`n", "`r`n"), (New-Object System.Text.UTF8Encoding $false))

$bad = Get-ChildItem $Stage -Recurse -File -Include *.md, *.pdf, *.qmd
if ($bad) { Fail ("dev-only files staged: " + ($bad.FullName -join ", ")) }

# ---- 2. Components and the missing-files check from the module registry ------------------
$modulesJs = Get-Content (Join-Path $Stage "learning\assets\modules.js") -Raw -Encoding UTF8
$stringsJs = Get-Content (Join-Path $Stage "learning\assets\strings-common.js") -Raw -Encoding UTF8
$split = $stringsJs.IndexOf("`n  es: {")
if ($split -lt 0) { Fail "strings-common.js: no 'es:' block" }
$text = @{ en = $stringsJs.Substring(0, $split); es = $stringsJs.Substring($split) }

function Str($lang, $key) {
  $mm = [regex]::Match($text[$lang], "\b$key\s*:\s*""((?:[^""\\]|\\.)*)""")
  if (-not $mm.Success) { Fail "strings-common.js: no $lang string $key" }
  return [regex]::Unescape($mm.Groups[1].Value).Replace("`r", " ").Replace("`n", " ")
}

$mods = @([regex]::Matches($modulesJs, '\{\s*key:\s*"(\w+)",\s*slug:\s*"([a-z0-9-]+)",\s*ready:\s*(true|false)\s*\}') |
  ForEach-Object { [pscustomobject]@{ Key = $_.Groups[1].Value; Slug = $_.Groups[2].Value; Ready = ($_.Groups[3].Value -eq "true") } })
if ($mods.Count -eq 0) { Fail "modules.js: no modules found" }

$fitsDir = Join-Path $Stage "learning\fits"
$known = $mods | ForEach-Object { $_.Slug }
Get-ChildItem $fitsDir -Directory | Where-Object { $known -notcontains $_.Name } | ForEach-Object {
  Write-Warning "learning\fits\$($_.Name) is not in modules.js; it is staged but not installed"
}

# A module folder splits into three parts by file name. Everything else is the page itself.
function PartOf($name) {
  if ($name -like "slides*.html") { return "slides" }
  if ($name -like "*.py" -or $name -like "*.ipynb") { return "python" }
  return "page"
}

$comps = New-Object System.Text.StringBuilder
$fileLines = New-Object System.Text.StringBuilder
$msgs = New-Object System.Text.StringBuilder
$code = New-Object System.Text.StringBuilder
[void]$comps.AppendLine('Name: "fits"; Description: "{cm:CompFits}"; Types: full compact custom')
[void]$msgs.AppendLine("en.CompFits=" + (Str en "seriesName"))
[void]$msgs.AppendLine("es.CompFits=" + (Str es "seriesName"))
[void]$code.AppendLine("{ GENERATED by build.ps1 from learning\assets\modules.js - do not edit. }")
[void]$code.AppendLine("{ Paths (relative to learning/) that are not on disk under Base, as JS string literals. }")
[void]$code.AppendLine("function OfflineMissing(Base: String): String;")
[void]$code.AppendLine("begin")
[void]$code.AppendLine("  Result := '';")

$n = 0
$ready = @()
foreach ($mod in $mods) {
  $n++
  if (-not $mod.Ready) { continue }   # the hub shows it as "In progress" with no link
  $ready += $mod.Slug
  $dir = Join-Path $fitsDir $mod.Slug
  if (-not (Test-Path (Join-Path $dir "index.html"))) { Fail "module $($mod.Slug) is ready but has no index.html" }
  $id = "fits\" + $mod.Key.ToLower()
  $cm = "Comp" + $mod.Key
  $only = "#if OnlyModule == """" || OnlyModule == ""$($mod.Slug)"""

  $parts = @{ page = @(); slides = @(); python = @() }
  Get-ChildItem $dir -File | ForEach-Object { $parts[(PartOf $_.Name)] += $_.Name }

  [void]$msgs.AppendLine("en.$cm=" + ((Str en "moduleN") -replace "\{n\}", $n) + ": " + (Str en "mod$($mod.Key)Title"))
  [void]$msgs.AppendLine("es.$cm=" + ((Str es "moduleN") -replace "\{n\}", $n) + ": " + (Str es "mod$($mod.Key)Title"))

  [void]$comps.AppendLine($only)
  [void]$comps.AppendLine("Name: ""$id""; Description: ""{cm:$cm}""; Types: full compact custom; Flags: checkablealone")
  $src = "stage\learning\fits\$($mod.Slug)"
  $dst = "{app}\learning\fits\$($mod.Slug)"
  [void]$fileLines.AppendLine($only)
  $partExcl = ($parts.slides + $parts.python) -join ","
  $excl = if ($partExcl) { "; Excludes: ""$partExcl""" } else { "" }
  [void]$fileLines.AppendLine("Source: ""$src\*""$excl; DestDir: ""$dst""; Components: $id; Flags: ignoreversion recursesubdirs")

  $base = "Base + 'fits\$($mod.Slug)\"
  [void]$code.AppendLine("  if not FileExists($base" + "index.html') then")
  [void]$code.AppendLine("    Result := Result + ',""fits/$($mod.Slug)/""'")
  [void]$code.AppendLine("  else begin")
  foreach ($p in @("slides", "python")) {
    if ($parts[$p].Count -eq 0) { continue }
    [void]$comps.AppendLine("Name: ""$id\$p""; Description: ""{cm:Part$p}""; Types: full")
    foreach ($f in $parts[$p]) {
      [void]$fileLines.AppendLine("Source: ""$src\$f""; DestDir: ""$dst""; Components: $id\$p; Flags: ignoreversion")
      [void]$code.AppendLine("    if not FileExists($base$f') then Result := Result + ',""fits/$($mod.Slug)/$f""';")
    }
  }
  [void]$code.AppendLine("  end;")
  [void]$comps.AppendLine("#endif")
  [void]$fileLines.AppendLine("#endif")
}
[void]$code.AppendLine("  if Result <> '' then Delete(Result, 1, 1);")
[void]$code.AppendLine("end;")

$generated = "; GENERATED by build.ps1 from learning\assets\modules.js - do not edit.`r`n" +
  "[Components]`r`n" + $comps.ToString() + "`r`n[Files]`r`n" + $fileLines.ToString() +
  "`r`n[CustomMessages]`r`n" + $msgs.ToString()
[System.IO.File]::WriteAllText((Join-Path $Stage "modules.iss"), $generated, $Utf8Bom)
[System.IO.File]::WriteAllText((Join-Path $Stage "modules-code.iss"), $code.ToString(), $Utf8Bom)

$mb = "{0:N1}" -f ((Get-ChildItem $Stage -Recurse -File | Measure-Object Length -Sum).Sum / 1MB)
Write-Host "Staged $copied files from learning\ ($mb MB); modules: $($ready -join ', ')"
if ($StageOnly) { exit 0 }

# ---- 3. Compile --------------------------------------------------------------------------
function Find-Iscc {
  if ($env:ISCC -and (Test-Path $env:ISCC)) { return $env:ISCC }
  $cmd = Get-Command ISCC.exe -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }
  $keys = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1",
          "HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1",
          "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1"
  foreach ($k in $keys) {
    $loc = (Get-ItemProperty $k -ErrorAction SilentlyContinue).InstallLocation
    if ($loc -and (Test-Path (Join-Path $loc "ISCC.exe"))) { return (Join-Path $loc "ISCC.exe") }
  }
  foreach ($p in "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe", "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
                 "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe") {
    if (Test-Path $p) { return $p }
  }
  return $null
}
$iscc = Find-Iscc
if (-not $iscc) { Fail "ISCC.exe not found. Install Inno Setup 6: winget install JRSoftware.InnoSetup (or set `$env:ISCC)" }

# dist\ holds only the latest build.
if (Test-Path $Dist) { Remove-Item $Dist -Recurse -Force }
Write-Host "Compiling with $iscc"
foreach ($only in @("") + $ready) {
  $isccArgs = @("/Q", "/DBuildCommit=$Commit")
  if ($only) { $isccArgs += "/DOnlyModule=$only" }
  & $iscc @isccArgs $Iss
  if ($LASTEXITCODE -ne 0) { Fail ("ISCC failed for " + $(if ($only) { $only } else { "the full installer" }) + " (exit $LASTEXITCODE)") }
}

# ---- Zip (whole series; forward-slash entry names so it unpacks anywhere) ----------------
Add-Type -AssemblyName System.IO.Compression
$zipPath = Join-Path $Dist "ReadingYourFits-$Version.zip"
$root = "Reading Your Fits/"
$fs = [System.IO.File]::Open($zipPath, [System.IO.FileMode]::Create)
$zip = New-Object System.IO.Compression.ZipArchive($fs, [System.IO.Compression.ZipArchiveMode]::Create)
function Add-ZipEntry($name, [byte[]]$bytes) {
  $e = $zip.CreateEntry($root + $name, [System.IO.Compression.CompressionLevel]::Optimal)
  $s = $e.Open(); $s.Write($bytes, 0, $bytes.Length); $s.Dispose()
}
$ascii = [System.Text.Encoding]::ASCII
Get-ChildItem $Stage -Recurse -File | Where-Object { $_.Extension -ne ".iss" } | ForEach-Object {
  $rel = $_.FullName.Substring($Stage.Length + 1).Replace("\", "/")
  $bytes = [System.IO.File]::ReadAllBytes($_.FullName)
  if ($rel -eq "learning/assets/modules.js") {
    # Same manifest the installer writes; the zip always holds everything, so nothing is missing.
    $bytes += $ascii.GetBytes("`r`n// Added by build.ps1 for the zip (learning/workshop/offline/): paths this copy lacks.`r`n" +
      "window.LEARN_OFFLINE = { version: ""$Version"", commit: ""$Commit"", missing: [] };`r`n")
  }
  Add-ZipEntry $rel $bytes
}
Add-ZipEntry "Reading Your Fits.html" ($ascii.GetBytes(
  "<!DOCTYPE html>`r`n<meta charset=""utf-8"">`r`n<meta http-equiv=""refresh"" content=""0; url=learning/index.html"">`r`n" +
  "<title>Reading Your Fits</title>`r`n<a href=""learning/index.html"">Open Reading Your Fits</a>`r`n"))
$zip.Dispose(); $fs.Dispose()

Get-ChildItem $Dist -File | ForEach-Object { Write-Host ("  {0,-44} {1,6:N1} MB" -f $_.Name, ($_.Length / 1MB)) }

# ---- 4. Release copies ------------------------------------------------------------------
if (-not $Release) { Write-Host "Dev build ($Commit). Use -Release for the upload set." -ForegroundColor Green; exit 0 }
$Out = Join-Path $Dist "release"
New-Item -ItemType Directory -Path $Out | Out-Null
Get-ChildItem $Dist -File | ForEach-Object {
  Copy-Item $_.FullName (Join-Path $Out ($_.Name -replace "-$([regex]::Escape($Version))(?=\.(exe|zip)$)", ""))
}
$sums = Get-ChildItem $Out -File | Sort-Object Name | ForEach-Object {
  (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower() + "  " + $_.Name
}
[System.IO.File]::WriteAllText((Join-Path $Out "SHA256SUMS.txt"), (($sums -join "`n") + "`n"), $ascii)
Write-Host "Release set for offline-v$Version ($Commit) in $Out" -ForegroundColor Green
Get-ChildItem $Out -File | ForEach-Object { Write-Host "  $($_.Name)" }
