FROM python:3.11-slim

# Variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=vacancy_project.settings \
    DEBIAN_FRONTEND=noninteractive

# Diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema (incluindo file para diagnóstico)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    netcat-openbsd \
    postgresql-client \
    dos2unix \
    file \
    && rm -rf /var/lib/apt/lists/*

# Copiar arquivo de requisitos
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copiar o entrypoint e garantir formatação UNIX
COPY entrypoint.sh /app/entrypoint.sh
RUN dos2unix /app/entrypoint.sh && \
    chmod 755 /app/entrypoint.sh && \
    sed -i 's/\r$//' /app/entrypoint.sh

# Copiar o projeto
COPY . /app/

# Expor porta
EXPOSE 8000

# Usar entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Comando para executar a aplicação
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-", "--error-logfile", "-", "vacancy_project.wsgi:application"]