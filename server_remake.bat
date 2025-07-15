@echo off
cd /d %~dp0

:: 1. 既存のapp.dbを削除（あれば）
if exist app.db (
    echo Deleting old app.db...
    del app.db
)

:: 2. データベース初期化スクリプトを実行
echo Initializing database...
python init_db.py
