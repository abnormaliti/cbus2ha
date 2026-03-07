# cbus2ha Docker Setup

This directory contains the necessary files to run the `cbus2ha` Home Assistant Add-on using Docker or Docker Compose without installing it directly into Home Assistant OS.

## Prerequisites
- Docker
- Docker Compose (Optional, but recommended)

## Configuration

Before building and running the container, you must configure the add-on by editing the `options.json` file. This file must be located in this directory (`docker/`), alongside the `docker-compose.yml` file.

### Customizing `options.json`

The following parameters are available in the configuration:

#### MQTT Configuration (`mqtt`)
- **`mqtt_broker`**: Hostname or IP address of your MQTT broker (e.g., `core-mosquitto` or `192.168.1.100`)
- **`mqtt_username`**: Username for MQTT authentication (leave empty if no authentication required)
- **`mqtt_password`**: Password for MQTT authentication (leave empty if no authentication required)
- **`mqtt_use_tls`**: Enable TLS/SSL encryption for MQTT connection (`true` or `false`)
- **`mqtt_port`**: Custom MQTT port (e.g., `1883`. Use `0` for defaults: 1883 for non-TLS, 8883 for TLS)

#### CBUS Connection Configuration (`cbus`)
- **`cbus_connection_type`**: Select `tcp` for network connection (CNI) or `serial` for USB connection (PCI)
- **`cbus_connection_string`**: For TCP: IP:port (e.g., `192.168.1.50:10001`). For Serial: device path (e.g., `/dev/ttyUSB0`)
- **`cbus_timesync`**: Interval in seconds to sync time with C-Bus network (`0` = disabled, default: `300`)
- **`project_file_path`**: Optional path to C-Bus Toolkit project file (`.cbz`) for custom device labels

#### CBUS Group Address Modifiers (`ga`)
All group addresses are imported as dimmable lights by default. Use these fields to change the import classification or ignore certain addresses.
- **`non_dimmable_lights`**: Comma-separated group addresses for non-dimmable lights (e.g., `"26,65,81"`)
- **`switches`**: Comma-separated group addresses for switch devices (e.g., `"15,90"`)
- **`binary_sensors`**: Comma-separated group addresses for read-only binary sensor devices (e.g., `"10,20,30"`)
- **`ignore`**: Comma-separated group addresses to exclude from MQTT discovery (e.g., `"5,15,25"`)

---

## Building and Running

### Option 1: Using Docker Compose (Recommended)

To build the image from the source code and start the container in the background, carefully review your `options.json` file and then run:

```bash
docker-compose up -d --build
```

To view the logs from the running container:
```bash
docker-compose logs -f
```

To stop the container:
```bash
docker-compose down
```

### Option 2: Using Docker CLI natively

If you prefer to build the container without Docker Compose, ensure your shell is currently located in this `docker` directory. We must specify the build context as the parent directory (`..`) at the end of the `docker build` command so that the project source files can be copied.

1. Build the Docker Image:
```bash
docker build -t cbus2ha -f Dockerfile ..
```

2. Run the Container:
Make sure to adjust the path to your customized `options.json` file and USB device path if necessary:
```bash
docker run -d \
  --name cbus2ha \
  --restart unless-stopped \
  -v $(pwd)/options.json:/data/options.json:ro \
  --device /dev/ttyUSB0 \
  cbus2ha
```
*(If you are using a TCP/CNI connection instead of a Serial connection, you can omit the `--device /dev/ttyUSB0` flag.)*
