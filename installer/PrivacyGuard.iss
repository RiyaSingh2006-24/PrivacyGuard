#define MyAppName "PrivacyGuard"
#define MyAppVersion "2.1.0"
#define MyAppPublisher "Riya Singh"
#define MyAppExeName "PrivacyGuard.exe"

[Setup]
AppId={{B46A5EA2-77F7-4E4A-BE81-8D042D294EA2}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\PrivacyGuard
DefaultGroupName=PrivacyGuard
DisableProgramGroupPage=yes
OutputDir=..\release
OutputBaseFilename=PrivacyGuard-Setup-2.1.0
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayName=PrivacyGuard

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "..\backend\dist\PrivacyGuard\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\PrivacyGuard"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\PrivacyGuard"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch PrivacyGuard"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
