"""
 Simple JSON-RPC Server

"""

import json
import socket
import inspect
import functions


class JSONRPCServer:
    """The JSON-RPC server."""

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = None
        self.funcs = {}

    def register(self, name, function):
        """Registers a function."""
        self.funcs[name] = function

    def start(self):
        """Starts the server."""
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.listen(1)
        print(f'Listening on port {self.port} ...')

        try:
            while True:
                # Accepts and handles client
                conn, _ = self.sock.accept()
                self.handle_client(conn)

                # Close client connection
                conn.close()

        except ConnectionAbortedError:
            pass
        except OSError:
            pass

    def stop(self):
        """Stops the server."""
        self.sock.close()

    def process_msg(self, msg):
        """Process the request message and build a response"""
        res = {'jsonrpc': '2.0'}

        try:
            # Load the json from the request
            msg = json.loads(msg)

            # Check if the request is valid
            if 'method' not in msg:
                raise ValueError('Invalid Request')
            method = msg['method']

            # Check if the request is a JSON-RPC notification
            if 'id' not in msg:
                return None
            rpc_id = msg['id']

            # Check if the method exists
            if method not in self.funcs:
                raise KeyError('Method not found')

            # Check function arguments
            func = self.funcs[method]
            func_params = inspect.signature(func).parameters
            if len(func_params) > 0:
                if 'params' in msg:
                    params = msg['params']

                    if len(params) == len(func_params):
                        res['result'] = func(*params)
                    else:
                        raise TypeError('Invalid params')
                else:
                    raise TypeError('Invalid params')
            else:
                res['result'] = func()

            # Place the id on the response
            res['id'] = rpc_id
        except json.JSONDecodeError:
            res['id'] = None
            res['error'] = {'code': -32700, 'message': 'Parse error'}
        except ValueError:
            res['id'] = None
            res['error'] = {'code': -32600, 'message': 'Invalid Request'}
        except KeyError:
            res['id'] = msg['id']
            res['error'] = {'code': -32601, 'message': 'Method not found'}
        except TypeError:
            res['id'] = msg['id']
            res['error'] = {'code': -32602, 'message': 'Invalid params'}

        return json.dumps(res)

    def handle_client(self, conn):
        """Handles the client connection."""

        # Receive message
        msg = conn.recv(1024).decode()
        print('Received:', msg)

        res = self.process_msg(msg)
        if res is not None:
            conn.send(res.encode())


if __name__ == "__main__":
    # Test the JSONRPCServer class
    server = JSONRPCServer('0.0.0.0', 8000)

    # Register functions
    server.register('hello', functions.hello)
    server.register('greet', functions.greet)
    server.register('add', functions.add)
    server.register('sub', functions.sub)
    server.register('mul', functions.mul)
    server.register('div', functions.div)

    # Start the server
    server.start()
