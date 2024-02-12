from datetime import datetime, timedelta
from starlette.status import HTTP_401_UNAUTHORIZED
from fastapi import HTTPException
from models import User

import hashlib
import databases


def auth(credentials):
    # Basic認証で受け取った値
    username = credentials.username
    password = hashlib.md5(credentials.password.encode()).hexdigest()

    user = databases.session.query(User).filter(User.username == username).first()
    databases.session.close()

    if user is None or user.password != password:
        error = 'ユーザ名かパスワードが間違っています'
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail=error,
            headers={
                'WWW-Authenticate': 'Basic',
            }
        )
    return user
