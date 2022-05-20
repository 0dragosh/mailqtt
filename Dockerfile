FROM python:3.10-slim
WORKDIR /mailqtt
COPY requirements.txt .
RUN pip3 install -r requirements.txt
COPY mailqtt.py .
EXPOSE 1025
CMD ["python3", "mailqtt.py"]
