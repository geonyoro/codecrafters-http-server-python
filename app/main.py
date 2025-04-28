import socket  # noqa: F401


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    while True:
        sock, _ = server_socket.accept()  # wait for client
        request: str = sock.recv(1024).decode()
        first_line = request.split("\r\n")[0]
        method, path, _ = first_line.split()
        if method != "GET":
            sock.sendall(b"HTTP/1.1 405 Method Not Allowed\r\n\r\nMethod Not Allowed")
            sock.close()
            continue
        if path == "/":
            sock.sendall(b"HTTP/1.1 200 OK\r\n\r\n")
            sock.close()
            continue
        if path.startswith("/echo/"):
            param = path[6:]
            response_data = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(param)}\r\n\r\n{param}"
            sock.sendall(response_data.encode("utf-8"))
            sock.close()
            continue
        else:
            sock.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")
            sock.close()
            continue


if __name__ == "__main__":
    main()
