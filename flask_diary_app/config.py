# 設定値

class Config:
    # 画像アップロードで許可された拡張子
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    # 一覧でプレビュー表示する文字数上限
    TEXT_PREVIEW=30
    # tmp配下に作成したzip削除までの時間
    DELETE_ZIP_DElAY=10
    # 最大アップロードサイズ
    MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB

    #エラーメッセージ
    DIARY_NOT_FOUND ="日記情報がありませんでした。"
    REQUIED_TITLE="タイトルは必須項目です。"
    TITLE_LENGTH="タイトルは20文字以内で入力してください。"
    REQUIED_CONTENT="本文は必須項目です。"
    EXTENSION_FILE="対応していない画像形式です。"
    OVERSIZE_IMAGE="画像サイズは5MB以下にしてください。"

