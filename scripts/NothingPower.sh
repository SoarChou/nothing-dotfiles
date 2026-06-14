#!/usr/bin/env bash
# Nothing 风格 rofi 电源菜单 (替代 wlogout, 复用 Nothing rofi 主题)
# 图标用 Nerd Font, rofi 渲染对齐好, 玻璃风统一

lock="󰌾"
suspend="󰒲"
logout="󰍃"
reboot="󰜉"
shutdown="󰐥"
hibernate="󰍜"

# 选项 (图标 + 中文)
options="$lock  Lock
$suspend  Suspend
$logout  Logout
$hibernate  Hibernate
$reboot  Reboot
$shutdown  Shutdown"

theme="$HOME/.config/rofi/themes/Nothing-power.rasi"

chosen=$(echo -e "$options" | rofi -dmenu \
    -theme "$theme" \
    -p "Power" \
    -no-custom \
    -select "Lock")

case "$chosen" in
    *Lock)   "$HOME/.config/hypr/scripts/LockScreen.sh" ;;
    *Suspend)   systemctl suspend ;;
    *Logout)   hyprctl dispatch exit 0 ;;
    *Hibernate)   systemctl hibernate ;;
    *Reboot)   systemctl reboot ;;
    *Shutdown)   systemctl poweroff ;;
esac
