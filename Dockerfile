FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
RUN groupadd -r fintra && useradd -r -g fintra -d /app -s /bin/fintra fintra
COPY . .
RUN mkdir -p data && chown -R fintra:fintra data
USER fintra
VOLUME ["/app/data"]
CMD ["python", "-m", "bot"]
