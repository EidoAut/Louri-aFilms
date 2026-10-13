#ifndef AppVersion
#define AppVersion "0.5.1"
#endif
#ifndef AppSource
#define AppSource "..\dist\lourihna_films"
#endif
[Setup]
AppId={{ED568AE0-7951-4FFB-84D7-1B84E4E09621}
AppName=Louriña Films
AppVersion={#AppVersion}
AppPublisher=EIDO Automation
AppPublisherURL=https://github.com/EidoAut/Louri-aFilms
DefaultDirName={localappdata}\Programs\LourihnaFilms
DefaultGroupName=Louriña Films
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.17763
OutputDir=..\dist\packages
OutputBaseFilename=lourihna-films-{#AppVersion}-windows-x86_64-setup
SetupIconFile=..\lourihna_films\assets\lourihna_films.ico
LicenseFile=..\LICENSE
Compression=lzma2
SolidCompression=yes
UninstallDisplayIcon={app}\lourihna_films.exe
[Files]
Source: "{#AppSource}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\Louriña Films"; Filename: "{app}\lourihna_films.exe"
Name: "{autodesktop}\Louriña Films"; Filename: "{app}\lourihna_films.exe"
[Run]
Filename: "{app}\lourihna_films.exe"; Description: "Abrir Louriña Films"; Flags: nowait postinstall skipifsilent
