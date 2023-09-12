FROM python:3-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt ./
RUN apt update
RUN apt install -y gcc
RUN pip install --no-cache-dir -r requirements.txt
COPY updatedns.py /app/
CMD [ "python", "/app/server.py" ]