#!/bin/bash
echo "=== ENTRYPOINT SIMPLES ==="
echo "Data e hora: $(date)"
echo "Hostname: $(hostname)"
echo "Usuário: $(whoami)"
echo "Diretório atual: $(pwd)"
echo "Arquivos no diretório:"
ls -la
echo "=== VARIÁVEIS DE AMBIENTE ==="
echo "POSTGRES_HOST: $POSTGRES_HOST"
echo "POSTGRES_DB: $POSTGRES_DB"
echo "POSTGRES_USER: $POSTGRES_USER"
echo "DEBUG: $DEBUG"
echo "=== AGUARDANDO POSTGRES ==="
echo "Tentando conectar ao PostgreSQL em $POSTGRES_HOST:5432..."
for i in {1..30}; do
    if nc -z $POSTGRES_HOST 5432 2>/dev/null; then
        echo "✅ PostgreSQL está pronto!"
        break
    fi
    echo "⏳ Tentativa $i: PostgreSQL não está pronto ainda..."
    sleep 2
    if [ $i -eq 30 ]; then
        echo "❌ PostgreSQL não ficou pronto após 30 tentativas"
        exit 1
    fi
done
echo "=== EXECUTANDO MIGRAÇÕES ==="
python manage.py migrate --noinput
echo "=== INICIANDO SERVIDOR ==="
exec "$@"
