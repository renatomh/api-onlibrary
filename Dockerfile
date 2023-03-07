# Using the required Python container image
FROM python:3.9-slim-buster

# Set the working directory to the application
WORKDIR /app

# Copy the current directory contents into the container application directory
COPY . /app/

# Installing the dependencies and compiling translations
RUN pip install --upgrade pip
RUN pip install --upgrade setuptools wheel
RUN pip install -r requirements.txt
RUN pybabel compile -d app/translations

# Installing ffmpeg
RUN apt-get -y update \
    && apt-get -y upgrade \
    && apt-get install -y ffmpeg

# Exposing defined port
EXPOSE 8080

# Run the command to start application
# It'll work only after copying '.env' and 'service-credentials.json' files to the container
CMD ["gunicorn", "--worker-class", "eventlet", "--bind",  "0.0.0.0:8080", "-m", "007", "wsgi:app", "--reload"]
