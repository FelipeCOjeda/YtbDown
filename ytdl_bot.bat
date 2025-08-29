@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Setup ytdl_bot + FFmpeg (Windows)

REM ---- Caminhos/alvos
set "FFMPEG_DIR=C:\ffmpeg"
set "FFMPEG_BIN=%FFMPEG_DIR%\bin"
set "TMP_ZIP=%TEMP%\ffmpeg-release-essentials.zip"
set "FFMPEG_URL=https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"

echo ==========================================================
echo [1/5] Instalando/atualizando pip e yt-dlp...
echo ==========================================================
where python >nul 2>&1
if errorlevel 1 (
  echo [ERRO] Python nao encontrado no PATH. Instale o Python 3.x e tente de novo.
  pause
  exit /b 1
)

python -m pip install --upgrade pip
if errorlevel 1 (
  echo [AVISO] Nao consegui atualizar o pip. Vou prosseguir mesmo assim.
)

python -m pip install --upgrade yt-dlp
if errorlevel 1 (
  echo [ERRO] Falha ao instalar/atualizar yt-dlp.
  pause
  exit /b 1
)

echo.
echo ==========================================================
echo [2/5] Baixando FFmpeg (release essentials)...
echo ==========================================================
if exist "%FFMPEG_BIN%\ffmpeg.exe" (
  echo FFmpeg ja encontrado em "%FFMPEG_BIN%". Pulando download.
) else (
  echo Baixando para "%TMP_ZIP%" ...
  powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "Try { Invoke-WebRequest -Uri '%FFMPEG_URL%' -OutFile '%TMP_ZIP%' -UseBasicParsing } Catch { exit 1 }"
  if errorlevel 1 (
    echo [ERRO] Falha ao baixar o FFmpeg.
    pause
    exit /b 1
  )

  echo.
  echo ========================================================
  echo [3/5] Extraindo para "%FFMPEG_DIR%"...
  echo ========================================================
  REM Apaga destino se existir (para manter padrao limpo)
  if exist "%FFMPEG_DIR%" (
    rmdir /s /q "%FFMPEG_DIR%" 2>nul
  )
  mkdir "%FFMPEG_DIR%" >nul 2>&1

  powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "Expand-Archive -Path '%TMP_ZIP%' -DestinationPath '%FFMPEG_DIR%' -Force"

  if not exist "%FFMPEG_DIR%" (
    echo [ERRO] Falha ao extrair o FFmpeg.
    pause
    exit /b 1
  )

  REM A pasta zipada vem com um subdiretorio (ffmpeg-*-essentials_build).
  REM Move o conteudo dele para %FFMPEG_DIR% e remove o subdir.
  powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$dest='%FFMPEG_DIR%'; $sub = Get-ChildItem $dest | Where-Object { $_.PSIsContainer } | Select-Object -First 1; " ^
    "if ($sub) { Move-Item -Path (Join-Path $sub.FullName '*') -Destination $dest -Force; Remove-Item $sub.FullName -Recurse -Force }"

  if not exist "%FFMPEG_BIN%\ffmpeg.exe" (
    echo [ERRO] Nao encontrei ffmpeg.exe em "%FFMPEG_BIN%".
    echo Verifique o conteudo extraido em "%FFMPEG_DIR%".
    pause
    exit /b 1
  )
)

echo.
echo ==========================================================
echo [4/5] Adicionando "%FFMPEG_BIN%" ao PATH (usuario)...
echo ==========================================================
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$u=[Environment]::GetEnvironmentVariable('Path','User'); " ^
  "if($u -notlike '*%FFMPEG_BIN%*'){ [Environment]::SetEnvironmentVariable('Path',$u+';%FFMPEG_BIN%','Use_*_*
