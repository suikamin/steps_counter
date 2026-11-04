# ui/main_window.py
"""メインGUIウィンドウ (WalkingAppGUIPreview) の描画・イベント制御モジュール。"""

import math
import sys
import tkinter as tk
from datetime import date
from pathlib import Path
from tkinter import messagebox
from typing import Optional
from PIL import Image, ImageTk

# --------------------------------------------------
# 親フォルダ(プロジェクトルート)をモジュール検索パスに追加 (ModuleNotFoundError対策)
# --------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.avatar import get_avatar_image
from core.magage_data import load_data, save_data
from core.models import UserProfile
from core.route_search import RouteOptimizer
from core.weekly_report import open_weekly_window as show_weekly_window

# ==========================================
# カラー＆フォント定義（テーマカラー：スカイブルー）
# ==========================================
FONT_FAMILY = "Meiryo"

COLOR_PRIMARY = "#0288D1"       # スカイブルー
COLOR_PRIMARY_HOVER = "#0277BD"

COLOR_ACCENT = "#FF9800"        # ビタミンオレンジ
COLOR_ACCENT_HOVER = "#F57C00"
COLOR_ACCENT_TEXT = "#FFFFFF"

BG_MAIN = "#F0F8FF"
BG_CARD = "#FFFFFF"
BG_HEADER = "#0288D1"
BG_NAVBAR = "#0288D1"

TEXT_MAIN = "#1A252C"
TEXT_SUB = "#546E7A"
BORDER_COLOR = "#B3E5FC"


