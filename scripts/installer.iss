; TCG Tools — Inno Setup installer script
; Build: iscc /DAppVersion=1.2.0 /DStagingDir=...\dist\staging /DOutputDir=...\dist scripts\installer.iss

#ifndef AppVersion
#define AppVersion "1.2.0"
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
SetupIconFile=..\launcher\internal\app\assets\icon.ico
UninstallDisplayIcon={app}\TCGTools.exe

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Area de Trabalho"; GroupDescription: "Atalhos:"; Flags: unchecked

[Files]
Source: "{#StagingDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Check: not PasswordOnlyMode
Source: "set-admin-password.ps1"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\TCG Tools"; Filename: "{app}\TCGTools.exe"; IconFilename: "{app}\TCGTools.exe"; Check: not PasswordOnlyMode
Name: "{autodesktop}\TCG Tools"; Filename: "{app}\TCGTools.exe"; IconFilename: "{app}\TCGTools.exe"; Tasks: desktopicon; Check: not PasswordOnlyMode

[Code]
var
  PortPage: TInputQueryWizardPage;
  AuthPage: TInputQueryWizardPage;
  StartWithWindowsCheck: TNewCheckBox;
  LanAccessCheck: TNewCheckBox;
  SetPasswordCheck: TNewCheckBox;
  PasswordOnlyCheck: TNewCheckBox;
  UninstallDeleteDataCheck: TNewCheckBox;
  IsPasswordOnly: Boolean;

{ Check: clauses require a function named PasswordOnlyMode (not a bare Boolean var). }
function PasswordOnlyMode: Boolean;
begin
  Result := IsPasswordOnly;
end;

function ValidatePort(PortStr: String): Boolean;
var
  P: Integer;
begin
  P := StrToIntDef(PortStr, -1);
  Result := (P >= 1024) and (P <= 65535);
end;

function AdminDbExists: Boolean;
begin
  Result := FileExists(ExpandConstant('{userappdata}\TCGTools\tcg_tools.db'));
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
  IsPasswordOnly := False;

  PortPage := CreateInputQueryPage(wpSelectDir,
    'Configuracao do servidor', 'Porta e rede local',
    'Informe a porta HTTP e se outros dispositivos na Wi-Fi podem acessar o TCG Tools.');
  PortPage.Add('Porta:', False);
  PortPage.Values[0] := '8000';

  StartWithWindowsCheck := TNewCheckBox.Create(PortPage);
  StartWithWindowsCheck.Parent := PortPage.Surface;
  StartWithWindowsCheck.Caption := 'Iniciar com Windows';
  StartWithWindowsCheck.Top := PortPage.Edits[0].Top + PortPage.Edits[0].Height + 12;
  StartWithWindowsCheck.Left := PortPage.Edits[0].Left;
  StartWithWindowsCheck.Width := PortPage.SurfaceWidth;

  LanAccessCheck := TNewCheckBox.Create(PortPage);
  LanAccessCheck.Parent := PortPage.Surface;
  LanAccessCheck.Caption := 'Permitir acesso na rede local (LAN)';
  LanAccessCheck.Top := StartWithWindowsCheck.Top + StartWithWindowsCheck.Height + 8;
  LanAccessCheck.Left := PortPage.Edits[0].Left;
  LanAccessCheck.Width := PortPage.SurfaceWidth;
  LanAccessCheck.Checked := False;

  PasswordOnlyCheck := TNewCheckBox.Create(PortPage);
  PasswordOnlyCheck.Parent := PortPage.Surface;
  PasswordOnlyCheck.Caption := 'Apenas alterar senha do admin (nao atualizar arquivos)';
  PasswordOnlyCheck.Top := LanAccessCheck.Top + LanAccessCheck.Height + 8;
  PasswordOnlyCheck.Left := PortPage.Edits[0].Left;
  PasswordOnlyCheck.Width := PortPage.SurfaceWidth;
  PasswordOnlyCheck.Checked := False;

  AuthPage := CreateInputQueryPage(PortPage.ID,
    'Senha do admin', 'Usuario fixo: admin',
    'Minimo 6 caracteres. Em upgrade, desmarque "Definir/alterar senha" para manter a atual.');
  AuthPage.Add('Senha:', True);
  AuthPage.Add('Confirmar senha:', True);

  SetPasswordCheck := TNewCheckBox.Create(AuthPage);
  SetPasswordCheck.Parent := AuthPage.Surface;
  SetPasswordCheck.Caption := 'Definir / alterar senha do admin';
  SetPasswordCheck.Top := AuthPage.Edits[1].Top + AuthPage.Edits[1].Height + 12;
  SetPasswordCheck.Left := AuthPage.Edits[0].Left;
  SetPasswordCheck.Width := AuthPage.SurfaceWidth;
  SetPasswordCheck.Checked := not AdminDbExists;
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := False;
  if IsPasswordOnly then
  begin
    if (PageID = wpSelectDir) or (PageID = wpSelectProgramGroup) or (PageID = wpSelectTasks) then
      Result := True;
  end;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = PortPage.ID then
  begin
    IsPasswordOnly := PasswordOnlyCheck.Checked;
    if not ValidatePort(PortPage.Values[0]) then
    begin
      MsgBox('Porta invalida. Use um valor entre 1024 e 65535.', mbError, MB_OK);
      Result := False;
      Exit;
    end;
    if IsPasswordOnly then
    begin
      if not FileExists(ExpandConstant('{app}\runtime\python\python.exe')) then
      begin
        MsgBox('Modo apenas senha exige TCG Tools ja instalado neste computador.', mbError, MB_OK);
        Result := False;
        Exit;
      end;
      SetPasswordCheck.Checked := True;
      SetPasswordCheck.Enabled := False;
    end
    else
      SetPasswordCheck.Enabled := True;
  end;
  if CurPageID = AuthPage.ID then
  begin
    if SetPasswordCheck.Checked then
    begin
      if Length(AuthPage.Values[0]) < 6 then
      begin
        MsgBox('Senha deve ter pelo menos 6 caracteres.', mbError, MB_OK);
        Result := False;
        Exit;
      end;
      if AuthPage.Values[0] <> AuthPage.Values[1] then
      begin
        MsgBox('Confirmacao de senha nao confere.', mbError, MB_OK);
        Result := False;
        Exit;
      end;
    end
    else if not AdminDbExists then
    begin
      MsgBox('Instalacao nova exige definir a senha do admin.', mbError, MB_OK);
      Result := False;
    end;
  end;
