FROM python:3

WORKDIR /var/www

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt


CMD [ "python", "./index.py" ]