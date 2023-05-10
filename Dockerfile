FROM python:3.9-slim-buster

WORKDIR /alias-game

COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip3 install -r requirements.txt

COPY . .

EXPOSE 5000
EXPOSE 8000
RUN ["chmod", "+x", "./gunicorn.sh"]
ENTRYPOINT ["./gunicorn.sh"]

