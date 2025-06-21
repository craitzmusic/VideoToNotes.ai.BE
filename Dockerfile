FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    aria2 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app /app

# Adiciona argumento para modo de execução (dev ou prod)
ARG MODE=prod
ENV MODE=${MODE}

# Recomenda rodar como usuário não-root em produção
RUN useradd -m appuser
USER appuser

# Por padrão, executa o servidor Uvicorn em modo produção
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]