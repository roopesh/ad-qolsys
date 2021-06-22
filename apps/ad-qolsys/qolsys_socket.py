import json
import socket
import ssl
import sys
import time
import asyncio
import threading
import appdaemon.plugins.mqtt.mqttapi as mqtt

#
# qolsys socket manager
#
# args
# yep
#

class qolsys:
    ################################################################################
    # Code

    def __init__(self, app):
        self._sock = socket.socket
        self._wrappedSocket = ssl.SSLContext.wrap_socket
        self._listening_thread = threading.Thread()
        self._listener_callback = callable
        self._hostname = ""
        self._port = 12345
        self._token = ""
        self._timeout = 60
        self.app = app
        self.__listening__ = True
        # logging.basicConfig(filename='qolsys_socket.log', level=logging.DEBUG)

    def create_socket(self, hostname, port, token, cb: callable, timeout=60):
        self._hostname = hostname
        self._port = port
        self._token = token
        self._listener_callback = cb
        self._timeout = timeout
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(timeout)
            #Set the listener callback at the instance level so we can restart the listener if needed
        except socket.error:
            self.app.log('Could not create a socket', level="ERROR")
            raise

        # Wrap SSL
        self.app.log("wrapping socket")
        self._wrappedSocket = ssl.wrap_socket(self._sock, cert_reqs=ssl.CERT_NONE, ssl_version=ssl.PROTOCOL_TLSv1_2)

        # Connect to server
        try:
            #The stupid Qolsys panel requires blocking
            # wrappedSocket.setblocking(False)
            self.app.log("connecting to socket", level="INFO")
            self._wrappedSocket.connect((hostname, port))
            self.app.log("Connected wrappedSocket: %s", self._wrappedSocket, level="INFO")
            
            self.app.log("Starting listener thread", level="INFO")
            self._start_listener()
            self.app.log("started listener", level="INFO")
            
            return True
        except socket.error:
            self.app.log("Error creating or connecting to socket %s", sys.exc_info(), level="ERROR")
            return False

    def _start_listener(self):
        self.app.log("Starting listener thread", level="INFO")
        self._listening_thread = threading.Thread(target=self.listen, args=([self._listener_callback]))
        self._listening_thread.start()
        self.app.log("started listener thread", level="INFO")

    def _reset_socket(self, timeout=1):
        self.close_socket(timeout=2)
        #self._listening_thread = threading.Thread(target=self.listen, args=([self._listener_callback]))
        self.app.log("Recreating socket", level="INFO")
        self.__listening__ = True
        self.create_socket(self._hostname, self._port, self._token, self._listener_callback, self._timeout)

    def close_socket(self, timeout=1):
        self.app.log("Detatching from wrapped socket", level="WARNING")
        self.__listening__ = False
        self._wrappedSocket.detach()
        self.app.log("Closing socket", level="WARNING")
        self._sock.close()
        time.sleep(timeout)

    def send_to_socket(self, message: json):

        self._wrappedSocket.send(b'\n')
        self._wrappedSocket.send((json.dumps(message)).encode())

        return True

    def listen(self, cb: callable):
        #listening = True
        self.app.log("starting listen", level="INFO")
        data = ""
        #err = ""
        while not (self._wrappedSocket._connected):
            self.app.log("not connected yet", level="WARNING")
            self.app.log(self._wrappedSocket._connected, level="INFO")
            time.sleep(1)
        try:
            while self._wrappedSocket._connected and self.__listening__:
                data = self._wrappedSocket.recv(8192).decode()
                if len(data) > 0:
                    self.app.log("data received from qolsys panel: %s len(data): %s", data, len(data), level="DEBUG")
                    if is_json(data):
                        try:
                            cb(data)
                        except:
                            self.app.log("Error calling callback: %s", cb, sys.exc_info(), level="ERROR")
                    else:
                        if data != 'ACK\n':
                            pass
                        self.app.log("non json data: %s", data, level="DEBUG")
                else:
                    self.app.log("No data received.  Bad token?  Detatching.", level="ERROR")
                    self._wrappedSocket.detach()
                    raise NoDataError
            self.app.log("stopped listening on qolsys socket", level="INFO")
        except socket.timeout:
            self.app.log("socket timeout, restarting socket", level="WARNING")
            self._reset_socket()
        except NoDataError:
            self.app.log("No data received from socket, restarting socket", level="INFO"
            self._reset_socket()
            # raise NoDataError
        except TimeoutError:
            self.app.log("qolsys socket TimeoutError: %s", sys.exc_info(), level="ERROR")
            self._reset_socket()
            # raise NoDataError
        except:
            self.app.log("listen failed/stopped: %s", sys.exc_info(), level="ERROR")
            self._reset_socket()



def is_json(myjson):
    try:
        json_object = json.loads(myjson)
        if json_object: return True
    except:
        #if myjson != 'ACK\n':
            #self.app.log(("not json: %s", myjson), level="WARNING")
            #self.app.log(("Error: %s", sys.exc_info()), level="ERROR")
        return False

class NoDataError(Exception):
    pass