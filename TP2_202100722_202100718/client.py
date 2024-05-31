"""
 Simple JSON-RPC Client
"""

import json
import socket
import time


class JSONRPCClient:
    """The JSON-RPC client."""

    def __init__(self, host, port):
        self.sock = socket.socket()
        self.sock.connect((host, port))
        self.ID = 1

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
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": self.ID
        }
        self.ID += 1
        msg = self.send(json.dumps(req))
        res = json.loads(msg)

        if 'error' in res:
            error_code = res['error'].get('code')
            error_message = res['error'].get('message')
            if error_code == -32602:
                raise TypeError(error_message)
            if error_code == -32601:
                raise AttributeError(error_message)

        if 'result' in res:
            return res['result']

        return res

    def batch(self, requests):
        """Sends a batch of requests."""
        batch_requests = []
        for req in requests:
            batch_requests.append({
                "jsonrpc": "2.0",
                "method": req['method'],
                "params": req.get('params', []),
                "id": self.ID
            })
            self.ID += 1
        response = self.send(json.dumps(batch_requests))
        return json.loads(response)

    def __getattr__(self, name):
        """Invokes a generic function."""

        def inner(*args, **kwargs):
            if kwargs:
                return self.invoke(name, kwargs)
            return self.invoke(name, list(args))

        return inner

    def sendNotification(self, method):
        """Sends a notification."""
        req = {
            "jsonrpc": "2.0",
            "method": method
        }
        self.sock.sendall(json.dumps(req).encode())


if __name__ == "__main__":
    # Test the JSONRPCClient class
    client = JSONRPCClient('127.0.0.1', 8000)

    client.sendNotification('keepAlive')
    time.sleep(0.1)
    # Single request example
    res = client.div(a=2, b=3)
    print(res)

    time.sleep(0.1)

    # Batch request example
    batch_requests = [
        {"method": "hello"},
        {"method": "greet", "params": ["World"]},
        {"method": "add", "params": [1, 2]}
    ]
    batch_responses = client.batch(batch_requests)
    print(batch_responses)

    time.sleep(0.1)

    client.sendNotification('closeConnection')

    time.sleep(0.1)

    client.close()
