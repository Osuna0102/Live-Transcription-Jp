FROM python:3.11.5


WORKDIR /app
COPY . /app
COPY main.py /app/main.py
RUN pip install -r requirements.txt
EXPOSE 5555
CMD ["python", "main.py"]
