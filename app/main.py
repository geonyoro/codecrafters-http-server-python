import argparse
import gzip
import os  # noqa: F401
import socket  # noqa: F401
import threading
from dataclasses import dataclass

HTTP_STATUS_VERBOSE: dict[int, str] = {
    200: "OK",
    201: "Created",
    400: "Bad Request",
    404: "Not Found",
    405: "Method Not Allowed",
}


class GzipEncoder:
    @staticmethod
    def encode(data: bytes) -> bytes:
        return gzip.compress(data)


ALLOWED_ENCODINGS = {
    "gzip": GzipEncoder,
}


@dataclass
class Request:
    method: str
    path: str
    headers: dict[str, str]
    data: str


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=str, default="/tmp/")
    args = parser.parse_args()

    # You can use print statements as follows for debugging, they'll be visible when running tests.
    port = 4221
    print(f"Logs from your program will appear here! Listening on {port=}")

    server_socket = socket.create_server(("localhost", port), reuse_port=True)
    while True:
        sock, _ = server_socket.accept()  # wait for client
        threading.Thread(target=handle_sock, args=(sock, args), daemon=True).start()


def parse_request(request: str) -> Request:
    parsing_headers = False
    lines = request.split("\r\n")
    request_headers: dict[str, str] = {}
    method, path = "", ""
    data_lines = []
    for index, line in enumerate(lines):
        if index == 0:
            method, path, _ = line.split()
            parsing_headers = True
            continue
        elif parsing_headers:
            if line == "":
                parsing_headers = False
            else:
                title, value = line.split(": ")
                request_headers[title] = value
        else:
            data_lines.append(line)

    data = "\r\n".join(data_lines)
    return Request(method=method, path=path, headers=request_headers, data=data)


def handle_sock(sock, args):
    while True:
        raw_request: str = sock.recv(1024).decode()
        if not raw_request.strip():
            continue

        req = parse_request(raw_request)

        if req.method == "GET":
            if req.path == "/":
                sock.sendall(to_response_data(req=req, body="", status_int=200))
                continue

            if req.path.startswith("/echo/"):
                echo_path = req.path[6:]
                sock.sendall(to_response_data(req=req, body=echo_path))
                continue

            if req.path.startswith("/files/"):
                filename = req.path[7:]
                filepath = os.path.join(args.directory, filename)
                if not os.path.exists(filepath):
                    sock.sendall(to_response_data(req=req, body="", status_int=404))
                    continue

                with open(filepath) as wfile:
                    data = wfile.read()
                sock.sendall(
                    to_response_data(
                        req=req,
                        body=data,
                        headers={"Content-Type": "application/octet-stream"},
                    )
                )
                continue

            if req.path == "/user-agent":
                user_agent = req.headers.get("User-Agent", "")
                sock.sendall(to_response_data(req=req, body=user_agent))
                continue

            # default catch all
            sock.sendall(to_response_data(req=req, body="", status_int=404))
            continue

        elif req.method == "POST":
            if req.path.startswith("/files/"):
                filename = req.path[7:]
                filepath = os.path.join(args.directory, filename)
                with open(filepath, "w") as wfile:
                    data = wfile.write(req.data)
                sock.sendall(to_response_data(req=req, body="", status_int=201))
                continue

        else:
            sock.sendall(to_response_data(req=req, body="", status_int=405))
            continue


def to_response_data(
    req: Request, body: str | bytes, status_int: int = 200, headers: dict | None = None
) -> bytes:
    if isinstance(body, str):
        body = body.encode("utf-8")

    try:
        status_str = HTTP_STATUS_VERBOSE[status_int]
    except KeyError:
        raise KeyError(f"Unsupported status code {status_int}")

    if not headers:
        headers = {}

    if body:
        requested_encodings = [
            i.strip() for i in req.headers.get("Accept-Encoding", "").split(",")
        ]
        for acc_encoding in requested_encodings:
            encoder = ALLOWED_ENCODINGS.get(acc_encoding)
            if encoder:
                # encode body
                headers["Content-Encoding"] = acc_encoding
                body = encoder.encode(body)
                # for now only gzip
                break

        # defaults
        if "Content-Type" not in headers:
            headers["Content-Type"] = "text/plain"
        if "Content-Length" not in headers:
            headers["Content-Length"] = len(body)

    headers_as_list = [f"{key}: {value}" for key, value in headers.items()]
    headers_as_str = "\r\n".join(headers_as_list)
    response_data = f"HTTP/1.1 {status_int} {status_str}\r\n{headers_as_str}\r\n"
    response_data = response_data.encode("utf-8")
    if body:
        response_data += b"\r\n"
        response_data += body

    return response_data


if __name__ == "__main__":
    main()
