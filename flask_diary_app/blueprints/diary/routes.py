from datetime import datetime
import shutil
from flask import Blueprint, flash, redirect, render_template, request, send_file, url_for, current_app, send_from_directory
from flask_diary_app.blueprints.diary.services import create, delayed_clean, delete, export_zip, get_diary, get_diary_list, import_zip, save_image, update, validate_diary
from flask_diary_app.config import Config
from flask_diary_app.errors import internal_error
from pathlib import Path


#Blueprintオブジェクトを作る（アプリを分割して管理するためのもの）
diary_bp = Blueprint("diary", __name__)


# 一覧表示
@diary_bp.route("/")
def index():
    #検索ワードと検索対象とソート
    keyword = request.args.get("search", "").strip()
    scope = request.args.get("scope", "title")
    sort = request.args.get("sort", "new")
    preserve = request.args.get("preserve", "")
    try:
      diary_list = get_diary_list(keyword, scope, sort)
    except Exception as e:
      return internal_error(e)
    return render_template("index.html", diaries=diary_list, sort=sort, preserve=preserve)

# 詳細取得
@diary_bp.route("/diary/<int:diary_id>")
def detail_diary(diary_id):
    try:
        diary = get_diary(diary_id)
        if diary is None:
            flash(Config.DIARY_NOT_FOUND, "error")
            return redirect(url_for("diary.index"))
    except Exception as e:
        return internal_error(e)
    return render_template("detail.html", diary=diary)

# 新規登録
@diary_bp.route("/new", methods=["GET", "POST"])
def new_diary():
    if request.method == "POST":
        image_file = request.files.get("image")
        #バリデーションチェック
        errors, data = validate_diary(request.form.get("title"), request.form.get("content"), image_file)
        if errors:
            return render_template("new.html",mode="create", errors=errors, title=data["title"],content=data["content"])
        filename = None
        if image_file:
            filename = save_image(image_file)

        date = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        try:
            create(date, data, filename)
        except Exception as e:
            return internal_error(e)
        return redirect(url_for("diary.index"))
    return render_template("new.html",mode="create", errors={})

# 編集
@diary_bp.route("/edit/<int:diary_id>", methods=["GET", "POST"])
def edit_diary(diary_id):
    title = request.form.get("title")
    content = request.form.get("content")
    image_file = request.files.get("image")
    delete_image = request.form.get("delete_image")
    try:
        if request.method == "POST":
            #存在確認
            diary = get_diary(diary_id)
            if diary is None:
              flash(Config.DIARY_NOT_FOUND, "error")
              return redirect(url_for("diary.index"))
            #更新処理
            diary, errors = update(diary["id"], title, content, diary,image_file, delete_image)
            if errors:
                return render_template(
                    "edit.html",
                    errors=errors,
                    title=title,
                    content=content,
                    diary_id=diary_id,
                    image=diary["image"]
                )
            if diary is None:
                flash(Config.DIARY_NOT_FOUND, "error")
                return redirect(url_for("diary.index"))

            return redirect(url_for("diary.detail_diary", diary_id=diary_id))
        
        diary = get_diary(diary_id)
        if diary is None:
            flash(Config.DIARY_NOT_FOUND, "error")
            return redirect(url_for("diary.index"))
        return render_template(
            "edit.html",
            errors={},
            title=diary["title"],
            content=diary["content"],
            diary_id=diary_id,
            image=diary["image"]
        )

    except Exception as e:
        return internal_error(e)

# 削除
@diary_bp.route("/delete/<int:diary_id>", methods=["POST"])
def delete_diary(diary_id):
    try:
        #存在確認
        diary = get_diary(diary_id)
        if diary is None:
          flash(Config.DIARY_NOT_FOUND, "error")
          return redirect(url_for("diary.index"))
        delete(diary)
    except Exception as e:
        return internal_error(e)
    return redirect(url_for("diary.index"))

#記事エクスポート
@diary_bp.route("/export/<int:diary_id>")
def export_diary(diary_id):
    try:
        #存在確認
        diary = get_diary(diary_id)
        if diary is None:
          flash(Config.DIARY_NOT_FOUND, "error")
          return redirect(url_for("diary.index"))
    except Exception as e:
        return internal_error(e)

    zip_path, timestamp = export_zip(diary)
    #zipファイル削除処理
    # delayed_clean(zip_path)
    # return send_file(
    #     zip_path,
    #     as_attachment=True,
    #     download_name=f"diary_export_{timestamp}.zip"
    # )
    downloads = Path.home() / "Downloads"
    downloads.mkdir(exist_ok=True)

    final_path = downloads / f"diary_export_{timestamp}.zip"
    shutil.copy(zip_path, final_path)

    flash(f"エクスポートしました: {final_path}", "success")
    delayed_clean(zip_path)
    return redirect(url_for("diary.detail_diary", diary_id=diary_id))

#記事インポート
@diary_bp.route("/import", methods=["POST"])
def import_diary():
    #zip受け取り
    file = request.files.get("import_file")
    if not file or file.filename == "":
        flash("インポートファイルを選択してください", "error")
        return redirect(url_for("diary.new_diary", mode="import"))
    if not file or not file.filename.endswith(".zip"):
        flash("zip形式のファイルを選択してください", "error")
        return redirect(url_for("diary.new_diary", mode="import"))
    
    try:
        result, payload = import_zip(file)
    except Exception as e:
        return internal_error(e)
    if result == "format_error":
        flash(payload, "error")
        return redirect(url_for("diary.new_diary", mode="import"))

    if result == "validation_error":
        flash("インポートデータに不正があります。", "error")
        for msg in payload.values():
            flash("・" + msg, "error")
        return redirect(url_for("diary.new_diary", mode="import"))

    return redirect(url_for("diary.index"))

@diary_bp.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        filename
    )
