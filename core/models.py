# core/models.py
"""ユーザーの歩行データおよびゲーミフィケーションステータスを管理するモデルモジュール。"""


class UserProfile:
    """ユーザーの身長・歩数・目標値から歩幅・不足距離・レベル等を算出するモデルクラス。"""

    DEFAULT_HEIGHT: float = 170.0
    DEFAULT_TARGET_STEPS: int = 8000
    LEVEL_STEP_UNIT: int = 8000
    MAX_LEVEL: int = 10
    STRIDE_FACTOR: float = 0.45

    def __init__(
        self,
        height: float = DEFAULT_HEIGHT,
        current_steps: int = 0,
        target_steps: int = DEFAULT_TARGET_STEPS,
    ) -> None:
        self.height = height
        self.target_steps = target_steps
        self.current_steps = current_steps

    # --- Getter / Setter (バリデーション付きカプセル化) ---
    @property
    def height(self) -> float:
        """身長 (cm) を取得する。"""
        return self._height

    @height.setter
    def height(self, value: float | int) -> None:
        """身長 (cm) を設定する（正の数値のみ許容）。"""
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("身長は数値である必要があります。")
        if value <= 0:
            raise ValueError("身長は正の値を指定してください。")
        self._height = float(value)

    @property
    def current_steps(self) -> int:
        """現在の歩数を取得する。"""
        return self._current_steps

    @current_steps.setter
    def current_steps(self, value: int) -> None:
        """現在の歩数を設定する（0以上の整数のみ許容）。"""
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError("歩数は整数である必要があります。")
        if value < 0:
            raise ValueError("歩数に負の値を設定することはできません。")
        self._current_steps = value

    @property
    def target_steps(self) -> int:
        """1日の目標歩数を取得する。"""
        return self._target_steps

    @target_steps.setter
    def target_steps(self, value: int) -> None:
        """1日の目標歩数を設定する（正の整数のみ許容）。"""
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError("目標歩数は整数である必要があります。")
        if value <= 0:
            raise ValueError("目標歩数は正の整数を指定してください。")
        self._target_steps = value

    # --- 計算プロパティ（読み取り専用） ---
    @property
    def stride_m(self) -> float:
        """身長から推定される1歩あたりの歩幅 (m)。"""
        return (self._height * self.STRIDE_FACTOR) / 100.0

    @property
    def remaining_steps(self) -> int:
        """目標達成までに不足している歩数。"""
        return max(0, self._target_steps - self._current_steps)

    @property
    def over_steps(self) -> int:
        """目標歩数を超過して達成した歩数。"""
        return max(0, self._current_steps - self._target_steps)

    @property
    def target_distance_km(self) -> float:
        """不足歩数から逆算した目標歩行距離 (km)。"""
        return round((self.remaining_steps * self.stride_m) / 1000.0, 2)

    @property
    def target_distance_m(self) -> float:
        """不足歩数から逆算した目標歩行距離 (m)。"""
        return round(self.remaining_steps * self.stride_m, 1)

    @property
    def current_level(self) -> int:
        """現在の歩数に応じたアバターレベル (1〜MAX_LEVEL)。"""
        return min(self.MAX_LEVEL, (self._current_steps // self.LEVEL_STEP_UNIT) + 1)

    @property
    def next_level_steps(self) -> int:
        """次のレベルに到達するまでに必要な残り歩数。"""
        if self.current_level >= self.MAX_LEVEL:
            return 0
        return self.LEVEL_STEP_UNIT - (self._current_steps % self.LEVEL_STEP_UNIT)

    @property
    def projected_level(self) -> int:
        """本日の目標達成時に到達する想定レベル。"""
        projected_steps = self._current_steps + self.remaining_steps
        return min(self.MAX_LEVEL, (projected_steps // self.LEVEL_STEP_UNIT) + 1)
