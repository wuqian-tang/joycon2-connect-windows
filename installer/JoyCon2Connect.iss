#ifndef AppVersion
  #define AppVersion "1.1.0"
#endif
#ifndef SourceRoot
  #define SourceRoot SourcePath + ".."
#endif

[Setup]
AppId={{D90F2D89-8806-44A6-B55F-C243A378E15B}
AppName=Joy-Con 2 Connect
AppVersion={#AppVersion}
AppPublisher=Joy-Con 2 Connect contributors
AppPublisherURL=https://github.com/wuqian-tang/joycon2-connect-windows
AppSupportURL=https://github.com/wuqian-tang/joycon2-connect-windows/issues
DefaultDirName={localappdata}\Programs\JoyCon2Connect
DefaultGroupName=Joy-Con 2 Connect
DisableProgramGroupPage=yes
DisableDirPage=no
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
MinVersion=10.0.19041
OutputDir={#SourceRoot}\releases
OutputBaseFilename=JoyCon2Connect-{#AppVersion}-Setup
SetupIconFile={#SourceRoot}\assets\app.ico
UninstallDisplayIcon={app}\JoyCon2Assistant.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
LicenseFile={#SourceRoot}\LICENSE
CloseApplications=yes
RestartApplications=no
LanguageDetectionMethod=uilanguage

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "chinesesimplified"; MessagesFile: "languages\ChineseSimplified.isl"
Name: "chinesetraditional"; MessagesFile: "languages\ChineseTraditional.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; Flags: checkedonce

[Files]
Source: "{#SourceRoot}\dist\JoyCon2Assistant\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "runtime\*,*.log"

[Icons]
Name: "{group}\Joy-Con 2 Connect"; Filename: "{app}\JoyCon2Assistant.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\Joy-Con 2 Connect"; Filename: "{app}\JoyCon2Assistant.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\JoyCon2Assistant.exe"; Description: "{cm:LaunchProgram,Joy-Con 2 Connect}"; Flags: nowait postinstall skipifsilent
