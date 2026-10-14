# app.py
from src import UserProfile, RouteOptimizer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

class WalkingApp:
    """
    ユーザー入出力および画面レンダリングを制御するコントローラークラス
    """
    BASE_LAT = 37.8694  # 新潟大学五十嵐キャンパス周辺
    BASE_LNG = 138.9430

    def __init__(self):
        self.console = Console()
        self.optimizer = RouteOptimizer(self.BASE_LAT, self.BASE_LNG)
        self._height = 170
        self._current_steps = 0
        self._profile = None

    # --- ゲッターとセッター ---
    @property
    def height(self) -> int:
        """身長のゲッター"""
        return self._height

    @height.setter
    def height(self, value: int):
        """身長のセッター"""
        if not isinstance(value, int) or value <= 0:
            raise ValueError("身長は正の整数を指定してください。")
        self._height = value

    @property
    def current_steps(self) -> int:
        """現在歩数のゲッター"""
        return self._current_steps

    @current_steps.setter
    def current_steps(self, value: int):
        """現在歩数のセッター"""
        if not isinstance(value, int) or value < 0:
            raise ValueError("歩数は0以上の整数を指定してください。")
        self._current_steps = value

    @property
    def profile(self) -> UserProfile:
        """プロファイルのゲッター"""
        return self._profile

    @profile.setter
    def profile(self, value: UserProfile):
        """プロファイルのセッター"""
        self._profile = value

    def run(self):
        self.console.print(Panel.fit("[bold green]🚶 ウォーキング支援シミュレータ 🚶[/bold green]\nバイブス上げて歩数を記録していきましょう🔥"))

        # input() による入力
        user_height_str = input("身長(cm)を入力してください [デフォルト: 170]: ").strip()
        user_steps_str = input("現在の歩数を入力してください [デフォルト: 0]: ").strip()

        # セッター経由で値をセット
        self.height = int(user_height_str) if user_height_str else 170
        self.current_steps = int(user_steps_str) if user_steps_str else 0

        # UserProfile を生成してセッターにセット
        self.profile = UserProfile(self.height, self.current_steps)

        # 結果をリッチなテーブルでサクッと表示
        table = Table(title="📊 今日のウォーキングステータス")
        table.add_column("項目", style="cyan", justify="right")
        table.add_column("値", style="magenta")

        table.add_row("身長", f"{self.height} cm")
        table.add_row("現在歩数", f"{self.current_steps:,} 歩")
        table.add_row("目標歩数", f"{self.profile.target_steps:,} 歩")
        table.add_row("不足歩数", f"{self.profile.remaining_steps:,} 歩")
        table.add_row("目標ウォーキング距離", f"{self.profile.target_distance_km} km")
        table.add_row("現在のレベル", f"Lv.{self.profile.current_level}")
        table.add_row("次レベルまで", f"{self.profile.next_level_steps:,} 歩")
        table.add_row("目標達成時の想定レベル", f"Lv.{self.profile.projected_level}")

        self.console.print(table)

        if self.profile.remaining_steps > 0:
            self.console.print(f"[bold yellow]✨ あと {self.profile.remaining_steps:,} 歩（約 {self.profile.target_distance_km} km）で目標達成！最高の一歩を！[/bold yellow]")
        else:
            self.console.print("[bold green]🎉 今日の目標達成済み！ナイスバイブス！[/bold green]")


if __name__ == "__main__":
    app = WalkingApp()
    app.run()