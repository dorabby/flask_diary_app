from datetime import datetime
import json
import os
import shutil
import threading
import uuid
import zipfile
from flask import app, current_app, flash, redirect, url_for

from flask_diary_app.config import Config
from flask_diary_app.db import get_db
from flask_diary_app.errors import internal_error

#日記一覧検索
def get_diary_list(keyword="", scope="title", sort="new"):
  db = get_db()
  try:
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
  finally:
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
  return diary_list

#記事取得
def get_diary(diary_id):
    db = get_db()
    try:
        c = db.cursor()
        c.execute("SELECT * FROM diaries WHERE id = ?", (diary_id,))
        diary = c.fetchone()
    finally:
        db.close()
    return diary

#記事登録
def create(date, data, filename):
    db = get_db()
    try:
      c = db.cursor()
      c.execute("INSERT INTO diaries (create_date, updata_date, title, content, image) VALUES (?, ?, ?, ?, ?)",
          (date, date, data["title"], data["content"], filename))
      db.commit()
    except Exception:
      db.rollback()
      raise
    finally:
        db.close()
    return

#記事編集
def update(diary_id, title, content, old_diary, image_file=None, delete_image=False):
    errors, data = validate_diary(title, content, image_file)
    if errors:
        return old_diary, errors
    image_file=data["image"]

    db = get_db()
    try:
        c = db.cursor()
        filename = None
        # 既存画像を取得
        image = get_image(c, diary_id)
        if image is None:
            return None, None
        filename = image["image"]
        # チェックがあれば画像削除
        if delete_image and filename:
            del_image(filename)
            filename = None
        # 新規画像保存
        elif image_file :
            if filename:
                #古い画像削除
                del_image(filename)
            filename = save_image(image_file)
        # 更新
        now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        c.execute(
            "UPDATE diaries SET title=?, content=?, updata_date=?, image=? WHERE id=?",
            (data["title"], data["content"], now, filename, diary_id)
        )
        #再検索
        c.execute("SELECT * FROM diaries WHERE id = ?", (diary_id,))
        db.commit()
        return c.fetchone(), None
    except Exception:
      db.rollback()
      raise
    finally:
        db.close()

#記事削除
def delete(diary):
    db = get_db()
    try:
        c = db.cursor()
        c.execute("DELETE FROM diaries WHERE id = ?", (diary["id"],))
        # uploadフォルダから画像を削除
        if diary["image"]:
            del_image(diary["image"])
        db.commit()
    except Exception:
      db.rollback()
      raise
    finally:
        db.close()
    
