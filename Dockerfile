FROM python:3.8-slim-buster

WORKDIR /app

# Copiar e instalar dependencias
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

# se copian el resto de archivos, se hace en otra linea para aprovechar el cache
COPY . .

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]