# image
FROM python:3.11

# env
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# install packages
RUN apt-get update && apt-get -y install curl nginx
RUN python3 -m pip install --upgrade setuptools
RUN pip install --upgrade pip

# Copy all app files
COPY . /app/
WORKDIR /app

# install python library
COPY requirements.txt /app/
RUN pip install -r requirements.txt

# docker entrypoint
RUN chmod +x /app/docker-entrypoint.sh
ENTRYPOINT [ "/app/docker-entrypoint.sh" ]