class WalkingAppGUIPreview:
    """ウォーキング支援＆アバター育成アプリのメインGUIコントローラークラス。"""

    GOAL: int = UserProfile.DEFAULT_TARGET_STEPS
    MAX_LEVEL: int = UserProfile.MAX_LEVEL

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("🚶 ウォーキング支援＆アバター育成")
        self.root.geometry("440x700")
        self.root.configure(bg=BG_MAIN)
        self.root.resizable(False, False)

        # 経路探索エンジンの初期化と開始・終了地点の座標変数
        self.optimizer = RouteOptimizer()
        self.start_lat: float = RouteOptimizer.DEFAULT_START_COORDS[0]
        self.start_lng: float = RouteOptimizer.DEFAULT_START_COORDS[1]
        self.end_lat: float = RouteOptimizer.DEFAULT_END_COORDS[0]
        self.end_lng: float = RouteOptimizer.DEFAULT_END_COORDS[1]

        # core.magage_data からデータをロード
        self.records: dict[str, int] = {}
        self.height: float = UserProfile.DEFAULT_HEIGHT
        self.profile: UserProfile = UserProfile()
        self.reload_data()

        self.title_frame: Optional[tk.Frame] = None
        self.app_container: Optional[tk.Frame] = None
        self.content_frame: Optional[tk.Frame] = None
        self.weekly_window: Optional[tk.Toplevel] = None

        # アニメーション用変数
        self.blink_job: Optional[str] = None
        self.sway_job: Optional[str] = None
        self.sway_step: int = 0
        self.raw_avatar_img: Optional[Image.Image] = None
        self.avatar_target_label: Optional[tk.Label] = None

        self.show_title_screen()

    def reload_data(self) -> None:
        """永続化ストレージから最新データを読み込んでUserProfileを更新する。"""
        data = load_data()
        self.records = data.get("records", {})
        self.height = float(data.get("height", UserProfile.DEFAULT_HEIGHT))

        today_key = date.today().isoformat()
        today_steps = int(self.records.get(today_key, 0))
        self.profile = UserProfile(
            height=self.height,
            current_steps=today_steps,
            target_steps=self.GOAL,
        )

    # --------------------------------------------------
    # 角丸・多重ラップゲージ描画
    # --------------------------------------------------
    def create_rounded_card(
        self, parent: tk.Widget, width: int, height: int, bg: str = BG_CARD
    ) -> tk.Canvas:
        canvas = tk.Canvas(
            parent, width=width, height=height, bg=parent["bg"], highlightthickness=0
        )
        r = 16
        canvas.create_arc(
            (0, 0, r * 2, r * 2), start=90, extent=90, fill=bg, outline=BORDER_COLOR
        )
        canvas.create_arc(
            (width - r * 2, 0, width, r * 2),
            start=0,
            extent=90,
            fill=bg,
            outline=BORDER_COLOR,
        )
        canvas.create_arc(
            (0, height - r * 2, r * 2, height),
            start=180,
            extent=90,
            fill=bg,
            outline=BORDER_COLOR,
        )
        canvas.create_arc(
            (width - r * 2, height - r * 2, width, height),
            start=270,
            extent=90,
            fill=bg,
            outline=BORDER_COLOR,
        )

        canvas.create_rectangle((r, 0, width - r, height), fill=bg, outline="")
        canvas.create_rectangle((0, r, width, height - r), fill=bg, outline="")

        canvas.create_line((r, 0, width - r, 0), fill=BORDER_COLOR)
        canvas.create_line((r, height, width - r, height), fill=BORDER_COLOR)
        canvas.create_line((0, r, 0, height - r), fill=BORDER_COLOR)
        canvas.create_line((width, r, width, height - r), fill=BORDER_COLOR)
        return canvas

    def draw_donut_gauge(self, parent: tk.Widget, size: int = 150) -> tk.Canvas:
        canvas = tk.Canvas(
            parent, width=size, height=size, bg=BG_CARD, highlightthickness=0
        )
        p = self.profile
        target = p.target_steps if p.target_steps > 0 else self.GOAL
        steps = p.current_steps

        pad = 10
        thickness = 18

        laps = steps // target
        remainder = steps % target
        progress_in_lap = remainder / target

        COLOR_LAP_0 = "#E1F5FE"
        COLOR_LAP_1 = "#0288D1"
        COLOR_LAP_2 = "#1565C0"
        COLOR_LAP_3 = "#FF9800"

        if laps == 0:
            bg_color, fg_color = COLOR_LAP_0, COLOR_LAP_1
        elif laps == 1:
            bg_color, fg_color = COLOR_LAP_1, COLOR_LAP_2
        else:
            bg_color, fg_color = COLOR_LAP_2, COLOR_LAP_3

        angle = progress_in_lap * 360

        canvas.create_oval(
            pad, pad, size - pad, size - pad, outline=bg_color, width=thickness
        )
        if angle > 0:
            canvas.create_arc(
                pad,
                pad,
                size - pad,
                size - pad,
                start=90,
                extent=-angle,
                style=tk.ARC,
                outline=fg_color,
                width=thickness,
            )

        if p.remaining_steps > 0:
            canvas.create_text(
                size // 2,
                size // 2 - 18,
                text="目標まで",
                font=(FONT_FAMILY, 9),
                fill=TEXT_SUB,
            )
            canvas.create_line(
                size // 2 - 35,
                size // 2 - 6,
                size // 2 + 35,
                size // 2 - 6,
                fill=BORDER_COLOR,
            )
            canvas.create_text(
                size // 2,
                size // 2 + 10,
                text=f"-{p.remaining_steps:,}",
                font=(FONT_FAMILY, 15, "bold"),
                fill=TEXT_MAIN,
            )
            canvas.create_text(
                size // 2,
                size // 2 + 28,
                text="歩",
                font=(FONT_FAMILY, 8, "bold"),
                fill=TEXT_SUB,
            )
        else:
            canvas.create_text(
                size // 2,
                size // 2 - 18,
                text="目標より",
                font=(FONT_FAMILY, 9),
                fill=TEXT_SUB,
            )
            canvas.create_line(
                size // 2 - 35,
                size // 2 - 6,
                size // 2 + 35,
                size // 2 - 6,
                fill=BORDER_COLOR,
            )
            canvas.create_text(
                size // 2,
                size // 2 + 10,
                text=f"+{p.over_steps:,}",
                font=(FONT_FAMILY, 15, "bold"),
                fill=fg_color,
            )
            canvas.create_text(
                size // 2,
                size // 2 + 28,
                text="歩",
                font=(FONT_FAMILY, 8, "bold"),
                fill=TEXT_SUB,
            )

        return canvas

    # --------------------------------------------------
    # 画面 1: タイトル画面
    # --------------------------------------------------
    def show_title_screen(self) -> None:
        self.stop_sway_animation()
        if self.app_container:
            self.app_container.destroy()

        self.title_frame = tk.Frame(self.root, bg=COLOR_PRIMARY, cursor="hand2")
        self.title_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            self.title_frame,
            text="― 毎日の歩みを、アバターの力に ―",
            font=(FONT_FAMILY, 10, "bold"),
            fg="#E1F5FE",
            bg=COLOR_PRIMARY,
        ).pack(pady=(120, 8))
        tk.Label(
            self.title_frame,
            text="Walking &\nAvatar Growth",
            font=(FONT_FAMILY, 26, "bold"),
            fg="#FFFFFF",
            bg=COLOR_PRIMARY,
            justify="center",
        ).pack(pady=10)

        logo_card = self.create_rounded_card(
            self.title_frame, width=160, height=160, bg=BG_CARD
        )
        logo_card.pack(pady=30)

        self.logo_label = tk.Label(logo_card, bg=BG_CARD)
        logo_card.create_window(80, 80, window=self.logo_label)
        self.load_avatar_image(
            self.logo_label, level=self.profile.current_level, size=(140, 140), enable_sway=True
        )

        self.touch_lbl = tk.Label(
            self.title_frame,
            text="― TOUCH TO START ―\n( 画面をタッチしてスタート )",
            font=(FONT_FAMILY, 11, "bold"),
            fg="#FFFFFF",
            bg=COLOR_PRIMARY,
            justify="center",
        )
        self.touch_lbl.pack(pady=20)

        for w in [self.title_frame, logo_card, self.logo_label, self.touch_lbl]:
            w.bind("<Button-1>", lambda e: self.show_main_app())

        self.animate_touch_label()

    def animate_touch_label(self) -> None:
        if hasattr(self, "touch_lbl") and self.touch_lbl.winfo_exists():
            next_fg = (
                "#0288D1" if self.touch_lbl.cget("fg") == "#FFFFFF" else "#FFFFFF"
            )
            self.touch_lbl.config(fg=next_fg)
            self.blink_job = self.root.after(600, self.animate_touch_label)

    # --------------------------------------------------
    # 画面 2: メインアプリ
    # --------------------------------------------------
    def show_main_app(self) -> None:
        if self.blink_job:
            self.root.after_cancel(self.blink_job)
            self.blink_job = None

        if self.title_frame:
            self.title_frame.destroy()

        self.app_container = tk.Frame(self.root, bg=BG_MAIN)
        self.app_container.pack(fill=tk.BOTH, expand=True)

        header = tk.Frame(self.app_container, bg=BG_HEADER, height=50)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)

        tk.Label(
            header,
            text="Walking & Avatar Growth",
            font=(FONT_FAMILY, 12, "bold"),
            fg="#FFFFFF",
            bg=BG_HEADER,
        ).pack(expand=True)

        self.content_frame = tk.Frame(self.app_container, bg=BG_MAIN)
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        self.create_bottom_navbar()
        self.switch_tab("home")

    def create_bottom_navbar(self) -> None:
        nav_bar = tk.Frame(self.app_container, bg=BG_NAVBAR, height=58)
        nav_bar.pack(fill=tk.X, side=tk.BOTTOM)
        nav_bar.pack_propagate(False)

        buttons = [
            ("🏠\nホーム", "home", 0.0, 0.25),
            ("✏️\n記録", "record", 0.25, 0.25),
            ("🗺️\nルート", "route", 0.50, 0.25),
            ("📊\nレポート", "weekly", 0.75, 0.25),
        ]

        for text, tab, relx, relw in buttons:
            btn = tk.Button(
                nav_bar,
                text=text,
                command=lambda t=tab: self.switch_tab(t),
                bg=BG_NAVBAR,
                fg="white",
                font=(FONT_FAMILY, 9, "bold"),
                bd=0,
                activebackground=COLOR_PRIMARY_HOVER,
                activeforeground="white",
                cursor="hand2",
            )
            btn.place(relx=relx, rely=0.0, relwidth=relw, relheight=1.0)

    def switch_tab(self, tab_name: str) -> None:
        if tab_name == "weekly":
            self.reload_data()
            if self.weekly_window is not None and self.weekly_window.winfo_exists():
                self.weekly_window.destroy()
            self.weekly_window = show_weekly_window(self.root, self.records, self.GOAL)
            return

        self.stop_sway_animation()
        if self.content_frame is None:
            return
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        if tab_name == "home":
            self.render_home_tab()
        elif tab_name == "record":
            self.render_record_tab()
        elif tab_name == "route":
            self.render_route_tab()

    # --------------------------------------------------
    # 各カテゴリー画面
    # --------------------------------------------------
    def render_home_tab(self) -> None:
        """【ホーム画面】"""
        self.reload_data()
        avatar_card = self.create_rounded_card(
            self.content_frame, width=190, height=180
        )
        avatar_card.pack(pady=10)

        img_lbl = tk.Label(avatar_card, bg=BG_CARD)
        avatar_card.create_window(95, 90, window=img_lbl)

        self.load_avatar_image(
            img_lbl,
            level=self.profile.current_level,
            size=(160, 160),
            enable_sway=True,
        )

        status_card = self.create_rounded_card(
            self.content_frame, width=390, height=220
        )
        status_card.pack(pady=5)

        p = self.profile
        inner_frame = tk.Frame(status_card, bg=BG_CARD)
        status_card.create_window(195, 110, window=inner_frame)

        left_info = tk.Frame(inner_frame, bg=BG_CARD)
        left_info.pack(side=tk.LEFT, padx=(0, 10), fill=tk.Y)

        tk.Label(
            left_info,
            text=f"Lv.{p.current_level}",
            font=(FONT_FAMILY, 15, "bold"),
            fg=COLOR_ACCENT,
            bg=BG_CARD,
        ).pack(anchor="w")
        tk.Label(
            left_info,
            text="本日の歩数",
            font=(FONT_FAMILY, 9),
            fg=TEXT_SUB,
            bg=BG_CARD,
        ).pack(anchor="w", pady=(6, 0))

        step_box = tk.Frame(left_info, bg=BG_CARD)
        step_box.pack(anchor="w")
        tk.Label(
            step_box,
            text=f"{p.current_steps:,}",
            font=(FONT_FAMILY, 22, "bold"),
            fg=TEXT_MAIN,
            bg=BG_CARD,
        ).pack(side=tk.LEFT)
        tk.Label(
            step_box,
            text=" 歩",
            font=(FONT_FAMILY, 10, "bold"),
            fg=TEXT_MAIN,
            bg=BG_CARD,
        ).pack(side=tk.LEFT, pady=(8, 0))

        tk.Label(
            left_info,
            text=f"目標 {p.target_steps:,} 歩",
            font=(FONT_FAMILY, 9),
            fg=TEXT_SUB,
            bg=BG_CARD,
        ).pack(anchor="w", pady=(0, 6))

        rem_text = (
            f"必要距離: {p.target_distance_km} km"
            if p.remaining_steps > 0
            else "🎉 目標達成！"
        )
        tk.Label(
            left_info,
            text=rem_text,
            font=(FONT_FAMILY, 9, "bold"),
            fg=COLOR_PRIMARY,
            bg=BG_CARD,
        ).pack(anchor="w")

        next_text = (
            f"次Lvまで {p.next_level_steps:,}歩"
            if p.current_level < self.MAX_LEVEL
            else "★ MAX"
        )
        tk.Label(
            left_info,
            text=next_text,
            font=(FONT_FAMILY, 8),
            fg=TEXT_SUB,
            bg=BG_CARD,
        ).pack(anchor="w", pady=(2, 0))

        gauge_canvas = self.draw_donut_gauge(inner_frame, size=150)
        gauge_canvas.pack(side=tk.RIGHT, padx=(10, 0))

    def render_record_tab(self) -> None:
        """【歩数記録画面】"""
        card = self.create_rounded_card(self.content_frame, width=390, height=320)
        card.pack(pady=20)

        inner = tk.Frame(card, bg=BG_CARD)
        card.create_window(195, 160, window=inner)

        tk.Label(
            inner,
            text="✏️ 歩数と身長の記録",
            font=(FONT_FAMILY, 14, "bold"),
            fg=COLOR_PRIMARY,
            bg=BG_CARD,
        ).pack(pady=(0, 10))

        tk.Label(
            inner,
            text="本日追加する歩数",
            font=(FONT_FAMILY, 9),
            fg=TEXT_SUB,
            bg=BG_CARD,
        ).pack(anchor="w")
        self.step_entry = tk.Entry(
            inner, font=(FONT_FAMILY, 12), justify="center", bd=1, relief="solid"
        )
        self.step_entry.pack(fill="x", ipady=5, pady=(2, 10))

        tk.Label(
            inner,
            text="身長 (cm)",
            font=(FONT_FAMILY, 9),
            fg=TEXT_SUB,
            bg=BG_CARD,
        ).pack(anchor="w")
        self.height_entry = tk.Entry(
            inner, font=(FONT_FAMILY, 12), justify="center", bd=1, relief="solid"
        )
        self.height_entry.pack(fill="x", ipady=5, pady=(2, 15))
        self.height_entry.insert(0, str(self.profile.height))

        update_btn = tk.Button(
            inner,
            text="記録・保存する",
            command=self.on_update_steps,
            bg=COLOR_PRIMARY,
            fg="white",
            activebackground=COLOR_PRIMARY_HOVER,
            activeforeground="white",
            font=(FONT_FAMILY, 10, "bold"),
            pady=8,
            padx=25,
            relief=tk.FLAT,
            cursor="hand2",
        )
        update_btn.pack(fill="x")

    def render_route_tab(self) -> None:
        """【ルート検索画面】"""
        card = self.create_rounded_card(self.content_frame, width=390, height=470)
        card.pack(pady=15)

        inner = tk.Frame(card, bg=BG_CARD)
        card.create_window(195, 235, window=inner, width=340)

        tk.Label(
            inner,
            text="🗺️ 周回ルート検索",
            font=(FONT_FAMILY, 14, "bold"),
            fg=COLOR_PRIMARY,
            bg=BG_CARD,
        ).pack(pady=(0, 6))

        rem_km = self.profile.target_distance_km
        if rem_km > 0:
            info_text = f"目標達成に必要な距離: {rem_km} km"
        else:
            info_text = "🎉 今日の目標歩数は達成されています！"

        tk.Label(
            inner,
            text=info_text,
            font=(FONT_FAMILY, 10, "bold"),
            fg=TEXT_MAIN,
            bg=BG_CARD,
            justify="center",
        ).pack(pady=(0, 10))

        # --- 開始地点 (始点 A) の緯度・経度入力 ---
        tk.Label(
            inner,
            text="📍 開始地点 (始点 A)",
            font=(FONT_FAMILY, 9, "bold"),
            fg=COLOR_PRIMARY,
            bg=BG_CARD,
        ).pack(anchor="w", pady=(2, 2))

        start_lat_frame = tk.Frame(inner, bg=BG_CARD)
        start_lat_frame.pack(fill="x", pady=2)
        tk.Label(
            start_lat_frame,
            text="緯度 (Lat):",
            font=(FONT_FAMILY, 9),
            fg=TEXT_SUB,
            bg=BG_CARD,
            width=10,
            anchor="w",
        ).pack(side="left")
        self.start_lat_entry = tk.Entry(
            start_lat_frame,
            font=(FONT_FAMILY, 10),
            justify="center",
            bd=1,
            relief="solid",
        )
        self.start_lat_entry.pack(side="left", fill="x", expand=True, ipady=3)
        self.start_lat_entry.insert(0, str(self.start_lat))

        start_lng_frame = tk.Frame(inner, bg=BG_CARD)
        start_lng_frame.pack(fill="x", pady=(2, 8))
        tk.Label(
            start_lng_frame,
            text="経度 (Lng):",
            font=(FONT_FAMILY, 9),
            fg=TEXT_SUB,
            bg=BG_CARD,
            width=10,
            anchor="w",
        ).pack(side="left")
        self.start_lng_entry = tk.Entry(
            start_lng_frame,
            font=(FONT_FAMILY, 10),
            justify="center",
            bd=1,
            relief="solid",
        )
        self.start_lng_entry.pack(side="left", fill="x", expand=True, ipady=3)
        self.start_lng_entry.insert(0, str(self.start_lng))

        # --- 終了地点 (終点 B) の緯度・経度入力 ---
        tk.Label(
            inner,
            text="🏁 終了地点 (終点 B)",
            font=(FONT_FAMILY, 9, "bold"),
            fg=COLOR_PRIMARY,
            bg=BG_CARD,
        ).pack(anchor="w", pady=(2, 2))

        end_lat_frame = tk.Frame(inner, bg=BG_CARD)
        end_lat_frame.pack(fill="x", pady=2)
        tk.Label(
            end_lat_frame,
            text="緯度 (Lat):",
            font=(FONT_FAMILY, 9),
            fg=TEXT_SUB,
            bg=BG_CARD,
            width=10,
            anchor="w",
        ).pack(side="left")
        self.end_lat_entry = tk.Entry(
            end_lat_frame,
            font=(FONT_FAMILY, 10),
            justify="center",
            bd=1,
            relief="solid",
        )
        self.end_lat_entry.pack(side="left", fill="x", expand=True, ipady=3)
        self.end_lat_entry.insert(0, str(self.end_lat))

        end_lng_frame = tk.Frame(inner, bg=BG_CARD)
        end_lng_frame.pack(fill="x", pady=(2, 12))
        tk.Label(
            end_lng_frame,
            text="経度 (Lng):",
            font=(FONT_FAMILY, 9),
            fg=TEXT_SUB,
            bg=BG_CARD,
            width=10,
            anchor="w",
        ).pack(side="left")
        self.end_lng_entry = tk.Entry(
            end_lng_frame,
            font=(FONT_FAMILY, 10),
            justify="center",
            bd=1,
            relief="solid",
        )
        self.end_lng_entry.pack(side="left", fill="x", expand=True, ipady=3)
        self.end_lng_entry.insert(0, str(self.end_lng))

        route_btn = tk.Button(
            inner,
            text="開始する（マップでルート検索）",
            command=self.on_search_route,
            bg=COLOR_ACCENT,
            fg=COLOR_ACCENT_TEXT,
            activebackground=COLOR_ACCENT_HOVER,
            activeforeground=COLOR_ACCENT_TEXT,
            font=(FONT_FAMILY, 10, "bold"),
            pady=9,
            padx=20,
            relief=tk.FLAT,
            cursor="hand2",
        )
        route_btn.pack(fill="x", pady=(4, 0))

    # --------------------------------------------------
    # アニメーション ＆ イベント処理
    # --------------------------------------------------
    def load_avatar_image(
        self,
        target_label: tk.Label,
        level: int = 1,
        size: tuple[int, int] = (170, 170),
        enable_sway: bool = False,
    ) -> None:
        """core.avatar からレベルに応じたアバター画像を取得・描画する。"""
        self.stop_sway_animation()

        try:
            self.raw_avatar_img = get_avatar_image(level=level, size=size)
            self.avatar_target_label = target_label

            if enable_sway:
                self.sway_step = 0
                self.animate_sway()
            else:
                tk_img = ImageTk.PhotoImage(self.raw_avatar_img)
                target_label.image = tk_img
                target_label.config(image=tk_img, text="", bg=BG_CARD)
        except Exception as e:
            target_label.config(
                text=f"[ avatar_lv{level}.png ]\n({e})",
                fg=TEXT_SUB,
                bg=BG_CARD,
                font=(FONT_FAMILY, 9),
            )

    def animate_sway(self) -> None:
        """サイン波を用いて植物アバターの風揺れアニメーションを描画する。"""
        if (
            self.raw_avatar_img
            and self.avatar_target_label
            and self.avatar_target_label.winfo_exists()
        ):
            angle = math.sin(self.sway_step * 0.08) * 3.5
            self.sway_step += 1

            w, h = self.raw_avatar_img.size
            rotated_img = self.raw_avatar_img.rotate(
                angle,
                resample=Image.Resampling.BICUBIC,
                center=(w // 2, int(h * 0.85)),
            )

            tk_img = ImageTk.PhotoImage(rotated_img)
            self.avatar_target_label.image = tk_img
            self.avatar_target_label.config(image=tk_img, text="", bg=BG_CARD)

            self.sway_job = self.root.after(33, self.animate_sway)

    def stop_sway_animation(self) -> None:
        if self.sway_job:
            self.root.after_cancel(self.sway_job)
            self.sway_job = None

    def on_update_steps(self) -> None:
        """歩数加算と身長データのバリデーション・アトミック保存を行う。"""
        raw_steps = self.step_entry.get().strip()
        raw_height = self.height_entry.get().strip()

        if not raw_steps.isdigit():
            messagebox.showwarning(
                "入力エラー", "追加歩数は半角の数字（0以上の整数）で入力してください。"
            )
            return

        try:
            height = float(raw_height)
            if height <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "入力エラー", "身長は正の数値で入力してください。"
            )
            return

        added_steps = int(raw_steps)
        today = date.today().isoformat()

        updated_records = dict(self.records)
        updated_records[today] = updated_records.get(today, 0) + added_steps

        # core.magage_data を使用してアトミック保存
        data_to_save = {"records": updated_records, "height": height}
        if save_data(data_to_save):
            self.reload_data()
            today_steps = self.records[today]
            messagebox.showinfo(
                "更新完了",
                f"歩数を加算して保存しました！\n本日の歩数: {today_steps:,} 歩",
            )
            self.switch_tab("home")
        else:
            messagebox.showerror("保存エラー", "データの保存に失敗しました。")

    def on_search_route(self) -> None:
        """入力された開始・終了座標を変数に代入し、ウォーキングルートを探索してブラウザで地図を開く。"""
        try:
            start_lat = float(self.start_lat_entry.get().strip())
            start_lng = float(self.start_lng_entry.get().strip())
            end_lat = float(self.end_lat_entry.get().strip())
            end_lng = float(self.end_lng_entry.get().strip())

            if not (-90.0 <= start_lat <= 90.0 and -90.0 <= end_lat <= 90.0):
                raise ValueError("緯度は -90 〜 90 の範囲で入力してください。")
            if not (-180.0 <= start_lng <= 180.0 and -180.0 <= end_lng <= 180.0):
                raise ValueError("経度は -180 〜 180 の範囲で入力してください。")
        except ValueError as e:
            messagebox.showwarning(
                "座標入力エラー",
                f"開始地点・終了地点の緯度経度を正しい数値で入力してください。\n({e})",
            )
            return

        # 入力値を変数および RouteOptimizer の座標に代入・上書き
        self.start_lat = start_lat
        self.start_lng = start_lng
        self.end_lat = end_lat
        self.end_lng = end_lng
        start_coords = (self.start_lat, self.start_lng)
        end_coords = (self.end_lat, self.end_lng)
        self.optimizer.start_coords = start_coords
        self.optimizer.end_coords = end_coords

        remaining_km = self.profile.target_distance_km
        if remaining_km <= 0:
            messagebox.showinfo("目標達成", "今日の目標歩数は達成されています！✨")
            return

        messagebox.showinfo("!", "ルートを探索中...")

        try:
            result = self.optimizer.search_and_generate_map(
                target_distance_km=remaining_km,
                start_coords=start_coords,
                end_coords=end_coords,
            )
            actual_km = result["actual_distance_m"] / 1000.0
            messagebox.showinfo(
                "ルート生成完了",
                f"最適ルートを算出してブラウザで開きました！\n"
                f"開始地点: ({self.start_lat:.5f}, {self.start_lng:.5f})\n"
                f"終了地点: ({self.end_lat:.5f}, {self.end_lng:.5f})\n"
                f"目標距離: {remaining_km:.2f} km / 実走距離: {actual_km:.2f} km",
            )
        except Exception as e:
            messagebox.showerror(
                "ルート検索エラー",
                f"経路探索中にエラーが発生しました:\n{e}",
            )
