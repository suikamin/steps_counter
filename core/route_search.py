# core/route_search.py
"""OSMnx・NetworkX・Foliumを用いた任意距離充足型の歩行経路探索モジュール。"""

import heapq
import math
import webbrowser
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import folium
import networkx as nx
import osmnx as ox

ROOT_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT_DIR / "cache"


class RouteOptimizer:
    """グラフネットワーク上の制約付き経路探索および地図生成を担当するサービスクラス。"""

    DEFAULT_BASE_LAT: float = 37.8694  # 新潟大学五十嵐キャンパス周辺
    DEFAULT_BASE_LNG: float = 138.9430
    DEFAULT_START_COORDS: Tuple[float, float] = (37.8703515, 138.9404929)
    DEFAULT_END_COORDS: Tuple[float, float] = (37.8617007, 138.9463893)
    DEFAULT_OUTPUT_HTML: str = str(ROOT_DIR / "route_map.html")

    # 稼働性の高いOverpassミラーを優先順に配置
    OVERPASS_ENDPOINTS: Tuple[str, ...] = (
        "https://overpass.kumi.systems/api",
        "https://lz4.overpass-api.de/api",
        "https://z.overpass-api.de/api",
        "https://overpass-api.de/api",
        "https://maps.mail.ru/osm/tools/overpass/api",
    )

    def __init__(
        self,
        base_lat: float = DEFAULT_BASE_LAT,
        base_lng: float = DEFAULT_BASE_LNG,
        start_coords: Tuple[float, float] = DEFAULT_START_COORDS,
        end_coords: Tuple[float, float] = DEFAULT_END_COORDS,
    ) -> None:
        self._base_lat = base_lat
        self._base_lng = base_lng
        self.start_coords = start_coords
        self.end_coords = end_coords

    @property
    def base_lat(self) -> float:
        """探索起点緯度を取得する。"""
        return self._base_lat

    @property
    def base_lng(self) -> float:
        """探索起点経度を取得する。"""
        return self._base_lng

    def haversine_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """2つの緯度経度間の大圏直線距離（メートル）を計算する。"""
        R = 6371000.0  # 地球の半径 (m)
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)

        a = (
            math.sin(dphi / 2.0) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
        )
        return 2.0 * R * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    def cross_product_2d(
        self,
        a: Tuple[float, float],
        b: Tuple[float, float],
        c: Tuple[float, float],
    ) -> float:
        """ベクトルABに対する点Cの2次元外積 (z成分) を計算する。

        > 0: 直線ABの左側, < 0: 直線ABの右側 (x=lon, y=lat として平面近似)
        """
        ab_x, ab_y = b[1] - a[1], b[0] - a[0]
        ac_x, ac_y = c[1] - a[1], c[0] - a[0]
        return ab_x * ac_y - ab_y * ac_x

    def dijkstra_with_cutoff(
        self,
        G: nx.MultiDiGraph,
        start_node: int,
        max_cost: float,
        reverse: bool = False,
    ) -> Tuple[Dict[int, float], Dict[int, Optional[int]]]:
        """指定上限距離 max_cost で枝刈りを行うダイクストラ法。

        reverse=True の場合、有向グラフの逆方向（終点へ向かう向き）を探索する。
        """
        dist: Dict[int, float] = {}
        parent: Dict[int, Optional[int]] = {}

        pq: List[Tuple[float, int]] = [(0.0, start_node)]
        dist[start_node] = 0.0
        parent[start_node] = None

        while pq:
            d, u = heapq.heappop(pq)
            if d > dist.get(u, float("inf")):
                continue
            if d > max_cost:
                continue

            edges = G.in_edges(u, data=True) if reverse else G.out_edges(u, data=True)

            for edge in edges:
                v = edge[0] if reverse else edge[1]
                weight = float(edge[2].get("length", 1.0))
                new_d = d + weight

                if new_d <= max_cost and new_d < dist.get(v, float("inf")):
                    dist[v] = new_d
                    parent[v] = u
                    heapq.heappush(pq, (new_d, v))

        return dist, parent

    def _resolve_endpoints(
        self,
        start_coords: Tuple[float, float],
        end_coords: Tuple[float, float],
        target_distance: float,
    ) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """目標距離が始点・終点の直線距離に対して短すぎる場合、終点座標を始点側へ補間調整する。"""
        d_ab = self.haversine_distance(
            start_coords[0], start_coords[1], end_coords[0], end_coords[1]
        )
        if d_ab <= 0:
            return start_coords, (start_coords[0] - 0.001, start_coords[1] + 0.001)

        if target_distance < d_ab * 1.15:
            ratio = max(0.1, (target_distance * 0.45) / d_ab)
            adj_lat = start_coords[0] + (end_coords[0] - start_coords[0]) * ratio
            adj_lon = start_coords[1] + (end_coords[1] - start_coords[1]) * ratio
            return start_coords, (adj_lat, adj_lon)

        return start_coords, end_coords

    def _fetch_walk_graph(
        self, center_lat: float, center_lon: float, search_radius: float
    ) -> nx.MultiDiGraph:
        """OSMnx v1/v2 両対応の設定および複数Overpassミラーのフォールバック付きで道路網グラフを取得する。"""
        user_agent = "MyWalkingRouteApp/1.0 (contact: xah2677@yahoo.co.jp)"

        if hasattr(ox.settings, "http_user_agent"):
            ox.settings.http_user_agent = user_agent
        if hasattr(ox.settings, "user_agent"):
            ox.settings.user_agent = user_agent

        if hasattr(ox.settings, "requests_timeout"):
            ox.settings.requests_timeout = 60
        if hasattr(ox.settings, "timeout"):
            ox.settings.timeout = 60

        # /api/status 接続拒否時に 60秒間スリープするのを防止し、即座に別ミラーへ切り替える
        if hasattr(ox.settings, "overpass_rate_limit"):
            ox.settings.overpass_rate_limit = False

        ox.settings.use_cache = True
        ox.settings.cache_folder = str(CACHE_DIR)
        ox.settings.log_console = True

        last_err: Optional[Exception] = None
        for endpoint in self.OVERPASS_ENDPOINTS:
            try:
                if hasattr(ox.settings, "overpass_url"):
                    ox.settings.overpass_url = endpoint
                elif hasattr(ox.settings, "overpass_endpoint"):
                    ox.settings.overpass_endpoint = endpoint

                return ox.graph_from_point(
                    (center_lat, center_lon),
                    dist=search_radius,
                    network_type="walk",
                )
            except Exception as e:
                print(f"[WARN] Overpass エンドポイント ({endpoint}) での取得失敗: {e}")
                last_err = e

        raise RuntimeError(
            f"OpenStreetMap (Overpass API) から道路網データを取得できませんでした: {last_err}"
        )

    def generate_target_route_map(
        self,
        start_coords: Optional[Tuple[float, float]] = None,
        end_coords: Optional[Tuple[float, float]] = None,
        target_distance: float = 3000.0,
        side: str = "left",
        output_html: str = DEFAULT_OUTPUT_HTML,
    ) -> Dict[str, Any]:
        """目標距離(m)を満たす最適経由点 C* を探索し、Folium HTML地図を生成する。"""
        s_coords = start_coords or self.start_coords
        e_coords = end_coords or self.end_coords
        target_distance = max(200.0, float(target_distance))

        s_coords, e_coords = self._resolve_endpoints(s_coords, e_coords, target_distance)
        d_AB = self.haversine_distance(
            s_coords[0], s_coords[1], e_coords[0], e_coords[1]
        )

        # 楕円探索エリアを含む道路網を OpenStreetMap から取得
        center_lat = (s_coords[0] + e_coords[0]) / 2.0
        center_lon = (s_coords[1] + e_coords[1]) / 2.0
        search_radius = min(2500.0, max(600.0, (target_distance / 2.0) * 1.15))

        print(f"[1/4] 道路網グラフを取得中 (半径約 {search_radius:.0f}m)...")
        G = self._fetch_walk_graph(center_lat, center_lon, search_radius)

        # 最近傍ノードの特定 (scikit-learn BallTree 使用)
        start_node = ox.distance.nearest_nodes(G, X=s_coords[1], Y=s_coords[0])
        end_node = ox.distance.nearest_nodes(G, X=e_coords[1], Y=e_coords[0])

        print("[2/4] A/Bからのダイクストラ探索を実行中 (上限枝刈り付き)...")
        cutoff = target_distance * 1.25
        dist_A, parent_A = self.dijkstra_with_cutoff(
            G, start_node, max_cost=cutoff, reverse=False
        )
        dist_B, parent_B = self.dijkstra_with_cutoff(
            G, end_node, max_cost=cutoff, reverse=True
        )

        print("[3/4] 楕円帯域から最適経由地 C* を選定中...")
        min_geom_sum = max(d_AB, (target_distance / 1.3) * 0.75)
        max_geom_sum = target_distance

        best_c: Optional[int] = None
        min_diff = float("inf")
        best_actual_dist = 0.0

        # 第1パス: 幾何半楕円帯域 + 左右片側フィルタリング
        for node in G.nodes():
            if node in (start_node, end_node):
                continue
            if node not in dist_A or node not in dist_B:
                continue

            node_lat = G.nodes[node]["y"]
            node_lon = G.nodes[node]["x"]

            cp = self.cross_product_2d(s_coords, e_coords, (node_lat, node_lon))
            if side == "left" and cp <= 0:
                continue
            if side == "right" and cp >= 0:
                continue

            d1 = self.haversine_distance(s_coords[0], s_coords[1], node_lat, node_lon)
            d2 = self.haversine_distance(node_lat, node_lon, e_coords[0], e_coords[1])
            geom_sum = d1 + d2

            if min_geom_sum <= geom_sum <= max_geom_sum:
                actual_dist = dist_A[node] + dist_B[node]
                diff = abs(actual_dist - target_distance)
                if diff < min_diff:
                    min_diff = diff
                    best_c = node
                    best_actual_dist = actual_dist

        # 第2パス (フォールバック): 狭義の楕円帯域内に候補がない場合は到達可能ノード全体から最良点を選択
        if best_c is None:
            for node in G.nodes():
                if node in (start_node, end_node):
                    continue
                if node not in dist_A or node not in dist_B:
                    continue
                actual_dist = dist_A[node] + dist_B[node]
                diff = abs(actual_dist - target_distance)
                if diff < min_diff:
                    min_diff = diff
                    best_c = node
                    best_actual_dist = actual_dist

        if best_c is None:
            raise RuntimeError("条件を満たす経由地ノードが見つかりませんでした。")

        # 最短経路の復元 (A -> C* -> B)
        path_AC: List[int] = []
        curr: Optional[int] = best_c
        while curr is not None:
            path_AC.append(curr)
            curr = parent_A.get(curr)
        path_AC.reverse()

        path_CB: List[int] = []
        curr = parent_B.get(best_c)
        while curr is not None:
            path_CB.append(curr)
            curr = parent_B.get(curr)

        full_node_path = path_AC + path_CB
        route_coords: List[Tuple[float, float]] = [
            (G.nodes[n]["y"], G.nodes[n]["x"]) for n in full_node_path
        ]
        c_coords = (G.nodes[best_c]["y"], G.nodes[best_c]["x"])

        print(f"[4/4] Folium HTML マップを作成中 ({output_html})...")
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=14,
            tiles="https://cyberjapandata.gsi.go.jp/xyz/std/{z}/{x}/{y}.png",
            attr='&copy; <a href="https://maps.gsi.go.jp/development/ichiran.html">国土地理院</a>',
        )

        folium.PolyLine(
            route_coords,
            color="#2b7bba",
            weight=5,
            opacity=0.85,
            tooltip=f"実走距離: {best_actual_dist:.0f}m (目標: {target_distance:.0f}m)",
        ).add_to(m)

        folium.PolyLine(
            [s_coords, e_coords],
            color="#888888",
            weight=2,
            dash_array="5, 10",
            tooltip="直線 AB (基準線)",
        ).add_to(m)

        folium.Marker(
            s_coords,
            popup="始点 A",
            icon=folium.Icon(color="green", icon="play"),
        ).add_to(m)
        folium.Marker(
            e_coords,
            popup="終点 B",
            icon=folium.Icon(color="red", icon="flag"),
        ).add_to(m)
        folium.Marker(
            c_coords,
            popup=f"選定経由地 C* (実走和: {best_actual_dist:.0f}m / 誤差: {min_diff:.0f}m)",
            icon=folium.Icon(color="blue", icon="info-sign"),
        ).add_to(m)

        output_path = Path(output_html).resolve()
        m.save(str(output_path))
        print(f"完了しました！ {output_path} をブラウザで開いて確認できます。")
        print(
            f"  - 目標距離: {target_distance:.1f} m / 実走距離: "
            f"{best_actual_dist:.1f} m (誤差: {min_diff:.1f} m)"
        )

        return {
            "output_html": str(output_path),
            "target_distance_m": target_distance,
            "actual_distance_m": best_actual_dist,
            "diff_m": min_diff,
            "route_coords": route_coords,
            "waypoint_coords": c_coords,
        }

    def search_and_generate_map(
        self,
        target_distance_km: float,
        start_coords: Optional[Tuple[float, float]] = None,
        end_coords: Optional[Tuple[float, float]] = None,
        side: str = "left",
        output_html: str = DEFAULT_OUTPUT_HTML,
        open_browser: bool = True,
    ) -> Dict[str, Any]:
        """目標距離 (km) と開始・終了座標から経路探索・地図HTML出力を行い、ブラウザで自動的に開く。"""
        if start_coords is not None:
            self.start_coords = start_coords
        if end_coords is not None:
            self.end_coords = end_coords

        target_distance_m = max(200.0, float(target_distance_km) * 1000.0)
        result = self.generate_target_route_map(
            start_coords=self.start_coords,
            end_coords=self.end_coords,
            target_distance=target_distance_m,
            side=side,
            output_html=output_html,
        )
        if open_browser:
            html_uri = Path(result["output_html"]).resolve().as_uri()
            webbrowser.open(html_uri)
        return result
