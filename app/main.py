import argparse
import os  # noqa: F401
import socket  # noqa: F401
import threading
from dataclasses import dataclass


@dataclass
class Request:
    method: str
    path: str
    headers: dict[str, str]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=str, default="/tmp/")
    args = parser.parse_args()

    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    while True:
        sock, _ = server_socket.accept()  # wait for client
        threading.Thread(target=handle_sock, args=(sock, args), daemon=True).start()


def parse_request(request: str) -> Request:
    parsing_headers = False
    lines = request.split("\r\n")
    request_headers: dict[str, str] = {}
    method, path = "", ""
    for index, line in enumerate(lines):
        if index == 0:
            method, path, _ = line.split()
            parsing_headers = True
            continue
        elif parsing_headers:
            if line == "":
                # if the next line is also empty, we are here
                next_index = index + 1
                if next_index < len(lines):
                    if lines[next_index] == "":
                        parsing_headers = False
            else:
                title, value = line.split(": ")
                request_headers[title] = value
        # else:
        #     print("BODY:", line)

    return Request(method=method, path=path, headers=request_headers)


def handle_sock(sock, args):
    raw_request: str = sock.recv(1024).decode()
    req = parse_request(raw_request)

    if req.method != "GET":
        sock.sendall(b"HTTP/1.1 405 Method Not Allowed\r\n\r\nMethod Not Allowed")
        sock.close()
        return

    if req.path == "/":
        sock.sendall(b"HTTP/1.1 200 OK\r\n\r\n")
        sock.close()
        return

    if req.path.startswith("/echo/"):
        param = req.path[6:]
        response_data = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(param)}\r\n\r\n{param}"
        sock.sendall(response_data.encode("utf-8"))
        sock.close()
        return

    if req.path.startswith("/files/"):
        filename = req.path[7:]
        filepath = os.path.join(args.directory, filename)
        if not os.path.exists(filepath):
            sock.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")
            sock.close()
            return

        with open(filepath) as wfile:
            data = wfile.read()
        response_data = f"HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Length: {len(data)}\r\n\r\n{data}"
        sock.sendall(response_data.encode("utf-8"))
        sock.close()
        return

    if req.path == "/user-agent":
        param = req.headers.get("User-Agent", "")
        response_data = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(param)}\r\n\r\n{param}"
        sock.sendall(response_data.encode("utf-8"))
        sock.close()
        return

    # default catch all
    sock.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")
    sock.close()
    return


if __name__ == "__main__":
    main()
