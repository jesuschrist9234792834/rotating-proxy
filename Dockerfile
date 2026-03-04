FROM python:3.11-slim
WORKDIR /app
COPY proxies.txt .
COPY rotator.py .
EXPOSE 10000
CMD ["python", "rotator.py"]
