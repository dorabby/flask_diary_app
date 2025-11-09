from flask import Flask,render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app=Flask(__name__)
DATABASE = "flask_diary_app/diary.db"

# --- データベース初期化 ---
def init_db():
    db = sqlite3.connect(DATABASE)
    table = db.cursor()
    table.execute('''
        CREATE TABLE IF NOT EXISTS diaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            create_date TEXT,
            updata_date TEXT,
            title TEXT,
            content TEXT
        )
    ''')
    db.commit()
    db.close()

init_db()  # アプリ起動時にDBがなければ作成する

# 仮データ（日記リスト）
diaries = [
    {"id": 1, "date": "11月1日", "title": "秋の散歩", "content": "公園を歩いた。紅葉が綺麗だった。"},
    {"id": 2, "date": "11月2日", "title": "本を読んだ", "content": "『ノルウェイの森』を読んだ。"},
    {"id": 3, "date": "11月3日", "title": "カレー作り", "content": "スパイスカレーに挑戦。うまくできた！"}
]

@app.route("/")
def index():
    db = sqlite3.connect(DATABASE)
    data = db.cursor()
    data.execute("SELECT id, create_date, updata_date, title FROM diaries ORDER BY id DESC")
    diaries = data.fetchall()
    db.close()
    return render_template("index.html", diaries=diaries)

@app.route("/new", methods=["GET", "POST"])
def new_diary():
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        date = datetime.now().strftime("%m月%d日")
        db = sqlite3.connect(DATABASE)
        data = db.cursor()
        data.execute("INSERT INTO diaries (create_date, updata_date, title, content) VALUES (?, ?, ?, ?)",
                  (date, date, title, content))
        db.commit()
        db.close()
        return redirect(url_for("index"))
    return render_template("new.html")

@app.route("/diary/<int:diary_id>")
def diary_detail(diary_id):
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    data = db.cursor()
    data.execute("SELECT id, create_date, updata_date, title, content FROM diaries WHERE id = ?", (diary_id,))
    diary = data.fetchone()
    db.close()
    print(diary)
    return render_template("detail.html", diary=diary)

@app.route("/edit/<int:diary_id>", methods=["GET", "POST"])
def edit_diary(diary_id):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        date = datetime.now().strftime("%m月%d日")

        c.execute("UPDATE diaries SET title = ?, content = ?, updata_date=? WHERE id = ?", 
                  (title, content, date, diary_id))
        conn.commit()
        conn.close()

        return redirect(url_for("diary_detail", diary_id=diary_id))

    # GET（編集画面表示）
    c.execute("SELECT * FROM diaries WHERE id = ?", (diary_id,))
    diary = c.fetchone()
    conn.close()
    return render_template("edit.html", diary=diary)

@app.route("/delete/<int:diary_id>", methods=["POST"])
def delete_diary(diary_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("DELETE FROM diaries WHERE id = ?", (diary_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))