import re  # noqa: F401
import socket  # noqa: F401


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    while True:
        sock, _ = server_socket.accept()  # wait for client
        request: str = sock.recv(1024).decode()
        if "GET / " in request:
            sock.sendall(b"HTTP/1.1 200 OK\r\n\r\n")
        elif "GET /echo/" in request:
            sobj = re.search(r"/echo/(\S+)", request)
            if not sobj:
                sock.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\n")
            else:
                param = sobj[1]
                response_data = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(param)}\r\n\r\n{param}\n\n"
                print(f"{param=} {response_data=}")
                sock.sendall(response_data.encode("utf-8"))
        elif "404 Not Found" in request:
            sock.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")
        sock.close()


if __name__ == "__main__":
    main()
