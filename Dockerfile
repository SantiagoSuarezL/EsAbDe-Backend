# Usa una imagen base oficial de Python
FROM python:3.12.5

ENV PYTHONUNBUFFERED=1

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /EsAbDe-backend

# Copia los archivos de requisitos (requirements.txt) al contenedor
COPY requirements.txt /EsAbDe-backend/

# Instala las dependencias (sin utilizar tu entorno virtual local .venv)
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo el código de tu aplicación al directorio de trabajo en el contenedor
COPY . /EsAbDe-backend/

# Expone el puerto en el que Django correrá (por defecto, 8000)
EXPOSE 8000

# Ejecuta el servidor de Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]