#define MyAppName "Registro de Equipamentos"
#define MyAppExeName "RegistroEquipamentos.exe"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Lar Cristão Evangélico"

[Setup]
AppId={{8D2F7C12-2B6E-4A7C-9F6B-7A0B1F2E4C01}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

; Instala por usuário (sem UAC) — ideal para “duplo clique e vai”
DefaultDirName={localappdata}\{#MyAppName}
PrivilegesRequired=lowest

DisableDirPage=yes
DisableProgramGroupPage=yes
DisableReadyPage=yes
DisableWelcomePage=yes
DisableFinishedPage=yes
WizardStyle=modern

OutputDir=..\installer_output
OutputBaseFilename=RegistroEquipamentos_Setup_{#MyAppVersion}
Compression=lzma
SolidCompression=yes

SetupIconFile=..\assets\logo.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "portuguese"; MessagesFile: "compiler:Languages\Portuguese.isl"

[Files]
; Copia o build do PyInstaller (modo pasta) para o diretório do app
Source: "..\dist\RegistroEquipamentos\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Atalho no Menu Iniciar
Name: "{userprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\assets\logo.ico"

; Atalho SEMPRE na Área de Trabalho (sem “task opcional”)
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\assets\logo.ico"

[Run]
Filename: "{app}\{#MyAppExeName}"; Flags: nowait postinstall skipifsilent
