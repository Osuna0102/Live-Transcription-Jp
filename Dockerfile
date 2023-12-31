FROM python:3.11.5


WORKDIR /app

COPY main.py /app
COPY serviceAccountKey.json /app
COPY templates /app/templates
COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt
EXPOSE 5555
CMD ["python", "main.py"]