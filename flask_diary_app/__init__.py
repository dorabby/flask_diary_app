import os
import uuid
from flask import Flask,render_template, request, redirect, url_for, send_from_directory
import sqlite3
from datetime import datetime
from werkzeug.utils import secure_filename


app=Flask(__name__)
DATABASE = "flask_diary_app/diary.db"

app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
            content TEXT,
            image TEXT
        )
    ''')
    db.commit()
    db.close()

init_db()  # アプリ起動時にDBがなければ作成する

@app.route("/")
def index():
    db = sqlite3.connect(DATABASE)
    data = db.cursor()
    data.execute("SELECT id, create_date, updata_date, title, image FROM diaries ORDER BY id DESC")
    diaries = data.fetchall()
    db.close()
    return render_template("index.html", diaries=diaries)

@app.route("/new", methods=["GET", "POST"])
def new_diary():
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        image_file = request.files.get("image")
        if image_file and allowed_file(image_file.filename):
            filename = save_image(image_file)

        date = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        db = sqlite3.connect(DATABASE)
        data = db.cursor()
        data.execute("INSERT INTO diaries (create_date, updata_date, title, content, image) VALUES (?, ?, ?, ?, ?)",
                  (date, date, title, content, filename))
        db.commit()
        db.close()
        return redirect(url_for("index"))
    return render_template("new.html")

@app.route("/diary/<int:diary_id>")
def diary_detail(diary_id):
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    data = db.cursor()
    data.execute("SELECT id, create_date, updata_date, title, content, image FROM diaries WHERE id = ?", (diary_id,))
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
        image_file = request.files.get("image")
        delete_image = request.form.get("delete_image")
        # 画像を取得
        c.execute("SELECT image FROM diaries WHERE id = ?", (diary_id,))
        existing = c.fetchone()
        image_filename = existing["image"]
        # 画像削除チェックがあれば削除
        if delete_image and image_filename:
            del_image(image_filename)
            filename = None
            
        elif image_file and allowed_file(image_file.filename):
            # 古い画像を削除
            if image_filename:
                del_image(image_filename)
            # 新しい画像を保存
            filename = save_image(image_file)

        date = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

        c.execute("UPDATE diaries SET title = ?, content = ?, updata_date=?, image=? WHERE id = ?", 
                  (title, content, date, filename, diary_id))
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

def save_image(image_file):
    ext = image_file.filename.rsplit('.', 1)[1]
    filename = f"{uuid.uuid4()}.{ext}"
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    image_file.save(image_path)
    return filename

def del_image(image_filename):
    old_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
    if os.path.exists(old_path):
        os.remove(old_path)