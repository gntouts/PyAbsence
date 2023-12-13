# PyAbsence
Simple Python utility that monitors LAN WiFi, identifies smartphones' absence, and notifies through MQTT

## Usage

The intended way of using PyAbsence is via Docker Compose with the provided `compose.yaml` file. Make sure you change the environment variables to match your family's
smartphones' IP's and your MQTT broker.

```bash
git clone https://github.com/gntouts/PyAbsence.git
cd PyAbsence
docker compose up -d
```

To check the logs, run:

```bash
docker logs pyabsence -f
```

## Building

To build the required Docker image:

```bash
docker build -t pyabsence:latest
```

To build the Docker image for both `arm64` and `amd64` architectures:

```bash
docker buildx build --platform linux/arm64,linux/amd64 --push -t gntouts/pyabsence:latest .
```

## Images

You can also find prebuilt images for both `arm64` and `amd64` architectures in [Dockerhub](https://hub.docker.com/r/gntouts/pyabsence).
