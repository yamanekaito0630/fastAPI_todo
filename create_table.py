from models import *

import databases
import os

if __name__ == "__main__":
    path = MYSQL_NAME
    if not os.path.isfile(path):
        Base.metadata.create_all(databases.engine)

    admin = User(
        username='admin',
        password='fastapi',
        mail='hoge@example.com'
    )
    databases.session.add(admin)
    databases.session.commit()

    task = Task(
        user_id=1,
        content='タスクの締め切り',
        deadline=datetime(2024, 2, 20, 12, 00, 00),
    )
    print(task)
    databases.session.add(task)
    databases.session.commit()

    databases.session.close()
