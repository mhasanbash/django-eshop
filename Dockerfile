FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade -i https://package-mirror.liara.ir/repository/pypi/simple pip

RUN pip install --no-cache-dir \
    -i https://package-mirror.liara.ir/repository/pypi/simple \
    -r requirements.txt

COPY . .

RUN mkdir -p /app/staticfiles

EXPOSE 8000



