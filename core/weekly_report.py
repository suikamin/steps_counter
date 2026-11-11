# core/weekly_report.py
"""今週（月曜日〜日曜日）の歩数推移を折れ線グラフおよび統計サマリーで表示するモジュール。"""

import math
import tkinter as tk
from datetime import date, timedelta
from typing import Dict, Optional


def create_weekly_report_frame(
    parent: tk.Misc,
    records: Optional[Dict[str, int]],
    goal: int = 8000,
) -> tk.Frame:
    """今週（月曜日～日曜日）の歩数データを折れ線グラフで表示するFrameを作成する。"""
    if records is None:
        records = {}

    today = date.today()
    # 今週の月曜日を取得 (weekday(): 月曜=0, 火曜=1, ..., 日曜=6)
    start_of_week = today - timedelta(days=today.weekday())

    week_data = []
    weekdays_jp = ["月", "火", "水", "木", "金", "土", "日"]

    for i in range(7):
        day = start_of_week + timedelta(days=i)
        key = day.isoformat()
        steps = int(records.get(key, 0))
        is_future = day > today
        recorded = key in records

        week_data.append(
            {
                "date": day,
                "weekday": weekdays_jp[i],
                "steps": steps,
                "recorded": recorded,
                "is_future": is_future,
            }
        )

    # 過去〜今日までのデータで集計（未来の日付は除外）
    past_items = [item for item in week_data if not item["is_future"]]
    total_steps = sum(item["steps"] for item in past_items)
    avg_steps = total_steps / len(past_items) if past_items else 0.0
    achieved_days = sum(1 for item in past_items if item["steps"] >= goal)

    # --------------------------------------------------
    # フレーム設定 (メインウィンドウのタブ用)
    # --------------------------------------------------
    window = tk.Frame(parent, bg="#F0F8FF")

    end_of_week = start_of_week + timedelta(days=6)
    date_range_str = (
        f"{start_of_week.strftime('%Y/%m/%d')} ～ {end_of_week.strftime('%m/%d')}"
    )

    tk.Label(
        window,
        text="今週のレポート",
        font=("Meiryo", 16, "bold"),
        bg="#F0F8FF",
        fg="#0288D1",
    ).pack(pady=(15, 2))

    tk.Label(
        window,
        text=date_range_str,
        font=("Meiryo", 9),
        bg="#F0F8FF",
        fg="#546E7A",
    ).pack(pady=(0, 10))

    # --------------------------------------------------
    # 1. 上部サマリーカード
    # --------------------------------------------------
    summary_card = tk.Frame(window, bg="white", bd=1, relief="solid")
    summary_card.pack(fill="x", padx=20, pady=(0, 12))

    metrics = [
        ("今週の合計", f"{total_steps:,} 歩"),
        ("1日平均", f"{avg_steps:,.0f} 歩"),
        ("目標達成日", f"{achieved_days} / 7日"),
    ]
    for title, val in metrics:
        col_frame = tk.Frame(summary_card, bg="white", padx=10, pady=8)
        col_frame.pack(side="left", expand=True, fill="both")
        tk.Label(
            col_frame, text=title, font=("Meiryo", 8), bg="white", fg="#546E7A"
        ).pack()
        tk.Label(
            col_frame,
            text=val,
            font=("Meiryo", 11, "bold"),
            bg="white",
            fg="#0288D1",
        ).pack(pady=(2, 0))

    # --------------------------------------------------
    # 2. 折れ線グラフ描画エリア (Canvas)
    # --------------------------------------------------
    canvas_width = 390  # メインウィンドウに収まるように調整
    canvas_height = 250
    canvas_card = tk.Frame(window, bg="white", bd=1, relief="solid")
    canvas_card.pack(padx=20, pady=(0, 12))

    canvas = tk.Canvas(
        canvas_card,
        width=canvas_width,
        height=canvas_height,
        bg="white",
        highlightthickness=0,
    )
    canvas.pack(padx=5, pady=5)

    pad_left = 45
    pad_right = 20
    pad_top = 25
    pad_bottom = 40

    graph_w = canvas_width - pad_left - pad_right
    graph_h = canvas_height - pad_top - pad_bottom

    max_steps_in_data = max([item["steps"] for item in week_data] + [goal])
    max_y_value = max(12000, math.ceil(max_steps_in_data / 2000) * 2000 + 2000)

    def get_x(index: int) -> float:
        return pad_left + (graph_w / 6) * index

    def get_y(steps: int) -> float:
        return (canvas_height - pad_bottom) - (steps / max_y_value) * graph_h

    # Y軸グリッド線 & 目盛
    y_step_unit = 5000 if max_y_value <= 15000 else 10000
    for y_val in range(0, max_y_value + 1, y_step_unit):
        y_pos = get_y(y_val)
        canvas.create_line(
            pad_left,
            y_pos,
            canvas_width - pad_right,
            y_pos,
            fill="#E2E8F0",
            width=1,
        )
        canvas.create_text(
            pad_left - 6,
            y_pos,
            text=f"{y_val:,}",
            font=("Meiryo", 7),
            anchor="e",
            fill="#64748B",
        )

    # 目標ライン (8,000歩)
    goal_y = get_y(goal)
    canvas.create_line(
        pad_left,
        goal_y,
        canvas_width - pad_right,
        goal_y,
        fill="#0288D1",
        width=1.5,
        dash=(4, 4),
    )
    canvas.create_text(
        canvas_width - pad_right - 5,
        goal_y - 8,
        text=f"目標: {goal:,}歩",
        font=("Meiryo", 8, "bold"),
        anchor="e",
        fill="#0288D1",
    )

    # 座標の計算
    points = []
    for i, item in enumerate(week_data):
        x = get_x(i)
        y = get_y(item["steps"])
        points.append((x, y, item))

        label_color = "#94A3B8" if item["is_future"] else "#1A252C"
        canvas.create_text(
            x,
            canvas_height - pad_bottom + 12,
            text=item["weekday"],
            font=("Meiryo", 9, "bold"),
            fill=label_color,
        )
        canvas.create_text(
            x,
            canvas_height - pad_bottom + 25,
            text=item["date"].strftime("%m/%d"),
            font=("Meiryo", 7),
            fill="#94A3B8",
        )

    # 折れ線の描画（過去〜今日までの間だけ実線、翌日へは破線）
    for i in range(len(points) - 1):
        x1, y1, item1 = points[i]
        x2, y2, item2 = points[i + 1]

        if not item2["is_future"]:
            canvas.create_line(
                x1,
                y1,
                x2,
                y2,
                fill="#0288D1",
                width=2.5,
                capstyle=tk.ROUND,
                joinstyle=tk.ROUND,
            )
        elif not item1["is_future"] and item2["is_future"]:
            canvas.create_line(
                x1, y1, x2, y2, fill="#CBD5E1", width=1.5, dash=(2, 2)
            )

    # プロット点の描画
    r = 4  # サイズ微調整
    for x, y, item in points:
        if item["is_future"]:
            canvas.create_oval(
                x - r,
                y - r,
                x + r,
                y + r,
                fill="white",
                outline="#CBD5E1",
                width=1.5,
            )
        else:
            is_achieved = item["steps"] >= goal
            dot_color = "#0288D1" if is_achieved else "#94A3B8"
            canvas.create_oval(
                x - r,
                y - r,
                x + r,
                y + r,
                fill="white",
                outline=dot_color,
                width=2,
            )
            canvas.create_oval(
                x - (r - 2),
                y - (r - 2),
                x + (r - 2),
                y + (r - 2),
                fill=dot_color,
                outline="",
            )

            val_text = f"{item['steps']:,}" if item["steps"] > 0 else "0"
            canvas.create_text(
                x, y - 11, text=val_text, font=("Meiryo", 8, "bold"), fill="#1A252C"
            )

    # --------------------------------------------------
    # 3. アドバイスメッセージ
    # --------------------------------------------------
    advice_card = tk.Frame(window, bg="white", bd=1, relief="solid")
    advice_card.pack(fill="x", padx=20, pady=(0, 10))

    if achieved_days >= 5:
        advice_msg = "🎉 素晴らしいペースです！今週も目標達成が見えてきました！"
    elif achieved_days >= 3:
        advice_msg = "👍 いい調子です！週末の散歩で達成日数を増やしましょう。"
    else:
        advice_msg = "💡 無理のない範囲で、あと少し歩数を伸ばしてみましょう！"

    tk.Label(
        advice_card,
        text=f"アドバイス: {advice_msg}",
        font=("Meiryo", 8, "bold"),
        bg="white",
        fg="#0288D1",
        padx=10,
        pady=8,
    ).pack()

    return window