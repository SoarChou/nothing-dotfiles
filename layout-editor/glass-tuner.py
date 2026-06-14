#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Waybar 玻璃质感调节器 (GTK3 滑块面板)
- 调 CSS 的 @glass (玻璃浓度) / @stroke (描边强度) 的 alpha
- 拖动滑块松手即应用 (sed 改 CSS + 重启 waybar)
运行: python3 ~/.config/waybar/layout-editor/glass-tuner.py
"""
import os, re, subprocess
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

HOME = os.path.expanduser("~")
CSS = os.path.realpath(os.path.join(HOME, ".config/waybar/style.css"))

# 可调变量: 名 -> (正则锁定 rgba 的 RGB 部分, 当前 alpha)
VARS = {
    "glass":  {"label": "玻璃浓度 (越大越实/越不透)", "rgb": "18, 18, 18"},
    "glassDim": {"label": "次级玻璃浓度", "rgb": "18, 18, 18"},
    "stroke": {"label": "描边强度", "rgb": "255, 255, 255"},
}


def read_alpha(name):
    s = open(CSS, encoding="utf-8").read()
    m = re.search(r'@define-color\s+%s\s+rgba\([^)]*?,\s*([\d.]+)\s*\)' % name, s)
    return float(m.group(1)) if m else 0.0


def write_alpha(name, alpha):
    s = open(CSS, encoding="utf-8").read()
    # 替换该变量 rgba 的 alpha (最后一个数)
    def repl(m):
        return re.sub(r'([\d.]+)(\s*\)$)', "%.2f\\2" % alpha, m.group(0))
    s = re.sub(r'@define-color\s+%s\s+rgba\([^)]*\)' % name, repl, s, count=1)
    open(CSS, "w", encoding="utf-8").write(s)


def reload_waybar():
    subprocess.run("killall waybar 2>/dev/null; sleep 0.6; "
                   "nohup waybar >/tmp/waybar-nothing.log 2>&1 &", shell=True)


CSS_STYLE = """
* { font-family: "Doto Nerd Font Black","Fusion Pixel 12px Prop zh_hans",monospace; }
window { background:#121212; }
label { color:#ffffff; }
.title { font-size:16px; color:#ffffff; }
.sub { font-size:11px; color:rgba(255,255,255,0.45); }
scale { min-width:280px; }
scale highlight { background:#d71921; }
.applybtn { background:#d71921; color:#fff; border-radius:12px; padding:8px 18px; }
"""


class Tuner(Gtk.Window):
    def __init__(self):
        super().__init__(title="Waybar 玻璃调节器")
        try:
            self.set_wmclass("waybar-glass-tuner", "waybar-glass-tuner")
        except Exception:
            pass
        self.set_role("waybar-glass-tuner")
        self.set_default_size(420, 280)
        self.set_border_width(16)
        prov = Gtk.CssProvider(); prov.load_from_data(CSS_STYLE.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(root)
        t = Gtk.Label(label="玻璃质感调节", xalign=0); t.get_style_context().add_class("title")
        root.pack_start(t, False, False, 0)

        self.scales = {}
        for name, info in VARS.items():
            lab = Gtk.Label(label=info["label"], xalign=0)
            lab.get_style_context().add_class("sub")
            root.pack_start(lab, False, False, 0)
            adj = Gtk.Adjustment(value=read_alpha(name), lower=0.0, upper=1.0,
                                 step_increment=0.01, page_increment=0.05)
            sc = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adj)
            sc.set_digits(2)
            sc.set_value_pos(Gtk.PositionType.RIGHT)
            sc.connect("button-release-event", self.on_release, name)
            sc.connect("key-release-event", self.on_release, name)
            self.scales[name] = sc
            root.pack_start(sc, False, False, 0)

        self.status = Gtk.Label(label="拖动滑块松手即应用", xalign=0)
        self.status.get_style_context().add_class("sub")
        root.pack_start(self.status, False, False, 0)

        bbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        close = Gtk.Button(label="关闭 (Esc)")
        close.connect("clicked", lambda b: Gtk.main_quit())
        bbox.pack_end(close, False, False, 0)
        root.pack_start(bbox, False, False, 0)
        self.connect("key-press-event", self.on_key)

    def on_release(self, widget, ev, name):
        alpha = widget.get_value()
        write_alpha(name, alpha)
        self.status.set_text("已应用 %s = %.2f, 重载中..." % (name, alpha))
        GLib.timeout_add(50, lambda: (reload_waybar(), False)[1])
        return False

    def on_key(self, w, ev):
        if ev.keyval == Gdk.KEY_Escape:
            Gtk.main_quit()
            return True
        return False


if __name__ == "__main__":
    GLib.set_prgname("waybar-glass-tuner")
    win = Tuner()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
