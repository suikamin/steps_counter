# core/avatar.py
"""レベル（Lv.1〜Lv.10）に応じた植物育成アバター画像を生成・取得するモジュール。"""

import math
from pathlib import Path
from typing import Dict, Optional, Tuple
from PIL import Image, ImageDraw

ROOT_DIR = Path(__file__).resolve().parent.parent
AVATAR_DIR = ROOT_DIR / "public"


def draw_seed_base(draw: ImageDraw.ImageDraw, cx: int, cy: int, angle: int = 25) -> None:
    """共通のベースとなる『種』を描画する。"""
    SEED_OUTLINE = (141, 110, 99, 255)
    SEED_BODY = (188, 170, 164, 255)
    SEED_SHADOW = (161, 136, 127, 255)

    draw.ellipse((cx - 55, cy + 10, cx + 55, cy + 70), fill=SEED_SHADOW)
    draw.ellipse((cx - 50, cy, cx + 50, cy + 60), fill=SEED_BODY, outline=SEED_OUTLINE, width=3)
    draw.arc((cx - 40, cy + 10, cx + 40, cy + 50), start=200, end=340, fill=SEED_OUTLINE, width=3)


def create_avatar_image(level: int, output_size: Tuple[int, int] = (200, 200)) -> Image.Image:
    """指定レベル (1〜10) のアバター画像をPIL Imageとして動的生成する。"""
    level = max(1, min(10, int(level)))

    GREEN_STEM = (76, 175, 80, 255)
    GREEN_LEAF_LIGHT = (129, 199, 132, 255)
    GREEN_LEAF_DARK = (56, 142, 60, 255)
    FLOWER_ORANGE = (255, 152, 0, 255)
    FLOWER_YELLOW = (255, 235, 59, 255)

    base_size = (400, 400)
    img = Image.new("RGBA", base_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = base_size[0] // 2, base_size[1] // 2 + 60

    # 土のベース
    draw.ellipse((cx - 130, cy + 35, cx + 130, cy + 110), fill=(141, 110, 99, 255))
    draw.ellipse((cx - 110, cy + 25, cx + 110, cy + 95), fill=(161, 136, 127, 255))

    # 種のベース描画
    draw_seed_base(draw, cx, cy)

    # レベルに応じた植物の成長描画
    if level == 1:
        pass  # 種のみ
    elif level == 2:
        draw.line([(cx - 15, cy + 25), (cx + 15, cy + 15)], fill=GREEN_STEM, width=6)
    elif level == 3:
        draw.line([(cx, cy + 20), (cx, cy - 15)], fill=GREEN_STEM, width=8)
        draw.ellipse((cx - 6, cy - 30, cx + 6, cy - 10), fill=GREEN_LEAF_LIGHT)
    elif level == 4:
        draw.line([(cx, cy + 20), (cx, cy - 40)], fill=GREEN_STEM, width=10)
        draw.ellipse((cx - 12, cy - 55, cx + 12, cy - 25), fill=GREEN_LEAF_LIGHT)
    elif level == 5:
        draw.line([(cx, cy + 20), (cx, cy - 45)], fill=GREEN_STEM, width=10)
        draw.ellipse((cx - 40, cy - 70, cx, cy - 30), fill=GREEN_LEAF_LIGHT)
        draw.ellipse((cx, cy - 70, cx + 40, cy - 30), fill=GREEN_LEAF_DARK)
    elif level == 6:
        draw.line([(cx, cy + 20), (cx, cy - 90)], fill=GREEN_STEM, width=12)
        draw.ellipse((cx - 50, cy - 115, cx, cy - 75), fill=GREEN_LEAF_LIGHT)
        draw.ellipse((cx, cy - 115, cx + 50, cy - 75), fill=GREEN_LEAF_DARK)
    elif level == 7:
        draw.line([(cx, cy + 20), (cx, cy - 120)], fill=GREEN_STEM, width=12)
        draw.ellipse((cx - 55, cy - 75, cx - 5, cy - 45), fill=GREEN_LEAF_DARK)
        draw.ellipse((cx + 5, cy - 75, cx + 55, cy - 45), fill=GREEN_LEAF_LIGHT)
        draw.ellipse((cx - 45, cy - 140, cx, cy - 105), fill=GREEN_LEAF_LIGHT)
        draw.ellipse((cx, cy - 140, cx + 45, cy - 105), fill=GREEN_LEAF_DARK)
    elif level == 8:
        draw.line([(cx, cy + 20), (cx, cy - 150)], fill=GREEN_STEM, width=14)
        draw.ellipse((cx - 65, cy - 90, cx - 5, cy - 55), fill=GREEN_LEAF_DARK)
        draw.ellipse((cx + 5, cy - 90, cx + 65, cy - 55), fill=GREEN_LEAF_LIGHT)
        draw.ellipse((cx - 55, cy - 150, cx - 5, cy - 115), fill=GREEN_LEAF_LIGHT)
        draw.ellipse((cx + 5, cy - 150, cx + 55, cy - 115), fill=GREEN_LEAF_DARK)
    elif level == 9:
        draw.line([(cx, cy + 20), (cx, cy - 160)], fill=GREEN_STEM, width=14)
        draw.ellipse((cx - 65, cy - 90, cx - 5, cy - 55), fill=GREEN_LEAF_DARK)
        draw.ellipse((cx + 5, cy - 90, cx + 65, cy - 55), fill=GREEN_LEAF_LIGHT)
        draw.ellipse((cx - 55, cy - 150, cx - 5, cy - 115), fill=GREEN_LEAF_LIGHT)
        draw.ellipse((cx + 5, cy - 150, cx + 55, cy - 115), fill=GREEN_LEAF_DARK)
        draw.ellipse((cx - 20, cy - 195, cx + 20, cy - 155), fill=FLOWER_ORANGE)
    elif level == 10:
        draw.line([(cx, cy + 20), (cx, cy - 160)], fill=GREEN_STEM, width=14)
        draw.ellipse((cx - 65, cy - 90, cx - 5, cy - 55), fill=GREEN_LEAF_DARK)
        draw.ellipse((cx + 5, cy - 90, cx + 65, cy - 55), fill=GREEN_LEAF_LIGHT)
        draw.ellipse((cx - 55, cy - 150, cx - 5, cy - 115), fill=GREEN_LEAF_LIGHT)
        draw.ellipse((cx + 5, cy - 150, cx + 55, cy - 115), fill=GREEN_LEAF_DARK)
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            px = cx + int(35 * math.cos(rad))
            py = (cy - 175) + int(35 * math.sin(rad))
            draw.ellipse((px - 18, py - 18, px + 18, py + 18), fill=FLOWER_ORANGE)
        draw.ellipse((cx - 22, cy - 197, cx + 22, cy - 153), fill=FLOWER_YELLOW)

    return img.resize(output_size, Image.Resampling.LANCZOS)


def generate_10_growth_stages(output_dir: Optional[Path] = None) -> Dict[int, Path]:
    """Lv.1〜Lv.10のアバターPNG画像を生成して指定ディレクトリへ保存する。"""
    target_dir = Path(output_dir) if output_dir is not None else AVATAR_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    saved_paths: Dict[int, Path] = {}
    for level in range(1, 11):
        img_final = create_avatar_image(level, output_size=(200, 200))
        out_path = target_dir / f"avatar_lv{level}.png"
        img_final.save(out_path, "PNG")
        saved_paths[level] = out_path

        if level == 1:
            img_final.save(target_dir / "avatar.png", "PNG")

    return saved_paths


def get_avatar_image(
    level: int = 1,
    size: Tuple[int, int] = (170, 170),
    output_dir: Optional[Path] = None,
) -> Image.Image:
    """指定レベルのアバター画像を取得する（未生成の場合は自動生成・キャッシュする）。"""
    level = max(1, min(10, int(level)))
    target_dir = Path(output_dir) if output_dir is not None else AVATAR_DIR
    img_path = target_dir / f"avatar_lv{level}.png"

    if img_path.exists():
        try:
            with Image.open(img_path) as img:
                return img.convert("RGBA").resize(size, Image.Resampling.LANCZOS)
        except Exception:
            pass

    # 画像ファイルが存在しない場合は自動生成して保存を試みる
    try:
        generate_10_growth_stages(target_dir)
    except Exception:
        pass

    return create_avatar_image(level, output_size=size)


if __name__ == "__main__":
    paths = generate_10_growth_stages()
    for lv, p in paths.items():
        print(f"✨ 生成完了 (Lv.{lv}): {p}")
