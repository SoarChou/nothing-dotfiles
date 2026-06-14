#!/usr/bin/env bash
# Nothing Waybar 主题安装脚本
# 仿 Nothing Phone 设计: Doto 点阵字 + 毛玻璃 + 黑白单色 + Nothing 红 + 上下分栏
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WB="$HOME/.config/waybar"
HYPR_USER="$HOME/.config/hypr/UserConfigs"
FONTDIR="$HOME/.local/share/fonts/nothing-waybar"
FCDIR="$HOME/.config/fontconfig"

c_red='\033[0;31m'; c_grn='\033[0;32m'; c_yel='\033[0;33m'; c_rst='\033[0m'
info() { echo -e "${c_grn}::${c_rst} $*"; }
warn() { echo -e "${c_yel}!!${c_rst} $*"; }
err()  { echo -e "${c_red}xx${c_rst} $*" >&2; }

# ---------- 依赖检查 ----------
need_cmd() { command -v "$1" >/dev/null 2>&1; }

info "检查依赖..."
MISSING=()
need_cmd waybar    || MISSING+=("waybar")
need_cmd hyprctl   || warn "未检测到 hyprctl (非 Hyprland? 毛玻璃与浮动规则将不可用)"
need_cmd fc-cache  || MISSING+=("fontconfig")
if (( ${#MISSING[@]} )); then
  err "缺少依赖: ${MISSING[*]}"
  err "请先安装后重试 (Arch: sudo pacman -S ${MISSING[*]}; Ubuntu: sudo apt install ${MISSING[*]})"
  exit 1
fi

# ---------- 备份 ----------
TS="$(date +%Y%m%d-%H%M%S)"
backup() {
  local f="$1"
  if [[ -e "$f" && ! -L "$f" ]]; then
    cp -r "$f" "$f.bak-$TS"
    warn "已备份 $f → $f.bak-$TS"
  fi
}

# ---------- 字体安装 ----------
install_fonts() {
  info "安装字体..."
  mkdir -p "$FONTDIR"
  # 打包的字体: Doto Black (Nerd 已打补丁) + Fusion Pixel 简体中文
  cp -f "$REPO/fonts/DotoNerdFont-Black.ttf" "$FONTDIR/" 2>/dev/null || true
  cp -f "$REPO/fonts/fusion-pixel-12px-proportional-zh_hans.ttf" "$FONTDIR/" 2>/dev/null || true

  # fontconfig: 修复 Nerd Font 图标 PUA 码位被 CJK 抢占
  mkdir -p "$FCDIR"
  if [[ -f "$FCDIR/fonts.conf" ]]; then
    backup "$FCDIR/fonts.conf"
    warn "已存在 fonts.conf, 请手动合并 $REPO/fonts/fontconfig-fonts.conf 的规则"
  else
    cp "$REPO/fonts/fontconfig-fonts.conf" "$FCDIR/fonts.conf"
    info "已写入 fontconfig 规则"
  fi
  fc-cache -f >/dev/null 2>&1
  info "字体缓存已刷新"
}

# ---------- waybar 配置安装 ----------
install_waybar() {
  info "安装 waybar 配置..."
  mkdir -p "$WB/configs" "$WB/style"
  # 模块定义文件 (覆盖前备份)
  for f in Modules ModulesCustom ModulesWorkspaces UserModules; do
    [[ -f "$WB/$f" ]] && backup "$WB/$f"
    cp "$REPO/waybar/$f" "$WB/$f"
  done
  # 布局与样式
  cp "$REPO/waybar/configs/[Nothing] macOS Style" "$WB/configs/"
  cp "$REPO/waybar/style/[Nothing] Dot Matrix.css" "$WB/style/"
  # 软链 config / style.css 指向本主题
  backup "$WB/config"; backup "$WB/style.css"
  ln -sf "configs/[Nothing] macOS Style" "$WB/config"
  ln -sf "style/[Nothing] Dot Matrix.css" "$WB/style.css"
  info "已切换 waybar 到 Nothing 主题"
}

# ---------- Hyprland 片段注入 ----------
inject_hypr() {
  need_cmd hyprctl || return 0
  info "注入 Hyprland 规则 (毛玻璃/浮动编辑器)..."
  mkdir -p "$HYPR_USER"
  local MARK="# >>> nothing-waybar >>>"
  local ENDMARK="# <<< nothing-waybar <<<"
  local target="$HYPR_USER/WindowRules.conf"
  touch "$target"
  if grep -q "$MARK" "$target"; then
    warn "WindowRules.conf 已有 nothing-waybar 块, 跳过"
  else
    {
      echo ""
      echo "$MARK"
      echo "layerrule = match:namespace waybar, blur on"
      echo "layerrule = match:namespace waybar, ignore_alpha 0.1"
      echo "windowrule = match:class waybar-layout-editor, float on, center on, size 1520 450"
      echo "windowrule = match:title Waybar 布局编辑器, float on, center on, size 1520 450"
      echo "$ENDMARK"
    } >> "$target"
    info "已注入毛玻璃 + 浮动编辑器规则"
  fi
  warn "毛玻璃需 Hyprland blur 已启用 (decoration { blur { enabled = true } })"
}

# ---------- 布局编辑器 ----------
install_editor() {
  info "安装布局编辑器..."
  mkdir -p "$WB/layout-editor"
  cp "$REPO/layout-editor/editor.py" "$WB/layout-editor/"
  if command -v python3 >/dev/null && python3 -c "import gi" 2>/dev/null; then
    info "编辑器就绪: python3 $WB/layout-editor/editor.py (或绑 Super+Shift+B)"
  else
    warn "编辑器需 python3-gobject (GTK3): Arch: python-gobject; Ubuntu: python3-gi"
  fi
}


# ---------- 锁屏 hyprlock ----------
install_hyprlock() {
  [[ -f "$REPO/hyprlock/hyprlock.conf" ]] || return 0
  info "安装 hyprlock 锁屏..."
  [[ -f "$HOME/.config/hypr/hyprlock.conf" ]] && backup "$HOME/.config/hypr/hyprlock.conf"
  cp "$REPO/hyprlock/hyprlock.conf" "$HOME/.config/hypr/hyprlock.conf"
}

# ---------- 通知 swaync ----------
install_swaync() {
  [[ -f "$REPO/swaync/style.css" ]] || return 0
  info "安装 swaync 通知样式..."
  mkdir -p "$HOME/.config/swaync"
  [[ -f "$HOME/.config/swaync/style.css" ]] && backup "$HOME/.config/swaync/style.css"
  cp "$REPO/swaync/style.css" "$HOME/.config/swaync/style.css"
  command -v swaync-client >/dev/null && swaync-client -rs 2>/dev/null || true
}

# ---------- rofi 主题 ----------
install_rofi() {
  [[ -d "$REPO/rofi/themes" ]] || return 0
  info "安装 rofi Nothing 主题..."
  mkdir -p "$HOME/.config/rofi/themes"
  cp "$REPO/rofi/themes/"*.rasi "$HOME/.config/rofi/themes/"
  warn "rofi: 如需启用, 把 config.rasi 末尾 @theme 指向 themes/Nothing.rasi"
}

# ---------- 电源菜单 + 音乐脚本 ----------
install_scripts() {
  info "安装电源菜单 + 音乐脚本..."
  mkdir -p "$HOME/.config/hypr/UserScripts"
  [[ -f "$REPO/scripts/WaybarCava.sh" ]] && mkdir -p "$HOME/.config/hypr/scripts" && cp "$REPO/scripts/WaybarCava.sh" "$HOME/.config/hypr/scripts/" && chmod +x "$HOME/.config/hypr/scripts/WaybarCava.sh"
  for sc in NothingPower.sh NothingPlayer.sh; do
    [[ -f "$REPO/scripts/$sc" ]] && cp "$REPO/scripts/$sc" "$HOME/.config/hypr/UserScripts/$sc" && chmod +x "$HOME/.config/hypr/UserScripts/$sc"
  done
  warn "电源菜单/音乐: 绑定见 hypr/UserKeybinds.snippet.conf, 需手动并入你的键位"
}

# ---------- quickshell 概览配色 ----------
install_quickshell() {
  [[ -f "$REPO/quickshell/Appearance.qml" ]] || return 0
  local t="$HOME/.config/quickshell/overview/common/Appearance.qml"
  [[ -f "$t" ]] || { warn "未找到 quickshell overview, 跳过概览配色"; return 0; }
  info "应用 quickshell 概览 Nothing 配色..."
  backup "$t"
  cp "$REPO/quickshell/Appearance.qml" "$t"
}

# ---------- 主流程 ----------
main() {
  echo "=== Nothing Waybar 主题安装 ==="
  install_fonts
  install_waybar
  inject_hypr
  install_editor
  install_hyprlock
  install_swaync
  install_rofi
  install_scripts
  install_quickshell
  echo ""
  info "完成! 重载 waybar:"
  echo "    killall waybar; nohup waybar >/dev/null 2>&1 &"
  need_cmd hyprctl && echo "    hyprctl reload   # 应用毛玻璃/浮动规则"
  echo ""
  info "可选: 装完整 Doto 其它字重 + 重打 Nerd 补丁见 scripts/patch-doto.sh"
}
main "$@"
