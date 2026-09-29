# build.ps1 - stage learning/ and compile the offline Windows installer (Phase D).
#
#   powershell -ExecutionPolicy Bypass -File learning\workshop\offline\build.ps1
#   powershell -ExecutionPolicy Bypass -File learning\workshop\offline\build.ps1 -StageOnly
#
# 1. Copies <repo>\learning\ into stage\learning\ (git-tracked and new-but-not-ignored files
#    only, so the gitignored papers never ship), minus the dev-only paths in $Exclude.
# 2. Copies the favicon the pages point at (..\assets\glogo.ico) into stage\assets\.
# 3. Writes stage\modules.iss and stage\modules-code.iss from learning\assets\modules.js and
#    strings-common.js: one installer component per ready module, each with optional Slides and
#    Python parts. A new module shows up in the installer with no edit here or in the .iss.
# 4. Runs ISCC.exe on ReadingYourFits.iss -> dist\ReadingYourFits-Setup-<version>.exe.
# stage\ and dist\ are gitignored (learning\workshop\.gitignore). Needs git and Inno Setup 6.
[CmdletBinding()]
param([switch]$StageOnly)

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
# ------------------------------------------------------------------------------------------

$ErrorActionPreference = "Stop"
$Here  = $PSScriptRoot
$Stage = Join-Path $Here "stage"
$Utf8Bom = New-Object System.Text.UTF8Encoding $true

function Fail($msg) { Write-Host "build.ps1: $msg" -ForegroundColor Red; exit 1 }

if (-not (Test-Path (Join-Path $RepoRoot "learning\assets\modules.js"))) { Fail "no learning\ folder under $RepoRoot" }

# ---- 1. Stage learning\ ------------------------------------------------------------------
if (Test-Path $Stage) { Remove-Item $Stage -Recurse -Force }
New-Item -ItemType Directory -Path $Stage | Out-Null

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$files = & git -C $RepoRoot -c core.quotepath=off ls-files --cached --others --exclude-standard -- learning
if ($LASTEXITCODE -ne 0) { Fail "git ls-files failed (is git on PATH?)" }

