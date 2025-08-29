#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import shutil
import sys
from pathlib import Path
from yt_dlp import YoutubeDL

"""
Bot de download do YouTube (máxima resolução) com FFmpeg
- Suporta link único e playlists (cole várias URLs)
- Junta vídeo + áudio via FFmpeg em MP4 quando possível (fallback para MKV se necessário)
- Detecta FFmpeg automaticamente no PATH ou via --ffmpeg
USO:
  python ytdl_bot.py URL [URL2 ...]
  python ytdl_bot.py --file urls.txt
  python ytdl_bot.py --out downloads URL
  python ytdl_bot.py --cookies cookies.txt URL
  python ytdl_bot.py --ffmpeg "C:\\ffmpeg\\bin" URL
"""

# -------------------------------
# Utilidades
# -------------------------------

def find_ffmpeg(custom_dir: str | None) -> str | None:
    """
    Retorna um caminho utilizável para o FFmpeg.
    - Se custom_dir for passado, valida se existe ffmpeg(.exe) lá.
    - Caso contrário, tenta encontrar no PATH do sistema via shutil.which.
    - Em Windows, também tenta variações comuns.
    Retorna o caminho da pasta que contém o executável, ou None se não encontrar.
    """
    def has_ffmpeg(dirpath: str) -> bool:
        exe = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
        return os.path.isfile(os.path.join(dirpath, exe))

    # 1) Diretório informado pelo usuário
    if custom_dir:
        if os.path.isdir(custom_dir) and has_ffmpeg(custom_dir):
            return custom_dir
        return None

    # 2) PATH do sistema
    which = shutil.which("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
    if which:
        return str(Path(which).parent)

    # 3) Tentativas comuns no Windows
    if os.name == "nt":
        guesses = [
            r"C:\ffmpeg\bin",
            r"C:\Program Files\ffmpeg\bin",
            r"C:\Program Files (x86)\ffmpeg\bin",
        ]
        for g in guesses:
            if os.path.isdir(g) and has_ffmpeg(g):
                return g

    return None


def load_urls_from_file(txt_path: str) -> list[str]:
    urls: list[str] = []
    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:
            u = line.strip()
            if u:
                urls.append(u)
    return urls


# -------------------------------
# CLI
# -------------------------------

def build_args():
    p = argparse.ArgumentParser(description="YouTube Max Quality Downloader (com FFmpeg)")
    p.add_argument("urls", nargs="*", help="URLs do YouTube (vídeos ou playlists)")
    p.add_argument("--file", help="Arquivo .txt com URLs (uma por linha)")
    p.add_argument("--out", default="downloads", help="Pasta de saída (default: downloads)")
    p.add_argument("--cookies", help="cookies.txt para vídeos com restrição")
    p.add_argument("--ffmpeg", help="caminho da pasta que contém ffmpeg(.exe), ex.: C:\\ffmpeg\\bin")
    p.add_argument("--audio-only", action="store_true",
                   help="Baixar apenas o áudio em M4A (sem vídeo)")
    return p.parse_args()


# -------------------------------
# Principal
# -------------------------------

def main():
    args = build_args()

    # URLs (linha de comando + arquivo)
    urls = list(args.urls)
    if args.file:
        if not os.path.isfile(args.file):
            print(f"[!] Arquivo com URLs não encontrado: {args.file}")
            sys.exit(1)
        urls.extend(load_urls_from_file(args.file))

    if not urls:
        print("Nenhuma URL fornecida.\nEx.: python ytdl_bot.py <URL> [URL2 ...]  |  --file urls.txt")
        sys.exit(1)

    # Saída
    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)

    # Detectar FFmpeg
    ffmpeg_dir = find_ffmpeg(args.ffmpeg)
    if not ffmpeg_dir:
        print(
            "[!] FFmpeg não encontrado.\n"
            "    Instale e/ou adicione o 'bin' do FFmpeg ao PATH, ou passe --ffmpeg \"C:\\\\ffmpeg\\\\bin\".\n"
            "    Download recomendado (Windows): https://www.gyan.dev/ffmpeg/builds/"
        )
        sys.exit(1)

    # Opções do yt_dlp
    if args.audio_only:
        # Áudio apenas (M4A/AAC quando disponível)
        ydl_opts = {
            "outtmpl": str(outdir / "%(title).200B [%(id)s].%(ext)s"),
            "format": "bestaudio[ext=m4a]/bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "m4a",
                    "preferredquality": "0",
                }
            ],
            "ffmpeg_location": ffmpeg_dir,
            "retries": 10,
            "fragment_retries": 10,
            "http_chunk_size": 10 * 1024 * 1024,  # 10 MiB
            "noplaylist": False,
            "ignoreerrors": "only_download",
            "quiet": False,
            "no_warnings": False,
        }
    else:
        # Vídeo + áudio (merge em MP4 quando possível)
        ydl_opts = {
            "outtmpl": str(outdir / "%(title).200B [%(id)s] [%(resolution)s] [%(fps)sfps].%(ext)s"),
            # Prioriza MP4 (vídeo) + M4A (áudio). Se não rolar, pega bestvideo+bestaudio. Fallback 'best'.
            "format": "((bestvideo[ext=mp4]/bestvideo)+bestaudio[ext=m4a]/(bestvideo+bestaudio)/best)",
            "format_sort": [
                "res:4320", "res:2160", "res:1440", "res:1080", "res",
                "fps", "vcodec:av01", "vcodec:vp9", "vcodec:h264"
            ],
            # Diz ao yt_dlp para gerar MP4 no merge quando possível.
            "merge_output_format": "mp4",
            # Remux pós-processamento para garantir contêiner MP4 quando compatível.
            "postprocessors": [
                {"key": "FFmpegVideoRemuxer", "preferedformat": "mp4"}
            ],
            "concurrent_fragment_downloads": 5,
            "retries": 10,
            "fragment_retries": 10,
            "http_chunk_size": 10 * 1024 * 1024,  # 10 MiB
            "noplaylist": False,
            "ignoreerrors": "only_download",
            "quiet": False,
            "no_warnings": False,
            "ffmpeg_location": ffmpeg_dir,  # <- AQUI usamos o FFmpeg detectado
        }

    # Cookies se houver
    if args.cookies:
        if not os.path.exists(args.cookies):
            print(f"[!] cookies.txt não encontrado: {args.cookies}")
            sys.exit(1)
        ydl_opts["cookiefile"] = args.cookies

    print(f"Saída: {outdir.resolve()}")
    if args.cookies:
        print(f"Usando cookies: {args.cookies}")
    print(f"FFmpeg em: {ffmpeg_dir}")
    print(f"URLs/Playlists: {len(urls)}")
    if args.audio_only:
        print("Modo: ÁUDIO APENAS (M4A)")

    # Download + merge
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download(urls)


if __name__ == "__main__":
    main()

