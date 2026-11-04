@echo off
chcp 65001 > nul
setlocal

REM スクリプト自身のディレクトリへ移動
cd /d "%~dp0"

set "VENV_DIR=.venv"
set "ACTIVATE_SCRIPT=%VENV_DIR%\Scripts\activate.bat"
set "INSTALLED_MARKER=%VENV_DIR%\.installed"

REM 1. Windows用仮想環境 (.venv\Scripts\activate.bat) が存在しない場合は作成
if not exist "%ACTIVATE_SCRIPT%" (
    echo [1/3] 仮想環境 ^(%VENV_DIR%^) を作成しています...
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [エラー] 仮想環境の作成に失敗しました。Pythonが正しくインストールされているか確認してください。
        pause
        exit /b 1
    )
)

REM 2. 仮想環境をアクティベート
call "%ACTIVATE_SCRIPT%"

REM 3. 初回のみ requirements.txt をインストール（2回目以降はスキップ）
if not exist "%INSTALLED_MARKER%" (
    echo [2/3] 依存パッケージをインストールしています ^(初回のみ^)...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [エラー] パッケージのインストールに失敗しました。
        pause
        exit /b 1
    )
    type nul > "%INSTALLED_MARKER%"
    echo インストールが完了しました。
) else (
    echo [2/3] パッケージはインストール済みのためスキップします。
)

REM 4. アプリケーションの起動
echo [3/3] アプリケーション ^(app.py^) を起動しています...
python app.py

endlocal

