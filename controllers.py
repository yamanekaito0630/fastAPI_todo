import re
from datetime import datetime, timedelta

from fastapi import FastAPI, Depends, Form
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates

import databases
from auth import auth
from models import User, Task
from mycalendar import MyCalendar

pattern = re.compile(r'\w{4,20}')
pattern_pw = re.compile(r'\w{6,20}')
pattern_main = re.compile(r'^\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$')

security = HTTPBasic()
app = FastAPI(
    title='Todo アプリケーション',
    description='fast apiのチュートリアルとして作成',
    version='0.9 beta'
)
app.mount(path='/static', app=StaticFiles(directory='static'), name='static')
templates = Jinja2Templates(directory='templates')
jinja_env = templates.env


def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name='index.html'
    )


def admin(request: Request, credentials: HTTPBasicCredentials = Depends(security)):
    # Basic認証
    user = auth(credentials)
    username = user.username

    today = datetime.now()
    next_w = today + timedelta(days=7)

    task = databases.session.query(Task).filter(Task.user_id == user.id).all() if user is not None else []
    databases.session.close()

    # カレンダーをHTML形式で取得
    cal = MyCalendar(
        username=username,
        linked_date={t.deadline.strftime('%Y%m%d'): t.done for t in task}
    )
    cal = cal.formatyear(today.year, 4)

    # 直近タスクのリストを書き換え
    task = [t for t in task if today <= t.deadline <= next_w]
    links = [t.deadline.strftime('/todo/' + username + '/%Y/%m/%d') for t in task]

    return templates.TemplateResponse(
        request=request,
        name='admin.html',
        context={
            'user': user,
            'task': task,
            'links': links,
            'calender': cal
        }
    )


async def register(request: Request):
    if request.method == 'GET':
        return templates.TemplateResponse(
            request=request,
            name='register.html',
            context={
                'username': '',
                'error': []
            }
        )

    if request.method == 'POST':
        # フォームから値を取得
        data = await request.form()
        username = data.get('username')
        password = data.get('password')
        password_tmp = data.get('password_tmp')
        mail = data.get('mail')

        error = []

        tmp_user = databases.session.query(User).filter(User.username == username).first()

        # エラー処理
        if tmp_user is not None:
            error.append('同じユーザ名が存在します。')
        if password != password_tmp:
            error.append('入力したパスワードが一致しません。')
        if pattern.match(username) is None:
            error.append('ユーザ名は4〜20文字の半角英数字にしてください。')
        if pattern_pw.match(password) is None:
            error.append('パスワードは6〜20文字の半角英数字にしてください。')
        if pattern_main.match(mail) is None:
            error.append('正しくメールアドレスを入力してください。')

        if error:
            return templates.TemplateResponse(
                request=request,
                name='register.html',
                context={
                    'username': username,
                    'error': error
                }
            )

        # 問題なければ登録
        user = User(username=username, password=password, mail=mail)
        databases.session.add(user)
        databases.session.commit()
        databases.session.close()

        return templates.TemplateResponse(
            request=request,
            name='complete.html',
            context={
                'username': username
            }
        )


def detail(request: Request, username, year, month, day, credientials: HTTPBasicCredentials = Depends(security)):
    # Basic認証
    user = auth(credientials)
    if user.username != username:
        return RedirectResponse('/')

    task = databases.session.query(Task).filter(Task.user_id == user.id).all()
    databases.session.close()

    theday = '{}{}{}'.format(year, month.zfill(2), day.zfill(2))
    task = [t for t in task if t.deadline.strftime('%Y%m%d') == theday]

    return templates.TemplateResponse(
        request=request,
        name='detail.html',
        context={
            'username': username,
            'task': task,
            'year': year,
            'month': month,
            'day': day
        }
    )


async def done(request: Request, credientials: HTTPBasicCredentials = Depends(security)):
    # Basic認証
    user = auth(credientials)

    # ログインユーザのタスクを取得
    task = databases.session.query(Task).filter(Task.user_id == user.id).all()

    # フォームで受け取ったタスク終了判定により内容を変更
    data = await request.form()
    t_dones = data.getlist('done[]')

    for t in task:
        if str(t.id) in t_dones:
            t.done = True

    databases.session.commit()
    databases.session.close()

    return RedirectResponse('/admin')


async def add(request: Request, credentials: HTTPBasicCredentials = Depends(security)):
    # Basic認証
    user = auth(credentials)

    # フォームからの値を取得
    data = await request.form()
    year = int(data['year'])
    month = int(data['month'])
    day = int(data['day'])
    hour = int(data['hour'])
    minute = int(data['minute'])

    deadline = datetime(year=year, month=month, day=day, hour=hour, minute=minute)

    # タスク追加
    task = Task(user_id=user.id, content=data['content'], deadline=deadline)
    databases.session.add(task)
    databases.session.commit()
    databases.session.close()

    return RedirectResponse('/admin')


def delete(request: Request, t_id: int, credentials: HTTPBasicCredentials = Depends(security)):
    # Basic認証
    user = auth(credentials)

    # 該当タスクを取得
    task = databases.session.query(Task).filter(Task.id == t_id).first()

    # ユーザIDが異なれば削除せずリダイレクト
    if task.user_id != user.id:
        return RedirectResponse('/admin')

    # 該当タスクの削除
    databases.session.delete(task)
    databases.session.commit()
    databases.session.close()

    return RedirectResponse('/admin')


def get(request: Request, credentials: HTTPBasicCredentials = Depends(security)):
    # Basic認証
    user = auth(credentials)

    # タスク取得
    task = databases.session.query(Task).filter(Task.user_id == user.id).all()
    databases.session.close()

    # JSON形式
    task = [{
        'id': t.id,
        'content': t.content,
        'deadline': t.deadline.strftime('%Y-%m-%d %H:%M:%S'),
        'published': t.date.strftime('%Y-%m-%d %H:%M:%S'),
        'done': t.done,
    } for t in task]

    return task


async def insert(request: Request, content: str = Form(), deadline: str = Form(),
                 credentials: HTTPBasicCredentials = Depends(security)):
    # Basic認証
    user = auth(credentials)

    # タスク追加
    task = Task(user_id=user.id, content=content, deadline=datetime.strptime(deadline, '%Y-%m-%d_%H:%M:%S'))
    databases.session.add(task)
    databases.session.commit()
    databases.session.close()

    task = databases.session.query(Task).all()[-1]
    databases.session.close()

    return {
        'id': task.id,
        'content': task.content,
        'deadline': task.deadline.strftime('%Y-%m-%d %H:%M:%S'),
        'published': task.date.strftime('%Y-%m-%d %H:%M:%S'),
        'done': task.done,
    }
