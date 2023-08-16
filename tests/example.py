"""Script meant to be run from the CLI with the conntracker command."""
import socket

from conntracker.testing import echo_server


def main() -> None:
    """Entrypoint that will open a socket connection."""
    with echo_server() as addr:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(addr)
            val = "Nothing interesting here"
            print(f"Sending the following data '{val}' to: {addr}")
            for _ in range(10):
                sock.send(val.encode())


if __name__ == "__main__":
    main()
