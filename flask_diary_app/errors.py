from flask import flash, redirect, url_for

#500エラー時
def internal_error(e):
    print(e)
    flash("予期しないエラーが発生しました。", "error")
    return redirect(url_for("diary.index"))