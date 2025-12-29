import os
import uuid
from flask import Flask,render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime
from werkzeug.utils import secure_filename


app=Flask(__name__)
DATABASE = "flask_diary_app/diary.db"
app.secret_key = "secret-key"

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

# 一覧表示
@app.route("/")
def index():
    #検索ワードと検索対象とソート
    keyword = request.args.get("search", "").strip()
    scope = request.args.get("scope", "title")
    sort = request.args.get("sort", "new")
    preserve = request.args.get("preserve", "")

    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row #カラム名でアクセスできるようになる
    c = db.cursor()

    sql = """SELECT id, create_date, title, content, image FROM diaries"""
    
    #検索キーワードが入力されていれば条件追加する
    params = []
    if keyword:
        if scope == "all":
            sql += " WHERE title LIKE ? OR content LIKE ?"
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        else:
            sql += " WHERE title LIKE ?"
            params.append(f"%{keyword}%")
    #ソート設定
    order_map = {
        "new": "create_date DESC",
        "old": "create_date ASC",
        "title": "title COLLATE NOCASE ASC"
    }
    order_by = order_map.get(sort, "create_date DESC")

    sql += f" ORDER BY {order_by}"
    c.execute(sql, params)
    diaries = c.fetchall()
    db.close()

    diary_list = []
    for d in diaries:
        #本文を30文字までプレビュー表示
        normalized = " ".join(d["content"].split())
        preview = normalized[:30]
        if len(normalized) > 30:
            preview += "…"

        diary_list.append({
            "id": d["id"],
            "title": d["title"],
            "preview": preview,
            "image": d["image"],
            "create_date": d["create_date"]
        })
    return render_template("index.html", diaries=diary_list, sort=sort, preserve=preserve)

# テーマ切り替え
@app.route("/toggle_theme")
def toggle_theme():
    session["theme"] = "dark" if session.get("theme") == "light" else "light"
    return redirect(request.referrer or url_for("index"))

# 新規登録
@app.route("/new", methods=["GET", "POST"])
def new_diary():
    if request.method == "POST":
        #バリデーションチェック
        errors, data = validation_content(request.form)
        if errors:
            return render_template("new.html", errors=errors,
                title=data["title"],content=data["content"])
        filename = None
        image_file = request.files.get("image")
        if image_file and allowed_file(image_file.filename):
            filename = save_image(image_file)

        date = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        db = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
        c = db.cursor()
        c.execute("INSERT INTO diaries (create_date, updata_date, title, content, image) VALUES (?, ?, ?, ?, ?)",
                  (date, date, data["title"], data["content"], filename))
        db.commit()
        db.close()
        return redirect(url_for("index"))
    return render_template("new.html", errors={})

# 詳細取得
@app.route("/diary/<int:diary_id>")
def diary_detail(diary_id):
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    c = db.cursor()
    c.execute("SELECT id, create_date, updata_date, title, content, image FROM diaries WHERE id = ?", (diary_id,))
    diary = c.fetchone()
    db.close()
    return render_template("detail.html", diary=diary)

# 編集
@app.route("/edit/<int:diary_id>", methods=["GET", "POST"])
def edit_diary(diary_id):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # データ取得
    c.execute("SELECT * FROM diaries WHERE id = ?", (diary_id,))
    diary = c.fetchone()

    if request.method == "POST":
        errors, data = validation_content(request.form)
        image_file = request.files.get("image")
        delete_image = request.form.get("delete_image")
        # 画像を取得
        c.execute("SELECT image FROM diaries WHERE id = ?", (diary_id,))
        existing = c.fetchone()
        filename = existing["image"]
        if errors:
            conn.close()
            return render_template(
                "edit.html",
                errors=errors,
                title=data["title"],
                content=data["content"],
                image=filename,
                diary_id=diary_id
            )
        # 画像削除チェックがあれば削除
        if delete_image and filename:
            del_image(filename)
            filename = None
            
        elif image_file and allowed_file(image_file.filename):
            # 古い画像を削除
            if filename:
                del_image(filename)
            # 新しい画像を保存
            filename = save_image(image_file)

        date = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

        c.execute("UPDATE diaries SET title = ?, content = ?, updata_date=?, image=? WHERE id = ?", 
                  (data["title"], data["content"], date, filename, diary_id))
        conn.commit()
        conn.close()

        return redirect(url_for("diary_detail", diary_id=diary_id))


    conn.close()
    return render_template(
        "edit.html",
        errors={},
        title=diary["title"],
        content=diary["content"],
        image=diary["image"],
        diary_id=diary_id
    )

# 削除
@app.route("/delete/<int:diary_id>", methods=["POST"])
def delete_diary(diary_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("DELETE FROM diaries WHERE id = ?", (diary_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

# 画像登録処理
def save_image(image_file):
    ext = image_file.filename.rsplit('.', 1)[1]
    filename = f"{uuid.uuid4()}.{ext}"
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    image_file.save(image_path)
    return filename

# 画像削除
def del_image(image_filename):
    old_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
    if os.path.exists(old_path):
        os.remove(old_path)

# バリデーションチェック
def validation_content(request):
    errors = {}

    title = request["title"].strip()
    content = request["content"].strip()

    if not title:
        errors["title"] = "必須項目です。"
    elif len(title) > 20:
        errors["title"] = "20文字以内で入力してください。"

    if not content:
        errors["content"] = "必須項目です。"

    return errors, {
        "title": title,
        "content": content
    }

