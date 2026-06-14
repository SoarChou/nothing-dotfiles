#!/usr/bin/env bash
# 还原 Nothing Waybar 主题 (恢复最近的 .bak, 移除 hypr 注入块)
set -euo pipefail
WB="$HOME/.config/waybar"
HYPR="$HOME/.config/hypr/UserConfigs/WindowRules.conf"
info() { echo -e "\033[0;32m::\033[0m $*"; }

# 移除 hypr 注入块
if [[ -f "$HYPR" ]]; then
  sed -i '/# >>> nothing-waybar >>>/,/# <<< nothing-waybar <<</d' "$HYPR"
  info "已移除 Hyprland nothing-waybar 规则块"
fi
# 恢复最近备份的软链目标 (提示用户手动选主题)
info "请用 waybar 主题切换器选回原主题, 或恢复 $WB/*.bak-* 备份"
info "完成"
