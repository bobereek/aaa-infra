FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
# ставим легкий torch
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install -r requirements.txt

COPY . .

CMD [ "uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]