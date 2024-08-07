# Usar una imagen base de Python
FROM python:3.9-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar los archivos de requerimientos y la aplicación
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

# Crear el directorio para los archivos de configuración
RUN mkdir /config

# Exponer el puerto de la aplicación
EXPOSE 5000

# Comando para ejecutar la aplicación
CMD ["python", "app.py"]
