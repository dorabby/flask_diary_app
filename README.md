## flask-daily-app

* 日記またはメモを書くデスクトップアプリ。文章や画像を登録・編集・削除できるほか、記事のエクスポート・インポート機能も備えている。

## Description

1. 日記を作成（画像1枚登録可能）、編集、削除できる。
2. 記事をZIP形式でエクスポート/インポートできる。
3. デスクトップアプリとしてPyWebView上で動作。
4. Light/Darkテーマ対応、一覧画面で検索もできる。

## Background

* PythonのFlaskフレームワークでCRUD処理やファイル操作、デスクトップ化を学ぶ個人的学習目的で作成。
* PyWebViewを使い、ブラウザベースのUIをデスクトップアプリ化。

## Development environment

| 種別      | 名称                   |
| ------- | -------------------- |
| 開発言語    | Python(ver 3.12.4)   |
| フレームワーク | Flask(ver 3.0.3)     |
| デスクトップ化 | PyWebView(ver 6.1) |
| マークアップ  | HTML,CSS,JS          |
| DB      | SQLite               |

## Demo

* 記事作成　https://gyazo.com/2913fdb25877dd52e16ced294dc61ef4
* 記事詳細画面　https://gyazo.com/4998ba776f0864e58ca79833ceb0527f
* 記事編集　https://gyazo.com/29724891f0b8738855113790edc5ee5a
* 記事削除　https://gyazo.com/126cd0174c6cebdfa77c6f7fb9499b9d
* 記事エクスポート　https://gyazo.com/6d654086ad114d76f30d5e28ce24f4de
　└エクスポート後のファイルhttps://gyazo.com/ff2af7017f59fd32d41734c8ed847f7b
* 記事インポート　https://gyazo.com/eaf5f89b06b792d32c680286c5568b5f
* 一覧画面周り　
　└①https://gyazo.com/591418b9a6a933f1c89a24e33f7c31f1
　└②https://gyazo.com/415d139e9ef54419fbc226d02503d98d

## Usage

1. DiaryApp.exe をダブルクリックで起動。
　初回起動時に以下のフォルダが作成されるので注意：
　C:\Users\{ユーザー名}\AppData\Local\flask_diary_app（データベースやアップロード画像、一時ファイルを保持。アップロード画像は編集で画像更新後に残った古い画像や記事を削除した場合、削除するように処理している）
　exeを直接編集せず、そのまま使用すること。


## Author

* Aoi Tokuzumi
* o68.tokuzumi.aoi@gmail.com