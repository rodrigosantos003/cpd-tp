"""
 Simple JSON-RPC Client

"""

import json
import socket


class JSONRPCClient:
    """The JSON-RPC client."""

    def __init__(self, host, port):
        self.sock = socket.socket()
        self.sock.connect((host, port))
        self.ID = 0

    def close(self):
        """Closes the connection."""
        self.sock.close()

    def send(self, msg):
        """Sends a message to the server."""
        self.sock.sendall(msg.encode())
        return self.sock.recv(1024).decode()

    def invoke(self, method, params):
        """Invokes a remote function."""
        req = {
            'Hello': 'World'
        }
        msg = self.send(json.dumps(req))
        res = json.loads(msg)
        return res

    def __getattr__(self, name):
        """Invokes a generic function."""
        def inner(*params):
            return self.invoke(name, params)
        return inner


if __name__ == "__main__":

    # Test the JSONRPCClient class
    client = JSONRPCClient('127.0.0.1', 8000)
    res = client.div(2, 3)
    print(res)
    client.close()
