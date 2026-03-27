FROM python:3.10

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt -f https://download.pytorch.org/whl/torch_stable.html

COPY . .

CMD ["fastapi", "run", "./src/app.py", "--host", "0.0.0.0", "--port", "8000"]