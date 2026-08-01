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
AppMutex=Local\TCGTools_SingleInstance
CloseApplications=force
RestartApplications=no

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
  UninstallDeleteDataCheck: TNewCheckBox;

function ValidatePort(PortStr: String): Boolean;
var
  P: Integer;
begin
  P := StrToIntDef(PortStr, -1);
  Result := (P >= 1024) and (P <= 65535);
end;

procedure StopTCGToolsProcesses;
var
  ResultCode: Integer;
  ScriptPath: String;
begin
  ScriptPath := ExpandConstant('{app}\stop-tcg-processes.ps1');
  if FileExists(ScriptPath) then
    Exec('powershell.exe', '-NoProfile -ExecutionPolicy Bypass -File "' + ScriptPath + '"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode)
  else
  begin
    Exec('taskkill', '/IM TCGTools.exe /F', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    Sleep(1000);
  end;
end;

procedure InitializeWizard;
begin
  PortPage := CreateInputQueryPage(wpSelectDir,
    'Configuracao do servidor', 'Porta HTTP local',
    'Informe a porta usada pelo TCG Tools (padrao 8000). Em upgrades, estes valores atualizam launcher_config.json.');
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

procedure MergeLauncherConfig;
var
  ConfigPath, AppDataDir, Json: String;
  PortVal: Integer;
begin
  AppDataDir := ExpandConstant('{userappdata}\TCGTools');
  ConfigPath := AppDataDir + '\launcher_config.json';
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
  if CurStep = ssInstall then
    StopTCGToolsProcesses;
  if CurStep = ssPostInstall then
    MergeLauncherConfig;
end;

procedure InitializeUninstallProgressForm;
begin
  UninstallDeleteDataCheck := TNewCheckBox.Create(UninstallProgressForm);
  UninstallDeleteDataCheck.Parent := UninstallProgressForm;
  UninstallDeleteDataCheck.Caption := 'Remover dados locais (%APPDATA%\TCGTools: banco, exports, logs, presets)';
  UninstallDeleteDataCheck.Checked := False;
  UninstallDeleteDataCheck.Top := UninstallProgressForm.StatusLabel.Top + UninstallProgressForm.StatusLabel.Height + 16;
  UninstallDeleteDataCheck.Left := UninstallProgressForm.StatusLabel.Left;
  UninstallDeleteDataCheck.Width := UninstallProgressForm.ClientWidth - 32;
end;

function InitializeUninstall(): Boolean;
begin
  if CheckForMutexes('Local\TCGTools_SingleInstance') then
  begin
    if MsgBox(
      'O TCG Tools parece estar em execucao nesta sessao de usuario.' + #13#10 +
      'Deseja encerrar o aplicativo antes de desinstalar?',
      mbConfirmation, MB_YESNO) = IDYES then
    begin
      StopTCGToolsProcesses;
    end
    else
    begin
      Result := False;
      Exit;
    end;
  end
  else
    StopTCGToolsProcesses;

  Result := MsgBox(
    'Desinstalar o TCG Tools remove os arquivos do programa em Program Files.' + #13#10 +
    'Na proxima tela voce pode optar por manter ou remover os dados em %APPDATA%\TCGTools.' + #13#10#13#10 +
    'Deseja continuar?',
    mbConfirmation, MB_YESNO) = IDYES;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  AppDataDir: String;
begin
  if CurUninstallStep = usUninstall then
    StopTCGToolsProcesses;

  if CurUninstallStep = usPostUninstall then
  begin
    RegDeleteValue(HKEY_CURRENT_USER, 'Software\Microsoft\Windows\CurrentVersion\Run', 'TCGTools');
    if UninstallDeleteDataCheck.Checked then
    begin
      AppDataDir := ExpandConstant('{userappdata}\TCGTools');
      if DirExists(AppDataDir) then
        DelTree(AppDataDir, True, True, True);
    end;
  end;
end;

[Run]
Filename: "{app}\TCGTools.exe"; Description: "Iniciar TCG Tools"; Flags: nowait postinstall skipifsilent
