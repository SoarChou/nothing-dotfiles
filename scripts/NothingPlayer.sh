#!/usr/bin/env bash
# Nothing 风格 waybar 音乐模块 — 无音乐/取不到信息时输出空 (模块自动隐藏)
# 输出 waybar JSON: {"text":..., "tooltip":..., "class":...}

play="󰐊"      # nf 播放
pause="󰏤"     # nf 暂停
note="󰝚"      # nf 音符

# 没有任何播放器 → 空输出, 模块隐藏
status=$(playerctl status 2>/dev/null) || { echo ""; exit 0; }

title=$(playerctl metadata title 2>/dev/null)
artist=$(playerctl metadata artist 2>/dev/null)

# 取不到标题 → 空输出
if [ -z "$title" ]; then
    echo ""
    exit 0
fi

# 状态图标
case "$status" in
    Playing) icon="$play" ;;
    Paused)  icon="$pause" ;;
    *)       icon="$note" ;;
esac

# 组合文字: 图标 + 标题 (有艺术家则补)
if [ -n "$artist" ]; then
    text="$icon $title - $artist"
else
    text="$icon $title"
fi

# markup 转义
text=$(echo "$text" | sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g')
tip=$(echo "$title — $artist" | sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g')

printf '{"text":"%s","tooltip":"%s\\n左键 上一首 · 中键 播放/暂停 · 右键 下一首","class":"%s"}\n' "$text" "$tip" "$status"
