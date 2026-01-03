#DB関連処理
import sqlite3

from flask import current_app


# アプリ起動時にDBがなければ作成する
def init_db():
    db = sqlite3.connect(current_app.config["DATABASE"])
    table = db.cursor()
    table.execute('''
        CREATE TABLE IF NOT EXISTS diaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            create_date TEXT,
            updata_date TEXT,
            title TEXT,
            content TEXT,
            image TEXT
        )
    ''')
    db.commit()
    db.close()

#DB接続
def get_db():
    db = sqlite3.connect(current_app.config["DATABASE"])
    db.row_factory = sqlite3.Row #カラム名でアクセスできるようになる
    return db