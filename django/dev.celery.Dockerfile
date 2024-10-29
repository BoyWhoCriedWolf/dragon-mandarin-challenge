FROM python:3.11

ENV PYTHONUNBUFFERED 1


WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt


RUN pip install watchdog

COPY . .

CMD watchmedo auto-restart --directory=./ --pattern=*.py --recursive -- celery -A cndict worker -l info

