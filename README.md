# Splitzie

A web app to use AI to split your bills!
1. Upload your bill
2. Give a short text description of who ate what
    "Split the Prothas and paneer curry between Amogh, Rajesh and Gokul. Rajesh didn't have any of the starters. Rajesh and Gokul rach had a coke."
3. The AI computes the mapping between the people to their items, and then returns a split up of the entire bill!

<video src="media/demo.mp4" width=200px autoplay loop></video>

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
