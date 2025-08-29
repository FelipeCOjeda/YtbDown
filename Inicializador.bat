@echo off
title YouTube Downloader Bot
cd /d "%~dp0"

:: Solicita o link do YouTube ao usuário
set /p url=Insira o link do YouTube nessa porra: 

:: Executa o script Python com o link informado
python ytdl_bot.py %url%

pause
