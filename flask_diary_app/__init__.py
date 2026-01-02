import os
from flask import Flask

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # instance_path 確保
    os.makedirs(app.instance_path, exist_ok=True)

    # データベース
    app.config["DATABASE"] = os.path.join(
        app.instance_path, "diary.db"
    )
    # 画像アップロードフォルダ
    app.config["UPLOAD_FOLDER"] = os.path.join(
        app.root_path, "static", "uploads"
    )
    # 一時フォルダ（インポート/エクスポート処理時に使用する）
    app.config["TMP_FOLDER"] = os.path.join(
        app.instance_path, "tmp"
    )

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["TMP_FOLDER"], exist_ok=True)

    # blueprint(アプリを分割して管理するためのもの)
    from .blueprints.diary import diary_bp
    app.register_blueprint(diary_bp)

    with app.app_context(): #今からこの app を使って処理をするという宣言
        from .db import init_db #循環 import を防ぐためcreate_app内で読み込む
        #DB（なければ）作成
        init_db()

    app.secret_key = "secret-key"

    return app

app = create_app()