import socket  # noqa: F401


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    while True:
        sock, _ = server_socket.accept()  # wait for client
        data = sock.recv(1024)
        status = b"200 OK" if b"GET / " in data else b"404 Not Found"
        sock.sendall(b"HTTP/1.1 %s\r\n\r\n" % status)
        sock.close()


if __name__ == "__main__":
    main()
