import socket


class SocketHandler:
    def __init__(self, host='127.0.0.1', port=12345, mod_version='1.0.1'):
        self.host = host
        self.port = port
        self.mod_version = mod_version
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))

    def close(self):
        self.client_socket.close()

    def send_and_rec(self, data):
        self.connect()
        self.client_socket.sendall(data.encode())
        massage = self.client_socket.recv(1024).decode().strip()
        self.close()
        return massage

    def play(self, path):
        return self.send_and_rec(f'LOAD_LEVEL{path}\r\n')

    def get_version(self):
        return self.send_and_rec(f'VERSION\r\n')

    def is_connected(self):
        try:
            self.send_and_rec(f'CONNECT\r\n')
            return True
        except ConnectionRefusedError:
            return False

    def is_new_version(self):
        return self.get_version() == self.mod_version


if __name__ == '__main__':
    handler = SocketHandler()
    print(handler.is_connected())
    print(handler.is_new_version())
