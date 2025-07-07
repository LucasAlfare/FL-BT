FROM python:3.10-slim
LABEL authors="Francisco Lucas"

# Evita prompts interativos e melhora logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Incluindo FFMPEG na imagem; necessário para lib Spleeter do python
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

# Diretório de trabalho
WORKDIR /app

# Copia dependências
COPY server/requirements.txt .

# Instala dependências
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copia código do servidor
COPY server/ .

# Expõe a porta usada pelo FastAPI
EXPOSE 8000

# Comando para iniciar o servidor
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]