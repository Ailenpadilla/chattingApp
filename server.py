import socket
import threading
from threading import Lock

HOST = '127.0.0.1'
PORT = 5556

clients = {}
lock = Lock()

def handle_client(client_socket, client_name):
    try:
        while True:
            data = client_socket.recv(1024)
            if not data:
                break

            message = data.decode('utf-8')
            if message == "update":
                send_client_list(client_socket)
            else:
                recipient, actual_message = message.split(':')

                # Send the message to the specified client
                with lock: 
                    if recipient in clients:
                        recipient_socket, _ = clients[recipient]
                        recipient_socket.send(f"{client_name}: {actual_message}".encode('utf-8'))
                    else:
                        client_socket.send("Recipient not found.".encode('utf-8'))

    except Exception as e:
        print(f"Error handling client {client_name}: {e}")
    finally:
        client_socket.close()
        with lock:
            del clients[client_name]
        send_client_list_all()
        
def send_client_list_all():
    client_list = []

    with lock:
        client_list = [(k, sock) for (k, (sock, _)) in clients.items()]

    if len(client_list) != 0:
        client_names, sockets = zip(*client_list)    
        send_client_list(client_names, sockets)

def send_client_list(client_names, sockets):
    try:
        # Construct the client list string
        client_list_str = " ".join(client_names)

        for client_socket in sockets:
            # Send the client list to the requesting client
            client_socket.send(f"update:{client_list_str}".encode('utf-8'))

    except Exception as e:
        print(f"Error sending client list: {e}")

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)

    print(f"Server listening on {HOST}:{PORT}")

    def accept_clients():
        while True:
            client_socket, addr = server.accept()
            print(f"Accepted connection from {addr}")

            name_in_use = True

            while name_in_use:
                # Receive the client name from the client
                client_name = client_socket.recv(1024).decode('utf-8')

                with lock:
                    if client_name not in clients:
                        # Add the new client to the dictionary
                        clients[client_name] = (client_socket, addr)
                        name_in_use = False

                if name_in_use is True:
                    client_socket.send(f"rejected: Rejected connection because the alias is being used".encode('utf-8'))

            # Start a new thread to handle the client
            client_handler = threading.Thread(target=handle_client, args=(client_socket, client_name))
            client_handler.start()

            client_socket.send(f"accepted: Accepted connection".encode('utf-8'))
                
            send_client_list_all()
            

    # Start a separate thread to accept clients
    accept_thread = threading.Thread(target=accept_clients)
    accept_thread.start()

    try:
        while True:
            pass  
    except KeyboardInterrupt:
        print("Server shutting down.")
    finally:
        server.close()

if __name__ == "__main__":
    main()
