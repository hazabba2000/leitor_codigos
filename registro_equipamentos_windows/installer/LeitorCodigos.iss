#define MyAppName "LeitorCodigos"
#define MyAppExeName "LeitorCodigos.exe"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Stone Franquias"

[Setup]
; Gere um novo AppId se quiser (recomendado quando muda de app)
AppId={{8D2F7C12-2B6E-4A7C-9F6B-7A0B1F2E4C01}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

; Instala por usuário (sem UAC)
DefaultDirName={localappdata}\{#MyAppName}
PrivilegesRequired=lowest

DisableDirPage=yes
DisableProgramGroupPage=yes
DisableReadyPage=yes
DisableWelcomePage=yes
DisableFinishedPage=yes
WizardStyle=modern

; <<< ESTE ARQUIVO .iss está em: registro_equipamentos_windows\installer\
; então precisa voltar 2 pastas até a raiz do repo
OutputDir=..\..\dist_installer
OutputBaseFilename=LeitorCodigos_Setup_{#MyAppVersion}
Compression=lzma
SolidCompression=yes

; Ícone do instalador (opcional) — ajuste se você criar logo.ico
; SetupIconFile=..\..\assets\logo.ico
; UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Files]
; Copia o build do PyInstaller (modo pasta) para o diretório do app
Source: "..\..\dist\LeitorCodigos\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Atalho no Menu Iniciar
Name: "{userprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"

; Atalho SEMPRE na Área de Trabalho
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Flags: nowait postinstall skipifsilent

