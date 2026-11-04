# app.py
"""ウォーキング支援＆アバター育成アプリケーションのエントリーポイント。"""

import sys
import tkinter as tk
from pathlib import Path

# プロジェクトのルートフォルダをPythonのモジュール検索パスの先頭に追加
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ui.main_window import WalkingAppGUIPreview


def main() -> None:
    """Tkinterルートウィンドウを生成し、アプリケーションを起動する。"""
    root = tk.Tk()
    WalkingAppGUIPreview(root)
    root.mainloop()


if __name__ == "__main__":
    main()



if __name__ == "__main__":
    main()