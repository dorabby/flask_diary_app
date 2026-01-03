#起動用ファイル
from flask_diary_app import app, create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)