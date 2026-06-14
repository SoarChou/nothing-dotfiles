#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Waybar 模块布局编辑器 (原生 GTK3, 无浏览器依赖)
- 6 个区域 (顶栏/底栏 × 左/中/右) + 可用模块池, 拖拽重排
- 保存: 正则就地替换 config 的 modules-* 数组 (保留注释/其它设置), 自动重载 waybar
运行: python3 ~/.config/waybar/layout-editor/editor.py
"""
import os, re, json, subprocess
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

HOME = os.path.expanduser("~")
WB = os.path.join(HOME, ".config/waybar")
CONFIG = os.path.realpath(os.path.join(WB, "config"))
MODULE_FILES = ["Modules", "ModulesCustom", "ModulesGroups",
                "ModulesWorkspaces", "UserModules"]
JUNK = {"format", "format-icons", "calendar", "actions", "states", "drawer",
        "tooltip-format", "player-icons", "status-icons", "modules",
        "persistent-workspaces", "on-click", "rewrite", "window-rewrite"}
DND = [Gtk.TargetEntry.new("text/plain", Gtk.TargetFlags.SAME_APP, 0)]

# 每个区 (左/中/右) 最多模块数, 放满拒绝
MAX_PER_ZONE = 12

# 模块友好显示: ID -> (Nerd图标, 中文名)。没列出的回退显示原 ID。
LABELS = {
    "clock": ("", "时钟"),
    "battery": ("", "电池"),
    "backlight": ("", "亮度"),
    "pulseaudio": ("", "音量"),
    "pulseaudio#microphone": ("", "麦克风"),
    "network": ("", "网络"),
    "network#speed": ("", "网速"),
    "bluetooth": ("", "蓝牙"),
    "cpu": ("", "CPU"),
    "memory": ("", "内存"),
    "temperature": ("", "温度"),
    "disk": ("", "磁盘"),
    "tray": ("", "托盘"),
    "mpris": ("", "音乐"),
    "custom/playerctl": ("", "音乐(playerctl)"),
    "custom/cava_mviz": ("", "频谱条"),
    "idle_inhibitor": ("", "防休眠"),
    "custom/power": ("⏻", "电源"),
    "custom/menu": ("", "菜单"),
    "custom/weather": ("", "天气"),
    "custom/nightlight": ("", "夜灯"),
    "custom/lock": ("", "锁屏"),
    "custom/notification": ("", "通知"),
    "custom/swaync": ("", "通知中心"),
    "custom/updater": ("", "更新"),
    "custom/cycle_wall": ("", "切换壁纸"),
    "custom/light_dark": ("", "明暗切换"),
    "custom/keyboard": ("", "键盘"),
    "custom/hint": ("", "提示"),
    "custom/hypridle": ("", "空闲守护"),
    "custom/file_manager": ("", "文件管理"),
    "custom/browser": ("", "浏览器"),
    "custom/tty": ("", "终端"),
    "custom/settings": ("", "设置"),
    "hyprland/window": ("", "窗口标题"),
    "hyprland/workspaces": ("", "工作区"),
    "hyprland/workspaces#rw": ("", "工作区"),
    "hyprland/language": ("", "输入法"),
    "hyprland/submap": ("", "子模式"),
    "group/audio": ("", "音频组"),
    "group/connections": ("", "连接组"),
    "group/notify": ("", "通知组"),
    "group/status": ("", "状态组"),
    "group/laptop": ("", "笔记本组"),
    "group/power": ("⏻", "电源组"),
    "group/app_drawer": ("", "应用抽屉"),
    "group/motherboard": ("", "硬件组"),
    "group/mobo_drawer": ("", "硬件抽屉"),
}


def chip_label(name):
    if name in LABELS:
        ic, cn = LABELS[name]
        return "%s  %s" % (ic, cn)
    return name



def available_modules():
    names = set()
    for f in MODULE_FILES:
        p = os.path.join(WB, f)
        if not os.path.exists(p):
            continue
        s = open(p, encoding="utf-8").read()
        for m in re.finditer(r'"([a-zA-Z][\w/.#-]*)"\s*:\s*\{', s):
            names.add(m.group(1))
    return sorted(n for n in names if n not in JUNK)


def strip_jsonc(s):
    s = re.sub(r'/\*.*?\*/', '', s, flags=re.S)
    s = re.sub(r'//[^\n]*', '', s)
    s = re.sub(r',(\s*[}\]])', r'\1', s)
    return s


def parse_config():
    data = json.loads(strip_jsonc(open(CONFIG, encoding="utf-8").read()))
    if isinstance(data, dict):
        data = [data]
    bars = []
    for bar in data:
        bars.append({
            "left": list(bar.get("modules-left", [])),
            "center": list(bar.get("modules-center", [])),
            "right": list(bar.get("modules-right", [])),
            "position": bar.get("position", "top"),
        })
    return bars


def save_config(bars):
    raw = open(CONFIG, encoding="utf-8").read()
    open(CONFIG + ".bak", "w", encoding="utf-8").write(raw)
    counters = {}

    def render_arr(items):
        if not items:
            return "[\n\t]"
        return "[\n%s,\n\t]" % ",\n".join('\t\t"%s"' % m for m in items)

    for key in ["modules-left", "modules-center", "modules-right"]:
        counters[key] = 0
        pat = re.compile(r'("%s"\s*:\s*)\[[^\]]*\]' % key)

        def repl(m, key=key):
            idx = counters[key]
            counters[key] += 1
            if idx < len(bars):
                arr = bars[idx].get(key.replace("modules-", ""), [])
                return m.group(1) + render_arr(arr)
            return m.group(0)
        raw = pat.sub(repl, raw)
    open(CONFIG, "w", encoding="utf-8").write(raw)
    subprocess.run("killall waybar 2>/dev/null; sleep 1; "
                   "nohup waybar >/tmp/waybar-nothing.log 2>&1 &", shell=True)


CSS = """
/* Touch Bar 式: 上方预览栏与 waybar 同款, 下方模块托盘 */
* { font-family: "Doto Nerd Font Black", "Doto Nerd Font", "Fusion Pixel 12px Prop zh_hans", monospace; }
window { background:#0e0e0e; }
label, button { color:#ffffff; }
.heading { color:rgba(255,255,255,0.85); font-size:14px; padding:4px 2px; }
.subtle { color:rgba(255,255,255,0.4); font-size:11px; padding:2px; }

/* 预览栏: 模拟 waybar 整条 (深色玻璃长条) */
.previewbar { background:rgba(18,18,18,0.55);
              border:1px solid rgba(255,255,255,0.18);
              border-radius:16px; padding:4px 8px; margin:2px 0; }
/* 三个放置区 */
.zone { border-radius:12px; padding:2px; }
.zone-l { background:rgba(255,255,255,0.03); }
.zone-c { background:rgba(255,255,255,0.05); }
.zone-r { background:rgba(255,255,255,0.03); }
/* 托盘 */
.tray { background:rgba(255,255,255,0.02);
        border:1px dashed rgba(255,255,255,0.15);
        border-radius:12px; padding:4px; }

/* 模块单元: 固定小方框(图标) + 方框外下方放名字 */
.cell { }
.chipbox { background:rgba(18,18,18,0.6);
           border:1px solid rgba(255,255,255,0.28);
           border-radius:12px;
           min-width:38px; min-height:38px;
           box-shadow: inset 0 1px 1px 0 rgba(255,255,255,0.30),
                       inset 0 -1px 1px 0 rgba(0,0,0,0.30);
           transition: all 180ms ease; }
.chipbox:hover { background:rgba(215,25,33,0.85); border-color:#d71921; }
.chip-icon { font-size:16px; color:#ffffff; }
.chip-name { font-size:9px; color:rgba(255,255,255,0.6); padding-top:1px; }
/* 左右微调箭头: 极窄, 整体不超过方框宽度 */
.arrow { background:rgba(255,255,255,0.08); color:rgba(255,255,255,0.65);
         border:none; border-radius:5px; padding:0; margin:0;
         min-height:14px; min-width:17px; font-size:10px; }
.arrow:hover { background:#d71921; color:#ffffff; }

/* 普通按钮(返回等): 深色玻璃, 不用 GTK 默认白底 */
button { background:rgba(18,18,18,0.55); color:#ffffff;
         border:1px solid rgba(255,255,255,0.18);
         border-radius:14px; padding:8px 18px; }
button:hover { background:rgba(255,255,255,0.12);
               border-color:rgba(255,255,255,0.4); }

.savebtn { background:#d71921; color:#ffffff;
           border:1px solid rgba(255,255,255,0.3);
           border-radius:14px; padding:8px 20px; }
.savebtn:hover { background:#ef3b43; }
"""


class Chip(Gtk.EventBox):
    """模块单元: 固定小方框(图标) + 名字 + 左右微调箭头"""
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.zone = None  # 由 add_chip 设置
        ic, cn = LABELS.get(name, ("", name))
        cell = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        cell.get_style_context().add_class("cell")
        cell.set_size_request(40, -1)  # 锁定单元宽度, 防止箭头撑宽导致换行
        # 固定小方框, 内放图标(无图标的用名字首字)
        sq = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sq.get_style_context().add_class("chipbox")
        sq.set_halign(Gtk.Align.CENTER)
        sq.set_valign(Gtk.Align.CENTER)
        il = Gtk.Label(label=ic if ic else cn[:1])
        il.get_style_context().add_class("chip-icon")
        il.set_halign(Gtk.Align.CENTER)
        il.set_valign(Gtk.Align.CENTER)
        il.set_hexpand(True)
        il.set_vexpand(True)
        sq.add(il)
        cell.pack_start(sq, False, False, 0)
        # 方框外的名字
        nl = Gtk.Label(label=cn)
        nl.get_style_context().add_class("chip-name")
        nl.set_halign(Gtk.Align.CENTER)
        cell.pack_start(nl, False, False, 0)
        # 左右微调箭头 (仅在栏内显示, 池里不显示)
        self.arrows = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        self.arrows.set_halign(Gtk.Align.CENTER)
        lb = Gtk.Button(label="‹")
        rb = Gtk.Button(label="›")
        for b in (lb, rb):
            b.get_style_context().add_class("arrow")
        lb.connect("clicked", lambda w: self.zone and self.zone.move_chip(self.name, -1))
        rb.connect("clicked", lambda w: self.zone and self.zone.move_chip(self.name, 1))
        self.arrows.pack_start(lb, False, False, 0)
        self.arrows.pack_start(rb, False, False, 0)
        cell.pack_start(self.arrows, False, False, 0)
        self.set_tooltip_text(name)
        self.add(cell)
        self.drag_source_set(Gdk.ModifierType.BUTTON1_MASK, DND, Gdk.DragAction.MOVE)
        self.connect("drag-data-get", self._get)

    def _get(self, w, ctx, sel, info, t):
        sel.set_text(self.name, -1)


class Zone(Gtk.Box):
    """一个可放置区域 (左/中/右/托盘)"""
    def __init__(self, title, key, app, is_pool=False, style=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.key = key
        self.app = app
        self.is_pool = is_pool
        if title:
            t = Gtk.Label(label=title, xalign=0.5)
            t.get_style_context().add_class("subtle")
            self.pack_start(t, False, False, 0)
        self.flow = Gtk.FlowBox()
        self.flow.set_selection_mode(Gtk.SelectionMode.NONE)
        if is_pool:
            self.flow.set_min_children_per_line(1)
            self.flow.set_max_children_per_line(40)
        else:
            # 栏内: 每行容纳足够多, 按宽度自然单行排 (不因上限卡住换行)
            self.flow.set_min_children_per_line(20)
            self.flow.set_max_children_per_line(20)
        self.flow.set_homogeneous(False)
        self.flow.set_row_spacing(2)
        self.flow.set_column_spacing(2)
        self.flow.set_valign(Gtk.Align.FILL)
        # 空栏也要有高度 (FlowBox 无内容时高度为 0, 会塌成细线)
        if not is_pool:
            self.flow.set_size_request(-1, 56)
        self.flow.get_style_context().add_class("zone")
        if style:
            self.flow.get_style_context().add_class(style)
        if is_pool:
            self.flow.get_style_context().add_class("tray")
        self.flow.drag_dest_set(Gtk.DestDefaults.ALL, DND, Gdk.DragAction.MOVE)
        self.flow.connect("drag-data-received", self._recv)
        self.pack_start(self.flow, True, True, 0)

    def add_chip(self, name):
        chip = Chip(name)
        chip.zone = self
        if self.is_pool:
            chip.arrows.set_no_show_all(True)  # 池里不显示箭头(防 show_all 覆盖)
            chip.arrows.hide()
        self.flow.add(chip)
        chip.show_all()

    def rebuild(self, order):
        """按给定顺序重排 (清空再按序加入)"""
        for child in list(self.flow.get_children()):
            self.flow.remove(child)
        for n in order:
            self.add_chip(n)

    def move_chip(self, name, delta):
        """把 name 在本区内左移(-1)/右移(+1)"""
        order = self.names()
        if name not in order:
            return
        i = order.index(name)
        j = i + delta
        if j < 0 or j >= len(order):
            return
        order[i], order[j] = order[j], order[i]
        self.rebuild(order)
        if self.app:
            self.app.status.set_text("已移动: %s" % name)

    def names(self):
        out = []
        for child in self.flow.get_children():
            ev = child.get_child()
            if isinstance(ev, Chip):
                out.append(ev.name)
        return out

    def _recv(self, w, ctx, x, y, sel, info, t):
        name = sel.get_text()
        if not name:
            return
        # 非池区放满则拒绝
        if not self.is_pool and name not in self.names() \
                and len(self.names()) >= MAX_PER_ZONE:
            if self.app:
                self.app.status.set_text("该区已满 (上限 %d 个)" % MAX_PER_ZONE)
            Gtk.drag_finish(ctx, False, False, t)
            return
        # 从其它非池区域移除 (池里是模板, 拖出是复制)
        for z in self.app.zones:
            if z is self or z.is_pool:
                continue
            for child in list(z.flow.get_children()):
                ev = child.get_child()
                if isinstance(ev, Chip) and ev.name == name:
                    z.flow.remove(child)
        if self.is_pool:
            return  # 拖回池 = 仅删除
        if name not in self.names():
            self.add_chip(name)
        Gtk.drag_finish(ctx, True, False, t)


class App(Gtk.Window):
    def __init__(self):
        super().__init__(title="Waybar 布局编辑器")
        # 固定窗口标识, 供 Hyprland float 规则匹配
        try:
            self.set_wmclass("waybar-layout-editor", "waybar-layout-editor")
        except Exception:
            pass
        self.set_role("waybar-layout-editor")
        self.set_default_size(1500, 430)
        self.set_border_width(12)
        prov = Gtk.CssProvider()
        prov.load_from_data(CSS.encode("utf-8"))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), prov,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.bars = parse_config()
        self.zones = []
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.add(root)

        head = Gtk.Label(label="拖动下方模块到栏里 · 拖回托盘移除", xalign=0)
        head.get_style_context().add_class("heading")
        root.pack_start(head, False, False, 0)

        # 每个 bar 渲染成一条 Touch Bar 式预览栏
        self.bar_zone_map = []
        for i, bar in enumerate(self.bars):
            pos = bar.get("position", "top")
            title = "▔ 顶栏" if pos == "top" else ("▁ 底栏" if pos == "bottom" else "栏 %d" % i)
            cap = Gtk.Label(label=title, xalign=0)
            cap.get_style_context().add_class("subtle")
            root.pack_start(cap, False, False, 0)

            barbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            barbox.set_homogeneous(True)
            barbox.get_style_context().add_class("previewbar")
            zmap = {}
            for key, sty in [("left", "zone-l"), ("center", "zone-c"), ("right", "zone-r")]:
                z = Zone(None, key, self, style=sty)
                for m in bar[key]:
                    z.add_chip(m)
                barbox.pack_start(z, True, True, 0)
                self.zones.append(z)
                zmap[key] = z
            self.bar_zone_map.append(zmap)
            root.pack_start(barbox, False, False, 0)

        # 模块托盘 (Touch Bar 下方的备选区)
        tray_cap = Gtk.Label(label="▾ 模块托盘 (拖上去添加)", xalign=0)
        tray_cap.get_style_context().add_class("subtle")
        root.pack_start(tray_cap, False, False, 0)
        tray_scroll = Gtk.ScrolledWindow()
        tray_scroll.set_min_content_height(150)
        self.pool = Zone(None, "pool", self, is_pool=True)
        for m in available_modules():
            self.pool.add_chip(m)
        self.zones.append(self.pool)
        tray_scroll.add(self.pool)
        root.pack_start(tray_scroll, True, True, 0)

        # 底部按钮
        bbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.status = Gtk.Label(label="Enter 保存 · Esc 退出", xalign=0)
        self.status.get_style_context().add_class("subtle")
        bbox.pack_start(self.status, True, True, 0)
        back = Gtk.Button(label="返回 (Esc)")
        back.connect("clicked", lambda b: Gtk.main_quit())
        bbox.pack_end(back, False, False, 0)
        save = Gtk.Button(label="保存 (Enter)")
        save.get_style_context().add_class("savebtn")
        save.connect("clicked", self.on_save)
        bbox.pack_end(save, False, False, 0)
        root.pack_start(bbox, False, False, 0)

        self.connect("key-press-event", self.on_key)

    def on_save(self, btn):
        out = []
        for zmap in self.bar_zone_map:
            out.append({
                "left": zmap["left"].names(),
                "center": zmap["center"].names(),
                "right": zmap["right"].names(),
            })
        try:
            save_config(out)
            self.status.set_text("已保存并重载 waybar ✓ (备份: config.bak)")
        except Exception as e:
            self.status.set_text("保存失败: %s" % e)

    def on_key(self, w, ev):
        # Esc 退出, Enter 保存
        if ev.keyval == Gdk.KEY_Escape:
            Gtk.main_quit()
            return True
        if ev.keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            self.on_save(None)
            return True
        return False


if __name__ == "__main__":
    GLib.set_prgname("waybar-layout-editor")
    win = App()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