$copied = 0
foreach ($rel in ($files | Sort-Object -Unique)) {
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

# ---- 2. Favicon (every page links ../assets/glogo.ico relative to learning/) -------------
New-Item -ItemType Directory -Path (Join-Path $Stage "assets") -Force | Out-Null
Copy-Item (Join-Path $RepoRoot "assets\glogo.ico") (Join-Path $Stage "assets\glogo.ico")

# Safety: nothing dev-only or unhostable slipped through.
$bad = Get-ChildItem $Stage -Recurse -File -Include *.md, *.pdf, *.qmd
if ($bad) { Fail ("dev-only files staged: " + ($bad.FullName -join ", ")) }

# ---- 3. Components from the module registry ----------------------------------------------
$modulesJs = Get-Content (Join-Path $Stage "learning\assets\modules.js") -Raw -Encoding UTF8
$stringsJs = Get-Content (Join-Path $Stage "learning\assets\strings-common.js") -Raw -Encoding UTF8
$split = $stringsJs.IndexOf("`n  es: {")
if ($split -lt 0) { Fail "strings-common.js: no 'es:' block" }
$text = @{ en = $stringsJs.Substring(0, $split); es = $stringsJs.Substring($split) }

function Str($lang, $key) {
  $m = [regex]::Match($text[$lang], "\b$key\s*:\s*""((?:[^""\\]|\\.)*)""")
  if (-not $m.Success) { Fail "strings-common.js: no $lang string $key" }
  $s = [regex]::Unescape($m.Groups[1].Value)
  return $s.Replace("`r", " ").Replace("`n", " ")
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

$iss  = New-Object System.Text.StringBuilder
$code = New-Object System.Text.StringBuilder
$msgs = New-Object System.Text.StringBuilder
[void]$iss.AppendLine("; GENERATED by build.ps1 from learning\assets\modules.js - do not edit.")
[void]$iss.AppendLine("[Components]")
[void]$iss.AppendLine('Name: "fits"; Description: "{cm:CompFits}"; Types: full compact custom')
[void]$msgs.AppendLine("en.CompFits=" + (Str en "seriesName"))
[void]$msgs.AppendLine("es.CompFits=" + (Str es "seriesName"))

$fileLines = New-Object System.Text.StringBuilder
[void]$code.AppendLine("{ GENERATED by build.ps1 from learning\assets\modules.js - do not edit. }")
[void]$code.AppendLine("{ Paths (relative to learning/) left out by the reader's component choice, as JS string literals. }")
[void]$code.AppendLine("function OfflineMissing(): String;")
[void]$code.AppendLine("begin")
[void]$code.AppendLine("  Result := '';")

$n = 0
foreach ($m in $mods) {
  $n++
  if (-not $m.Ready) { continue }   # the hub shows it as "In progress" with no link
  $dir = Join-Path $fitsDir $m.Slug
  if (-not (Test-Path (Join-Path $dir "index.html"))) { Fail "module $($m.Slug) is ready but has no index.html" }
  $id = "fits\" + $m.Key.ToLower()
  $cm = "Comp" + $m.Key

  $parts = @{ page = @(); slides = @(); python = @() }
  Get-ChildItem $dir -File | ForEach-Object { $parts[(PartOf $_.Name)] += $_.Name }

  [void]$iss.AppendLine("Name: ""$id""; Description: ""{cm:$cm}""; Types: full compact custom; Flags: checkablealone")
  [void]$msgs.AppendLine("en.$cm=" + ((Str en "moduleN") -replace "\{n\}", $n) + ": " + (Str en "mod$($m.Key)Title"))
  [void]$msgs.AppendLine("es.$cm=" + ((Str es "moduleN") -replace "\{n\}", $n) + ": " + (Str es "mod$($m.Key)Title"))
  $src = "stage\learning\fits\$($m.Slug)"
  $dst = "{app}\learning\fits\$($m.Slug)"
  $partExcl = ($parts.slides + $parts.python) -join ","
  $excl = if ($partExcl) { "; Excludes: ""$partExcl""" } else { "" }
  [void]$fileLines.AppendLine("Source: ""$src\*""$excl; DestDir: ""$dst""; Components: $id; Flags: ignoreversion recursesubdirs")

  [void]$code.AppendLine("  if not WizardIsComponentSelected('$id') then")
  [void]$code.AppendLine("    Result := Result + ',""fits/$($m.Slug)/""'")
  [void]$code.AppendLine("  else begin")
  foreach ($p in @("slides", "python")) {
    if ($parts[$p].Count -eq 0) { continue }
    [void]$iss.AppendLine("Name: ""$id\$p""; Description: ""{cm:Part$p}""; Types: full")
    foreach ($f in $parts[$p]) {
      [void]$fileLines.AppendLine("Source: ""$src\$f""; DestDir: ""$dst""; Components: $id\$p; Flags: ignoreversion")
    }
    $list = ($parts[$p] | ForEach-Object { """fits/$($m.Slug)/$_""" }) -join ","
    [void]$code.AppendLine("    if not WizardIsComponentSelected('$id\$p') then")
    [void]$code.AppendLine("      Result := Result + ',$list';")
  }
  [void]$code.AppendLine("  end;")
}
[void]$code.AppendLine("  if Result <> '' then Delete(Result, 1, 1);")
[void]$code.AppendLine("end;")

[void]$iss.AppendLine("")
[void]$iss.AppendLine("[Files]")
[void]$iss.Append($fileLines.ToString())
[void]$iss.AppendLine("")
[void]$iss.AppendLine("[CustomMessages]")
[void]$iss.Append($msgs.ToString())

[System.IO.File]::WriteAllText((Join-Path $Stage "modules.iss"), $iss.ToString(), $Utf8Bom)
[System.IO.File]::WriteAllText((Join-Path $Stage "modules-code.iss"), $code.ToString(), $Utf8Bom)

$mb = "{0:N1}" -f ((Get-ChildItem $Stage -Recurse -File | Measure-Object Length -Sum).Sum / 1MB)
Write-Host "Staged $copied files from learning\ ($mb MB) in $Stage"
if ($StageOnly) { exit 0 }

# ---- 4. Compile --------------------------------------------------------------------------
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

Write-Host "Compiling with $iscc"
& $iscc /Q (Join-Path $Here "ReadingYourFits.iss")
if ($LASTEXITCODE -ne 0) { Fail "ISCC failed (exit $LASTEXITCODE)" }
$exe = Get-ChildItem (Join-Path $Here "dist") -Filter *.exe | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Write-Host ("Built {0} ({1:N1} MB)" -f $exe.FullName, ($exe.Length / 1MB)) -ForegroundColor Green
