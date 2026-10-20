[Setup]
; Nome e Versão do Sistema
AppName=SGE - Sistema de Gestão Empresarial
AppVersion=1.0.0
AppPublisher=Folestech,Lda
AppPublisherURL=https://Folestech,lda.co.mz
DefaultDirName={autopf}\Genesis
DefaultGroupName=SGE - Faturação
UninstallDisplayIcon={app}\Genesis.exe
Compression=lzma2
SolidCompression=yes
OutputDir=Output
OutputBaseFilename=Setup
SetupIconFile=icone.ico
PrivilegesRequired=admin

[Files]
; O Executável principal
Source: "dist\Genesis.exe"; DestDir: "{app}"; Flags: ignoreversion
; O Ficheiro de Configuração (.env)
Source: "dist\.env"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
; Cria a pasta "data" e dá permissões totais aos utilizadores
; (CRUCIAL: senão a base de dados não consegue gravar)
Name: "{app}\data"; Permissions: users-modify
Name: "{app}\data\uploads"; Permissions: users-modify
Name: "{app}\data\uploads\logotipos"; Permissions: users-modify

[Icons]
; Atalhos no Menu Iniciar e no Ambiente de Trabalho
Name: "{group}\SGE - Faturação"; Filename: "{app}\Genesis.exe"
Name: "{autodesktop}\SGE - Faturação"; Filename: "{app}\Genesis.exe"; IconFilename: "{app}\Genesis.exe"

[Run]
; Abre o sistema no fim da instalação
Filename: "{app}\Genesis.exe"; Description: "Abrir o SGE agora"; Flags: postinstall nowait skipifsilent