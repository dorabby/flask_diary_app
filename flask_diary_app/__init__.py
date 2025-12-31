import os
import uuid
from flask import Flask, abort, flash,render_template, request, redirect, url_for, session, send_file, after_this_request
import sqlite3
from datetime import datetime
from werkzeug.utils import secure_filename
import zipfile
import shutil
import json
import threading


app=Flask(__name__)
DATABASE = "flask_diary_app/diary.db"
app.secret_key = "secret-key"
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
TMP =  os.path.join(app.root_path, "tmp")

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
        errors, data = validation_content(request.form.get("title"), request.form.get("content"))
        if errors:
            return render_template("new.html",mode="create", errors=errors, title=data["title"],content=data["content"])
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
    return render_template("new.html",mode="create", errors={})

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
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    c = db.cursor()

    # データ取得
    c.execute("SELECT * FROM diaries WHERE id = ?", (diary_id,))
    diary = c.fetchone()

    if request.method == "POST":
        errors, data = validation_content(request.form.get("title"), request.form.get("content"))
        image_file = request.files.get("image")
        delete_image = request.form.get("delete_image")
        # 画像を取得
        c.execute("SELECT image FROM diaries WHERE id = ?", (diary_id,))
        existing = c.fetchone()
        filename = existing["image"]
        if errors:
            db.close()
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
        db.commit()
        db.close()

        return redirect(url_for("diary_detail", diary_id=diary_id))


    db.close()
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
    db = sqlite3.connect(DATABASE)
    c = db.cursor()
    c.execute("DELETE FROM diaries WHERE id = ?", (diary_id,))
    db.commit()
    db.close()
    return redirect(url_for("index"))

# 画像登録処理
def save_image(image_file):
    filename = create_uuid_filename(image_file.filename)
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    image_file.save(image_path)
    return filename

#UUID生成
def create_uuid_filename(image_file):
    ext = os.path.splitext(image_file)[1]
    return f"{uuid.uuid4().hex}{ext}"

# 画像削除
def del_image(image_filename):
    print("通過してる？")
    old_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
    if os.path.exists(old_path):
        os.remove(old_path)

# バリデーションチェック
def validation_content(title, content):
    errors = {}

    title = title.strip()
    content = content.strip()

    if not title:
        errors["title"] = "タイトルは必須項目です。"
    elif len(title) > 20:
        errors["title"] = "タイトルは20文字以内で入力してください。"

    if not content:
        errors["content"] = "本文は必須項目です。"

    return errors, {
        "title": title,
        "content": content
    }

#記事エクスポート
@app.route("/export/<int:diary_id>")
def export_diary(diary_id):
    # 一時フォルダ名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_dir = os.path.join(TMP, f"export_{timestamp}")
    images_dir = os.path.join(base_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    c = db.cursor()

    c.execute(
        "SELECT id, title, content, create_date, image FROM diaries WHERE id = ?",
        (diary_id,)
    )
    diary = c.fetchone()
    db.close()

    if diary is None:
        abort(404)

    # 画像コピー
    images = []
    if diary["image"]:
        src = os.path.join(app.config["UPLOAD_FOLDER"], diary["image"])
        dst = os.path.join(images_dir, diary["image"])
        #画像存在確認
        if os.path.exists(src):
            shutil.copy(src, dst)
            images.append(diary["image"])

    # JSON作成
    data = {
        "app": "diary_app",
        "version": 1,
        "exported_at": datetime.now().isoformat(),
        "diary": {
            "id": diary["id"],
            "title": diary["title"],
            "content": diary["content"],
            "create_date": diary["create_date"],
            "images": images
        }
    }

    json_path = os.path.join(base_dir, "data.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # ZIP作成
    zip_path = os.path.abspath(f"{base_dir}.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for foldername, _, filenames in os.walk(base_dir):
            for filename in filenames:
                file_path = os.path.join(foldername, filename)
                arcname = os.path.relpath(file_path, base_dir)
                zipf.write(file_path, arcname)

    # 一時フォルダ削除
    shutil.rmtree(base_dir)

    delayed_clean(zip_path)
    
    return send_file(
        zip_path,
        as_attachment=True,
        download_name=f"diary_export_{timestamp}.zip"
    )

#zipファイルの削除
def delayed_clean(zip_path, delay=3):
    def clean_zip():
        try:
            if os.path.exists(zip_path):
                os.remove(zip_path)
        except Exception as e:
            app.logger.error(f"Failed to delete zip: {e}")
    #3秒後に削除するようにタイマー設定（設定しないと、Windows では削除時にまだファイル掴まれてる判定でエラーになる）
    threading.Timer(delay, clean_zip).start()

@app.route("/import", methods=["POST"])
def import_diary():
    #zip受け取り
    file = request.files.get("import_file")
    if not file or file.filename == "":
        flash("インポートファイルを選択してください", "error")
        return redirect(url_for("new_diary", mode="import"))
    if not file or not file.filename.endswith(".zip"):
        flash("zip形式のファイルを選択してください", "error")
        return redirect(url_for("new_diary", mode="import"))
    # 一時フォルダ作成展開
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_dir = os.path.join(TMP, f"import_{timestamp}")
    os.makedirs(base_dir, exist_ok=True)

    zip_path = os.path.join(base_dir, "import.zip")
    file.save(zip_path)

    with zipfile.ZipFile(zip_path, "r") as zipf:
        zipf.extractall(base_dir)
    
    # json読み込み
    json_path = os.path.join(base_dir, "data.json")
    try:
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        if data.get("app") != "diary_app":
            raise ValueError("invalid app")

        if data.get("version") != 1:
            raise ValueError("invalid version")
    # ファイルがない、json読み込みエラー、jsonに記載されたappとversionの記載が違ったらエラーメッセージを返す
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        flash("インポートファイルが不正です。", "error")
        return redirect(url_for("new_diary", mode="import"))
    diary = data["diary"]
    #バリデーションチェック
    errors, data = validation_content(
    diary["title"],
    diary["content"]
    )
    if errors:
        flash("インポートデータに不正があります。", "error")
        for message in errors.values():
            flash("・"+message, "error")
        return redirect(url_for("new_diary", mode="import"))
    # 画像コピー
    image_filename = None
    images_dir = os.path.join(base_dir, "images")
    if diary["images"]:
        src_name = diary["images"][0]
        src = os.path.join(images_dir, src_name)
        if os.path.exists(src):
            image_filename = create_uuid_filename(src_name)
            dst = os.path.join(app.config["UPLOAD_FOLDER"], image_filename)
            shutil.copy(src, dst)

    db = sqlite3.connect(DATABASE)
    c = db.cursor()

    c.execute("""
        INSERT INTO diaries (title, content, create_date, image)
        VALUES (?, ?, ?, ?)
        """, (
        diary["title"],
        diary["content"],
        diary["create_date"],
        image_filename
    ))

    db.commit()
    db.close()
    shutil.rmtree(base_dir)
    return redirect(url_for("index"))
