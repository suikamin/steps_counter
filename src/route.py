class RouteOptimizer:
    """
    グラフネットワーク上の制約付き経路探索を担当するサービスクラス
    """
    def __init__(self, base_lat: float, base_lng: float):
        self._base_lat = base_lat
        self._base_lng = base_lng

    def search_constrained_route(self, target_distance_km: float) -> list[tuple[float, float]]:
        """
        目標距離を満たす周回経路を生成（本番ではOSMnx/NetworkXの探索をここに記述）
        """
        return []