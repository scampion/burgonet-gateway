from datetime import datetime
from flask import Flask

def datetimeformat(value, format='%Y-%m-%d %H:%M'):
    if value is None:
        return ''
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    return value.strftime(format)

def init_app(app: Flask):
    app.jinja_env.filters['datetimeformat'] = datetimeformat
