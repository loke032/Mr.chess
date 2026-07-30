FROM python:3.12

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

RUN git clone https://github.com/official-stockfish/Stockfish.git \
    && cd Stockfish/src \
    && make build ARCH=x86-64

COPY . .

CMD ["gunicorn", "--workers", "1", "--threads", "4", "--bind", "0.0.0.0:8000", "main:app"]