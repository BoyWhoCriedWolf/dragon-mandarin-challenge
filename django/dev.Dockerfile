FROM python:3.11

ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y netcat-openbsd

WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . .

CMD sh -c "until nc -z postgres 5432; do sleep 1; done && python manage.py runserver 0.0.0.0:8000"



