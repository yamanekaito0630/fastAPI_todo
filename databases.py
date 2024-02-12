from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

Base = declarative_base()
rdb_path = "mysql+pymysql://root:root@:3306/todo_app?charset=utf8mb4"
engine = create_engine(url=rdb_path, echo=True)

Session = sessionmaker(bind=engine)
session = Session()
