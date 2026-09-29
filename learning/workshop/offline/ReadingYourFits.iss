; ReadingYourFits.iss - offline Windows installer for gideonong.me/learning (Phase D).
; Build with build.ps1 (it stages learning\ and generates stage\modules*.iss first); compiling
; this file on its own fails with a pointer to build.ps1. Saved as UTF-8 with BOM (Spanish text).
;
; Components: the hub and shared files (always), then per series a group of modules, each with
; optional parts (slides, Python). The module list comes from learning\assets\modules.js via
; build.ps1, so a new module needs no edit here. What the reader leaves out is written into the
; installed modules.js as window.LEARN_OFFLINE, and learning.js marks those modules
; "Not installed" and hides links to left-out files. A future series: add its component group
; and files the same way (build.ps1 section 3).

; ---- The one place the version lives ------------------------------------------------------
#define AppVersion "1.0.0"
; -------------------------------------------------------------------------------------------
#define AppName "Reading Your Fits"

#if !FileExists(AddBackslash(SourcePath) + "stage\modules.iss")
  #error stage\modules.iss is missing: run build.ps1, not ISCC on this file directly
#endif

[Setup]
; AppId identifies the install for upgrades and the uninstaller. Never change it.
AppId={{02F24A47-1234-4F1D-A418-ECF2285446C6}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Gideon A. Ong
AppPublisherURL=https://gideonong.me/learning/
VersionInfoVersion={#AppVersion}
; Per-user install: no admin prompt, nothing outside the user's profile.
PrivilegesRequired=lowest
DefaultDirName={localappdata}\Programs\{#AppName}
DisableProgramGroupPage=yes
AlwaysShowComponentsList=yes
ShowLanguageDialog=yes
UninstallDisplayName={#AppName}
UninstallDisplayIcon={app}\assets\glogo.ico
SetupIconFile=stage\assets\glogo.ico
WizardStyle=modern
Compression=lzma2/max
SolidCompression=yes
OutputDir=dist
OutputBaseFilename=ReadingYourFits-Setup-{#AppVersion}

[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"

[Types]
Name: "full"; Description: "{cm:TypeFull}"
Name: "compact"; Description: "{cm:TypeCompact}"
Name: "custom"; Description: "{cm:TypeCustom}"; Flags: iscustom

[Components]
Name: "hub"; Description: "{cm:CompHub}"; Types: full compact custom; Flags: fixed

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[InstallDelete]
; Start clean on every install, repair or upgrade, so deselected modules and files dropped from
; a newer version don't linger. The folder only ever holds what this installer put there.
Type: filesandordirs; Name: "{app}\learning"

[Files]
; Hub + shared assets (everything but the module folders), and the favicon the pages link at
; ..\assets\glogo.ico. Module folders come from stage\modules.iss.
Source: "stage\learning\*"; Excludes: "\fits\*";DestDir: "{app}\learning"; Components: hub; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "stage\assets\glogo.ico"; DestDir: "{app}\assets"; Components: hub; Flags: ignoreversion

#include "stage\modules.iss"

[Icons]
; A shortcut to an .html file opens it in the default browser.
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\learning\index.html"; IconFilename: "{app}\assets\glogo.ico"; Comment: "{cm:ShortcutComment}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\learning\index.html"; IconFilename: "{app}\assets\glogo.ico"; Comment: "{cm:ShortcutComment}"; Tasks: desktopicon

[Run]
Filename: "{app}\learning\index.html"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: postinstall shellexec nowait skipifsilent

[UninstallDelete]
Type: dirifempty; Name: "{app}"

[CustomMessages]
en.TypeFull=Everything: pages, slides and Python scripts
es.TypeFull=Todo: páginas, diapositivas y scripts de Python
en.TypeCompact=Interactive pages only (smallest)
es.TypeCompact=Solo las páginas interactivas (lo más ligero)
en.TypeCustom=Choose modules and parts
es.TypeCustom=Elegir módulos y partes
en.CompHub=Learning home page and shared files
es.CompHub=Página de inicio de Aprendizaje y archivos comunes
en.Partslides=Slides (English and Spanish)
es.Partslides=Diapositivas (inglés y español)
en.Partpython=Python script and Jupyter notebook
es.Partpython=Script de Python y cuaderno de Jupyter
en.ShortcutComment=Interactive modules on checking a line fit against lab data
es.ShortcutComment=Módulos interactivos para revisar un ajuste de curvas con datos de laboratorio

[Code]
#include "stage\modules-code.iss"

// Tell the pages what was left out: append window.LEARN_OFFLINE to the installed modules.js
// (a fresh copy on every install, since [InstallDelete] clears the folder first).
procedure CurStepChanged(CurStep: TSetupStep);
var
  F, S: String;
begin
  if CurStep = ssPostInstall then
  begin
    F := ExpandConstant('{app}\learning\assets\modules.js');
    S := #13#10 + '// Added by the offline installer (learning/workshop/offline/): paths this copy leaves out.' + #13#10 +
         'window.LEARN_OFFLINE = { version: "{#AppVersion}", missing: [' + OfflineMissing() + '] };' + #13#10;
    if not SaveStringToFile(F, S, True) then
      Log('Could not append the offline manifest to ' + F);
  end;
end;
