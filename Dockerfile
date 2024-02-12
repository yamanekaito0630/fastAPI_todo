FROM python:3.8.13

WORKDIR /todo_app
ADD requirements.txt .
RUN pip install -r requirements.txt