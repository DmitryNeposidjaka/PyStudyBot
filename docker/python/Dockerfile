FROM python:3-alpine

RUN apk add supervisor
#RUN apt-get update
#RUN apt-get install supervisor

COPY supervisor/py_study_bot.conf /etc/supervisor/py_study_bot.conf

WORKDIR /var/www

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN supervisorctl start

CMD [ "python", "./index.py" ]