#記事エクスポート
def export_zip(diary):
    # 一時フォルダ名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_dir = os.path.join(current_app.config["TMP_FOLDER"], f"export_{timestamp}")
    image_dir = os.path.join(base_dir, "image")
    os.makedirs(image_dir, exist_ok=True)
    
    # 画像コピー
    image = None
    if diary["image"]:
        src = os.path.join(current_app.config["UPLOAD_FOLDER"], diary["image"])
        dst = os.path.join(image_dir, diary["image"])
        #画像存在確認
        if os.path.exists(src):
            shutil.copy(src, dst)
            image=diary["image"]

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
            "image": image 
        }
    }

    json_path = os.path.join(base_dir, "data.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # tmp配下にZIP作成
    zip_path = os.path.abspath(f"{base_dir}.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for foldername, _, filenames in os.walk(base_dir):
            for filename in filenames:
                file_path = os.path.join(foldername, filename)
                arcname = os.path.relpath(file_path, base_dir)
                zipf.write(file_path, arcname)
    # 作業フォルダ削除
    shutil.rmtree(base_dir)
    return zip_path, timestamp

#記事インポート
def import_zip(file):
    # 一時フォルダ作成展開
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_dir = os.path.join(current_app.config["TMP_FOLDER"], f"import_{timestamp}")
    os.makedirs(base_dir, exist_ok=True)
    try:
        zip_path = os.path.join(base_dir, "import.zip")
        file.save(zip_path)
        with zipfile.ZipFile(zip_path, "r") as zipf:
            zipf.extractall(base_dir)
        # json読み込み
        data = import_json(base_dir)
        diary = data["diary"]
        #二つ目の戻り値は今回不要なので_で記載して無視する。また、画像関連はこのタイミングではチェックできないため第三引数は何も指定しない
        errors, _  = validate_diary(diary["title"], diary["content"])
        if errors:
            return "validation_error", errors
        # 画像コピー
        image_filename = None
        image_dir = os.path.join(base_dir, "image")
        if diary["image"]:
            src_name = diary["image"]
            src = os.path.join(image_dir, src_name)
            size = os.path.getsize(src)
            errors = {}
            # 拡張子とファイルサイズの確認
            if not check_extension_file(src_name):
                errors["image"] = Config.EXTENSION_FILE
                return "validation_error", errors 
            elif size > Config.MAX_IMAGE_SIZE:
                errors["image"] = Config.OVERSIZE_IMAGE
                return "validation_error", errors
            if os.path.exists(src):
                image_filename = create_uuid_filename(src_name)
                dst = os.path.join(current_app.config["UPLOAD_FOLDER"], image_filename)
                shutil.copy(src, dst)
        create(diary["create_date"], diary, image_filename)
        return "ok", None
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        return "format_error", "インポートファイルが不正です。"
    finally:
        shutil.rmtree(base_dir)

# json読み込み
def import_json(base_dir):
    json_path = os.path.join(base_dir, "data.json")
    try:
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        if data.get("app") != "diary_app":
            raise ValueError("invalid app")

        if data.get("version") != 1:
            raise ValueError("invalid version")
        return data
    # ファイルがない、json読み込みエラー、jsonに記載されたappとversionの記載が違ったらエラーメッセージを返す
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        raise

#画像取得
def get_image(c, diary_id):
      c.execute("SELECT image FROM diaries WHERE id = ?", (diary_id,))
      return c.fetchone()

#アップロードされたファイルが許可された拡張子か判定
def check_extension_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

# 画像登録処理
def save_image(image_file):
    filename = create_uuid_filename(image_file.filename)
    image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    image_file.save(image_path)
    return filename

#UUID生成
def create_uuid_filename(image_file):
    ext = os.path.splitext(image_file)[1]
    return f"{uuid.uuid4().hex}{ext}"

# 画像削除
def del_image(image_filename):
    old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image_filename)
    if os.path.exists(old_path):
        os.remove(old_path)

#作成したzipファイルの削除の予約（削除自体はsend_file実行後、OSが zip を掴んで送信中に、10秒経過したら別スレッドが起動して削除を行う）
def delayed_clean(zip_path, delay=Config.DELETE_ZIP_DElAY):
    def clean_zip():
        if os.path.exists(zip_path):
            os.remove(zip_path)
    #10秒後に削除するようにタイマー設定（設定しないと、Windows では削除時にまだファイル掴まれてる判定でエラーになる）
    threading.Timer(delay, clean_zip).start()

#バリデーションチェック
def validate_diary(title, content, image_file=None):
    errors = {}

    title = title.strip()
    content = content.strip()

    if not title:
        errors["title"] = Config.REQUIED_TITLE
    elif len(title) > 20:
        errors["title"] = Config.TITLE_LENGTH

    if not content:
        errors["content"] = Config.REQUIED_CONTENT

    if image_file and image_file.filename:
        if not check_extension_file(image_file.filename):
            errors["image"] = Config.EXTENSION_FILE

        elif not check_image_size(image_file):
            errors["image"] = Config.OVERSIZE_IMAGE

    return errors, {
        "title": title,
        "content": content,
        "image":image_file
    }

# ファイルサイズ確認
def check_image_size(file):
    # ファイルポインタをファイルの末尾に移動
    file.seek(0, os.SEEK_END)
    # 現在のカーソル位置（バイト数） を返す
    size = file.tell()
    # ファイルポインタを開始位置に戻す
    file.seek(0)
    return size <= Config.MAX_IMAGE_SIZE