# Splitzie

A template with a python web server and a react web app

# Getting started

## Server

```bash
cd server
make virtualenv
source .venv/bin/activate
make install
python3 -m server
```

## Web UI

```bash
cd web-ui
npm install
npm start
```

## Deploy

```bash
docker-compose build
docker compose up
```

Open the web ui on http://localhost:80/
