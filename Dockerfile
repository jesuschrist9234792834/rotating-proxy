FROM python:3.11-slim
WORKDIR /app
COPY proxies.txt .
COPY rotator.py .
EXPOSE 8080
CMD ["python", "rotator.py"]