end;

procedure MergeLauncherConfig;
var
  ConfigPath, AppDataDir, Json: String;
  PortVal: Integer;
  LanVal, AutoVal: String;
begin
  AppDataDir := ExpandConstant('{userappdata}\TCGTools');
  ConfigPath := AppDataDir + '\launcher_config.json';
  ForceDirectories(AppDataDir);
  PortVal := StrToInt(PortPage.Values[0]);
  if LanAccessCheck.Checked then LanVal := 'true' else LanVal := 'false';
  if StartWithWindowsCheck.Checked then AutoVal := 'true' else AutoVal := 'false';
  Json := Format('{' + #13#10 +
    '  "port": %d,' + #13#10 +
    '  "start_with_windows": %s,' + #13#10 +
    '  "lan_access": %s' + #13#10 +
    '}', [PortVal, AutoVal, LanVal]);
  SaveStringToFile(ConfigPath, Json, False);
end;

procedure ApplyFirewallRule;
var
  PortVal: String;
  ResultCode: Integer;
begin
  PortVal := PortPage.Values[0];
  Exec('netsh', 'advfirewall firewall delete rule name="TCG Tools"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  if LanAccessCheck.Checked then
    Exec('netsh',
      'advfirewall firewall add rule name="TCG Tools" dir=in action=allow protocol=TCP localport=' + PortVal,
      '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

procedure ApplyAdminPassword;
var
  ResultCode: Integer;
  ScriptPath, Args, PwFile: String;
begin
  if not SetPasswordCheck.Checked then
    Exit;
  ScriptPath := ExpandConstant('{app}\set-admin-password.ps1');
  if not FileExists(ScriptPath) then
  begin
    MsgBox('Script set-admin-password.ps1 nao encontrado. Instale/atualize os arquivos do app primeiro.', mbError, MB_OK);
    Exit;
  end;
  if not FileExists(ExpandConstant('{app}\runtime\python\python.exe')) then
  begin
    MsgBox('Instalacao do TCG Tools incompleta (python ausente).', mbError, MB_OK);
    Exit;
  end;
  PwFile := ExpandConstant('{tmp}\tcgtools_admin_pw.txt');
  SaveStringToFile(PwFile, AuthPage.Values[0], False);
  Args := '-NoProfile -ExecutionPolicy Bypass -File "' + ScriptPath +
    '" -InstallDir "' + ExpandConstant('{app}') +
    '" -PasswordFile "' + PwFile + '"';
  if not Exec('powershell.exe', Args, '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
    MsgBox('Falha ao executar definicao de senha.', mbError, MB_OK)
  else if ResultCode <> 0 then
    MsgBox('Falha ao gravar senha do admin (codigo ' + IntToStr(ResultCode) + ').', mbError, MB_OK);
  DeleteFile(PwFile);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then
    StopTCGToolsProcesses;
  if CurStep = ssPostInstall then
  begin
    if not IsPasswordOnly then
      MergeLauncherConfig;
    ApplyFirewallRule;
    ApplyAdminPassword;
  end;
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
  ResultCode: Integer;
begin
  if CurUninstallStep = usUninstall then
  begin
    StopTCGToolsProcesses;
    Exec('netsh', 'advfirewall firewall delete rule name="TCG Tools"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  end;

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
Filename: "{app}\TCGTools.exe"; Description: "Iniciar TCG Tools"; Flags: nowait postinstall skipifsilent; Check: not PasswordOnlyMode
