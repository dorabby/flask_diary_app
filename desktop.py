import threading
import webview

from flask_diary_app import create_app

def run_flask():
    app = create_app()
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False
    )

if __name__ == "__main__":
    # Flask を別スレッドで起動
    threading.Thread(target=run_flask, daemon=True).start()

    # デスクトップウィンドウ起動
    webview.create_window(
        title="日記アプリ",
        url="http://127.0.0.1:5000",
        width=900,
        height=700,
        min_size=(800, 600),
        resizable=True
    )
    webview.start()
