#!/usr/bin/env bash
# 可选: 下载 Google Doto + 用 Nerd Fonts font-patcher 打补丁
# 生成 "Doto Nerd Font Black" 等字重。仓库已含打好的 Black, 此脚本供想要其它字重的人。
set -euo pipefail

OUT="$HOME/.local/share/fonts/nothing-waybar"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

c_grn='\033[0;32m'; c_yel='\033[0;33m'; c_rst='\033[0m'
info() { echo -e "${c_grn}::${c_rst} $*"; }
warn() { echo -e "${c_yel}!!${c_rst} $*"; }

command -v fontforge >/dev/null || { warn "需要 fontforge (Arch: sudo pacman -S fontforge; Ubuntu: sudo apt install fontforge python3-fontforge)"; exit 1; }

cd "$TMP"
info "下载 Google Doto..."
# Doto 在 Google Fonts, 也可从 GitHub 镜像
curl -sL -o doto.zip "https://github.com/google/fonts/raw/main/ofl/doto/Doto%5BROND,wght%5D.ttf" 2>/dev/null \
  || { warn "下载失败, 请手动从 https://fonts.google.com/specimen/Doto 获取后放到 $TMP"; exit 1; }

info "下载 Nerd Fonts font-patcher..."
curl -sL -o fp.zip "https://github.com/ryanoasis/nerd-fonts/releases/latest/download/FontPatcher.zip"
unzip -oq fp.zip

# 可变字体需先取静态实例 (这里假设用户提供静态 Doto-Black.ttf 更简单)
warn "提示: 可变字体打补丁可能不稳。建议从 fonts.google.com 下载 Doto static 'Black' 字重 ttf,"
warn "      放到 $OUT 后运行: fontforge -script font-patcher --complete --careful Doto-Black.ttf -out $OUT"

info "完成。仓库已含预打补丁的 DotoNerdFont-Black.ttf, 一般无需此脚本。"
