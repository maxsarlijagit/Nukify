#ifndef AppVersion
  #define AppVersion "0.9.2"
#endif
[Setup]
AppId={{FE32A4AE-6325-4CB3-9ED7-8EF24C191F24}
AppName=Nukify
AppVersion={#AppVersion}
AppPublisher=Max Sarlija
AppPublisherURL=https://github.com/maxsarlijagit
AppSupportURL=https://github.com/maxsarlijagit/Nukify/issues
AppUpdatesURL=https://github.com/maxsarlijagit/Nukify/releases
DefaultDirName={localappdata}\Programs\Nukify
DefaultGroupName=Nukify
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\releases\{#AppVersion}
OutputBaseFilename=Nukify-Setup-{#AppVersion}
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\Nukify.exe
LicenseFile=..\LICENSE
CloseApplications=no
RestartApplications=no

[Files]
Source: "..\releases\{#AppVersion}\Nukify\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Tasks]
Name: desktopicon; Description: "Crear acceso directo en el escritorio"; Flags: unchecked

[Icons]
Name: "{group}\Nukify"; Filename: "{app}\Nukify.exe"
Name: "{autodesktop}\Nukify"; Filename: "{app}\Nukify.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Nukify.exe"; Description: "Abrir Nukify"; Flags: nowait postinstall skipifsilent
