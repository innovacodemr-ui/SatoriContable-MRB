# Usar imagen base ligera de Python
FROM python:3.10-slim

# Evitar archivos .pyc y buffering
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema (necesarias para criptografía, lxml y netcat para entrypoint)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libcairo2-dev \
    pkg-config \
    netcat-openbsd \
    openssl \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del proyecto
COPY . .

# Configurar Entrypoint
COPY ./entrypoint.sh .
RUN sed -i 's/\r$//g' /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Recolectar estáticos
RUN python manage.py collectstatic --noinput

# Exponer puerto
EXPOSE 8000

# Definir Entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Comando de arranque (Usando Gunicorn)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]
