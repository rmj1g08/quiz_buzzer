import socket
import selectors
import types
import PySimpleGUI as sg

###
# Network
###
HOST = '127.0.0.1'
PORT = 3000
sel = selectors.DefaultSelector()

###
# GUI
###
data=['player1', 'player2']
col_names=['name', 'buzz_success']



class Handle_Sockets(Thread):
    def __init__(self, selector):
        super().__init__(daemon=True)
        self.selector = selector

    def _read(self, sock, client):
        data = sock.recv(1024)
        if not data:
            self._close(sock, client)
            return
        self._clear_echo(client, data)
        self._broadcast(client, data)
        
    def _clear_echo(self, client, data):
        client.outb += '\033[F\033[K'.encode()
        client.outb += 'me> '.encode() + data

    def _write(self, sock, client):
        # is there anything in client mailbox?
        if not client.outb:
            return
        sent = sock.send(client.outb)
        client.outb = client.outb[sent:]

    def _close():
        print("close")

    def run(self):
        while True:
            # get ready sockets
            events = self.selector.select(timeout=None)
            for key, mask in events:
                sock = key.fileobj
                client = key.data

                if mask & selectors.EVENT_READ:
                    self._read(sock, client)

                if mask & selectors.EVENT_WRITE:
                    self._write(sock, client)

class Accept_Connections(Thread):
    def __init__(self, selector):
        super().__init__(daemon=True)
        self.selector = selector
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

def accept_wrapper(sock):
    conn, addr = sock.accept()
    print('Accepted connection from', addr)
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b'', outb=b'')
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)

def service_connection(key, mask):
    sock = key.fileobj
    data = key.data

    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)
        if recv_data:
            data.outb += recv_data
        else:
            print('closnig connection to ', data.addr)
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            print('echoing', repr(data.outb), 'to ', data.addr)
            sent = sock.send(data.outb)
            data.outb = data.outb[sent:]

def host_game():
    print("Try to Host")

    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lsock.bind((HOST, PORT))
    lsock.listen()
    print("Listening on ", (HOST, PORT))
    lsock.setblocking(False)

    sel.register(lsock, selectors.EVENT_READ, data=None)

    while True:
        events = sel.select(timeout=None)
        for key, mask in events:
            if key.data is None:
                accept_wrapper(key.fileobj)
            else:
                service_connection(key, mask)

def join_game():
    print("Try to Join")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(b'Hello, world')
        data = s.recv(1024)

    print('Received', repr(data))

def buzz():
    print("Try to buzz")

def quit():
    print("Graceful shutdown")
    window.close()

def event_switch(event):
    if event == 'Buzz':
        buzz()
    elif event == 'Host':
        host_game()
    elif event == 'Join':
        join_game()
    elif event == 'Quit':
        quit()
    elif event == sg.WINDOW_CLOSED:
        quit()
    else:
        print("How did we get into this mess? Event invalid")

layout = [ [sg.Button('Host'), sg.Button('Join')],
            [sg.Table(values=data, headings=col_names)],
            [sg.Button('Buzz')],
            [sg.Text(size=(40,1), key='-output-')],
            [sg.Button('Ok'), sg.Button('Quit')] ]

window = sg.Window('Buzzer', layout)

def main():
    # networking threads
    sel = selectors.DefaulSelector()
    Accept_Connections(sel).start()
    Handle_Sockets(sel).start()

    while True:
        event, values = window.read()
        event_switch(event)
    window.close()

if __name__ == "__main__":
    main()
