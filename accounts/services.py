import subprocess

def scan_wifi():
    try:
        result = subprocess.check_output(
            ["nmcli", "-t", "-f", "ACTIVE,SSID", "dev", "wifi"],
            encoding="utf-8"
        )

        networks = []
        connected = None

        for line in result.split(""):
            if line:
                active, ssid = line.split(":", 1)
                networks.append(ssid)
                if active == "yes":
                    connected = ssid

        return {
            "connected": connected,
            "networks": list(set(networks))
        }

    except Exception as e:
        return {
            "connected": None,
            "networks": [],
            "error": str(e)
        }


def connect_wifi(ssid, password):
    try:
        subprocess.check_call([
            "nmcli",
            "dev",
            "wifi",
            "connect",
            ssid,
            "password",
            password
        ])

        return {
            "message": f"Conectado a {ssid} correctamente"
        }

    except subprocess.CalledProcessError:
        return {
            "message": "No se pudo conectar a la red"
        }