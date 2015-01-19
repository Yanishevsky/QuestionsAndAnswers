web: gunicorn runp-heroku:app
init: python db_create.py && python db_upgrade.py
upgrade: python db_upgrade.py

