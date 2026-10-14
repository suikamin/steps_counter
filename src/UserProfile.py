# UserProfile.py
import math

class UserProfile:
    """
    ユーザーの歩行データおよびゲーミフィケーションステータスを管理するモデルクラス
    """
    
    LEVEL_STEP_UNIT = 8000  # レベルアップに必要な歩数単位

    def __init__(self, height: int = 170, current_steps: int = 0):
        self._height = height
        self._target_steps = 8000
        self.current_steps = current_steps

    # --- current_steps の Getter / Setter ---
    @property
    def current_steps(self) -> int:
        """現在の歩数を取得"""
        return self._current_steps

    @property
    def height(self) -> int:
        """身長を取得"""
        return self._height

    @current_steps.setter
    def current_steps(self, value: int):
        """現在の歩数を設定（負の値は不可）"""
        if not isinstance(value, int):
            raise TypeError("歩数は整数である必要があります。")
        if value < 0:
            raise ValueError("歩数に負の値を設定することはできません。")
        self._current_steps = value

    # --- target_steps の Getter / Setter ---
    @property
    def target_steps(self) -> int:
        """目標歩数を取得"""
        return self._target_steps


    # --- 計算プロパティ（読み取り専用） ---
    @property
    def remaining_steps(self) -> int:
        """目標達成までに不足している歩数"""
        return max(0, self._target_steps - self._current_steps)

    @property
    def target_distance_km(self) -> float:
        """不足歩数から逆算した目標距離 (km)"""
        stride_m = (self.height * 0.45) / 100.0
        return round((self.remaining_steps * stride_m) / 1000.0, 2)

    @property
    def current_level(self) -> int:
        """現在のプレイヤーレベル"""
        return (self._current_steps // self.LEVEL_STEP_UNIT) + 1

    @property
    def next_level_steps(self) -> int:
        """次レベル到達までに必要な歩数"""
        return self.LEVEL_STEP_UNIT - (self._current_steps % self.LEVEL_STEP_UNIT)

    @property
    def projected_level(self) -> int:
        """目標達成時の想定プレイヤーレベル"""
        return ((self._current_steps + self.remaining_steps) // self.LEVEL_STEP_UNIT) + 1
