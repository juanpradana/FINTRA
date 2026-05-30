FROM python:3.12-slim
WORKDIR /app
RUN groupadd -r fintra && useradd -r -g fintra -d /app -s /sbin/nologin fintra
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p data && chown -R fintra:fintra data
USER fintra
VOLUME ["/app/data"]
CMD ["python", "-m", "bot"]
