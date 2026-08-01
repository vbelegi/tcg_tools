; TCG Tools — Inno Setup installer script
; Build: iscc /DAppVersion=1.1.0 /DStagingDir=...\dist\staging /DOutputDir=...\dist scripts\installer.iss

#ifndef AppVersion
#define AppVersion "1.1.0"
#endif
#ifndef StagingDir
#define StagingDir "..\dist\staging"
#endif
#ifndef OutputDir
#define OutputDir "..\dist"
#endif

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName=TCG Tools
AppVersion={#AppVersion}
AppPublisher=TCG Tools
DefaultDirName={autopf}\TCG Tools
DefaultGroupName=TCG Tools
OutputDir={#OutputDir}
OutputBaseFilename=TCGTools-{#AppVersion}-setup
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=admin
UsePreviousAppDir=yes
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Area de Trabalho"; GroupDescription: "Atalhos:"; Flags: unchecked

[Files]
Source: "{#StagingDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\TCG Tools"; Filename: "{app}\TCGTools.exe"
Name: "{autodesktop}\TCG Tools"; Filename: "{app}\TCGTools.exe"; Tasks: desktopicon

[Code]
var
  PortPage: TInputQueryWizardPage;
  StartWithWindowsCheck: TNewCheckBox;

function ValidatePort(PortStr: String): Boolean;
var
  P: Integer;
begin
  Result := TryStrToInt(PortStr, P) and (P >= 1024) and (P <= 65535);
end;

procedure InitializeWizard;
begin
  PortPage := CreateInputQueryPage(wpSelectDir,
    'Configuracao do servidor', 'Porta HTTP local',
    'Informe a porta usada pelo TCG Tools (padrao 8000).');
  PortPage.Add('Porta:', False);
  PortPage.Values[0] := '8000';

  StartWithWindowsCheck := TNewCheckBox.Create(PortPage);
  StartWithWindowsCheck.Parent := PortPage.Surface;
  StartWithWindowsCheck.Caption := 'Iniciar com Windows';
  StartWithWindowsCheck.Top := PortPage.Edits[0].Top + PortPage.Edits[0].Height + 12;
  StartWithWindowsCheck.Left := PortPage.Edits[0].Left;
  StartWithWindowsCheck.Width := PortPage.SurfaceWidth;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = PortPage.ID then
  begin
    if not ValidatePort(PortPage.Values[0]) then
    begin
      MsgBox('Porta invalida. Use um valor entre 1024 e 65535.', mbError, MB_OK);
      Result := False;
    end;
  end;
end;

procedure WriteLauncherConfig;
var
  ConfigPath, AppDataDir, Json: String;
  PortVal: Integer;
begin
  AppDataDir := ExpandConstant('{userappdata}\TCGTools');
  ConfigPath := AppDataDir + '\launcher_config.json';
  if FileExists(ConfigPath) then
    Exit;
  ForceDirectories(AppDataDir);
  PortVal := StrToInt(PortPage.Values[0]);
  if StartWithWindowsCheck.Checked then
    Json := Format('{' + #13#10 +
      '  "port": %d,' + #13#10 +
      '  "start_with_windows": true' + #13#10 +
      '}', [PortVal])
  else
    Json := Format('{' + #13#10 +
      '  "port": %d,' + #13#10 +
      '  "start_with_windows": false' + #13#10 +
      '}', [PortVal]);
  SaveStringToFile(ConfigPath, Json, False);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    WriteLauncherConfig;
end;

function InitializeUninstall(): Boolean;
begin
  Result := MsgBox(
    'Desinstalar o TCG Tools remove tambem todos os dados em %APPDATA%\TCGTools (torneios, exports, logs).' + #13#10 +
    'Faca backup do arquivo tcg_tools.db antes de continuar.' + #13#10#13#10 +
    'Deseja continuar?',
    mbConfirmation, MB_YESNO) = IDYES;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  AppDataDir: String;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    AppDataDir := ExpandConstant('{userappdata}\TCGTools');
    if DirExists(AppDataDir) then
      DelTree(AppDataDir, True, True, True);
    RegDeleteValue(HKEY_CURRENT_USER, 'Software\Microsoft\Windows\CurrentVersion\Run', 'TCGTools');
  end;
end;

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\TCGTools"

[Run]
Filename: "{app}\TCGTools.exe"; Description: "Iniciar TCG Tools"; Flags: nowait postinstall skipifsilent
