FROM python:3

apt-get install supervisor
cp supervisor/py_study_bot.conf /etc/supervisor/py_study_bot.conf

WORKDIR /var/www

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

/etc/init.d/supervisor start

# CMD [ "python", "./index.py" ]