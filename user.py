import tkinter as tk
from tkinter import scrolledtext
import socket
import threading
import sys
from datetime import datetime

HOST = '127.0.0.1'
PORT = 5556

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def set_connection():
    client.connect((HOST, PORT))

    # Start a separate thread to receive messages
    receive_thread = threading.Thread(target=receive_messages, args=(client,))
    receive_thread.start()

def hide_list_clients(): 
    label_list.pack_forget()
    connected_user_label.pack_forget()
    listbox.pack_forget()

def hide_login(): 
    label_user.pack_forget()
    entry_user.pack_forget()
    submit_user.pack_forget()
    label_user_error.pack_forget()

def hide_chat():
    selected_user_label.pack_forget()
    frame_chat.pack_forget()
    frame_entry_message.pack_forget()
    
def show_login():
    label_user.pack(pady=(100,10))
    entry_user.pack(ipady=5)
    submit_user.pack(pady=40)
    
def show_chat(event):
    global selected_name
    selected_index = listbox.curselection()[0]
    selected_name = listbox.get(selected_index)
    if selected_name:
        hide_list_clients()
        selected_user_label.config(text=selected_name)
        selected_user_label.pack(padx=10,pady=10)
        frame_chat.pack(padx=25, pady=10)
        frame_entry_message.pack(padx=25, pady=10)
        send_button.config(state=tk.NORMAL)
        listbox.itemconfig(selected_index, {'bg': 'white'})
        load_chat(selected_name)
    else:
        label_user.config(text="Please select a name.")

def show_list_clients():
    label_list.config(text=f"Hello, {username}!")
    label_list.pack(pady=20)
    connected_user_label.pack()
    listbox.pack(pady=10)

def ask_for_other_alias():
    label_user_error.pack(pady=10)
    label_user_error.configure(text="The alias you entered is being used. Please choose another")

def get_username():
    global username
    username = entry_user.get()
    if username:
        # Send the client name to the server
        client.send(username.encode('utf-8'))
        # hide_login()
        # show_list_clients()
    else:
        label_user_error.pack(pady=10)
        label_user_error.configure(text="Please enter an alias")
        
def parse_message(data):
    # Split the message into message type and data
    parts = data.split(':')
    if len(parts) == 2:
        return parts[0], parts[1]
    else:
        return None, None
        
def receive_messages(client_socket):
    try:
        while True:
            data = client_socket.recv(1024)
            if not data:
                break

            message = parse_message(data.decode('utf-8'))
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            if message[0] == "update":
                update_client_list(message[1])
            elif message[0] == "rejected":
                ask_for_other_alias()
            elif message[0] == "accepted":
                hide_login()
                show_list_clients()
            else:
                if message[0] == selected_name:
                    chat_display.insert(tk.END, f"{timestamp} - {message[0]}: {message[1]}\n")
                else: 
                    unread_message(names.index(message[0]))
                save_chat(message[0], message[1], timestamp)
    except Exception as e:
        print(f"Error receiving messages: {e}")
    finally:
        client_socket.close()
        
def load_chat(user):
    chat_display.delete(1.0, tk.END)
    
    # Display entire chat history for the user
    if user in user_chats:
        for message in user_chats[user]:
            chat_display.insert(tk.END, message)
        
def save_chat(user, message, time, me=False):
    global user_chats
    # Check if user exists in the dictionary, if not, create an entry
    if user not in user_chats:
        user_chats[user] = []
    
    # Update chat display, save chat history, and display entire chat history
    if me is True:     
        user_chats[user].append(f"{time} - You: {message}\n")
    else:
        user_chats[user].append(f"{time} - {user}: {message}\n")
           
def send_message():
    message = entry_message.get()
    if message:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        if selected_name not in names: 
            chat_display.insert(tk.END, f"{timestamp} - You: {message}\n", 'error')
            chat_display.insert(tk.END, "\nThe message was not sent because the destination user has disconnected", 'error')
            chat_display.tag_config('error', foreground='red')
            entry_message.delete(0, tk.END)
            send_button.config(state=tk.DISABLED)
        else: 
            try:
            # Send the message to the server
                client.send(f"{selected_name}:{message}".encode('utf-8'))
                chat_display.insert(tk.END, f"{timestamp} - You: {message}\n")
                save_chat(selected_name, message, timestamp, True)
                entry_message.delete(0, tk.END)
            except Exception as e:
                print(f"Error sending message: {e}")
            
def unread_message(user_index):
    listbox.itemconfig(user_index, {'bg': '#7CFC00'})

def update_client_list(list_clients):
    global names 
    all_names = list(list_clients.split(' '))
    names = [x for x in all_names if x != username]
    listbox.delete(0,tk.END)
    for name in names:
        listbox.insert(tk.END, name)
        
def back_to_list():
    global selected_name
    selected_name = ""
    listbox.selection_clear(0, tk.END)
    hide_chat()
    show_list_clients()
    
def on_closing():
    client.close()
    window.destroy()
    sys.exit()

# Create the main window
window = tk.Tk()
window.title("ChattingApp")
window.geometry('500x400')
window.tk_setPalette(background='#FFFFFF', foreground='#000000')

# Variables 
username = ""
selected_name = ""
names = []
user_chats = {}

# Constants
LIST_WIDHT= 25
ENTRY_WIDHT = 30
BUTTON_WIDTH = 13
FONT_MEDIUM = ("Courier", 15)
FONT_SMALL = ("Courier", 11)

# Login elements
label_user = tk.Label(window, text="Choose an alias:", font=FONT_MEDIUM)
entry_user = tk.Entry(window, width=ENTRY_WIDHT, font=FONT_SMALL)
submit_user = tk.Button(window, text="Submit", command=get_username, width=BUTTON_WIDTH, font=FONT_MEDIUM)
label_user_error = tk.Label(window, font=FONT_SMALL, fg="red")

# Client List elements
label_list = tk.Label(window, font=FONT_MEDIUM)
connected_user_label = tk.Label(window, text="Connected users", font=FONT_SMALL)
listbox = tk.Listbox(window, selectmode=tk.SINGLE, exportselection=False, takefocus=False, font=FONT_MEDIUM, width=LIST_WIDHT)
listbox.bind("<<ListboxSelect>>", show_chat)  # Bind the click event

# Chat elements
selected_user_label = tk.Label(window, font=FONT_MEDIUM)
frame_chat = tk.Frame(window, bd=2, relief=tk.GROOVE)
chat_display = scrolledtext.ScrolledText(frame_chat, wrap=tk.WORD, height=20)
chat_display.pack()
frame_entry_message = tk.Frame(window, relief=tk.GROOVE)
entry_message = tk.Entry(frame_entry_message, font=FONT_SMALL, width=40)
send_button = tk.Button(frame_entry_message, text="Send", command=send_message, font=FONT_SMALL, width=10)
back_button = tk.Button(frame_entry_message, text="Back", command=back_to_list, font=FONT_SMALL, width=10)
entry_message.pack(side=tk.LEFT, ipady=4)
back_button.pack(side=tk.RIGHT, ipady=5)
send_button.pack(side=tk.RIGHT, ipady=5)
window.bind("<Return>", lambda event=None: send_message()) # Bind the Enter key to the send_message function
# Set the protocol for the main window
window.protocol("WM_DELETE_WINDOW", on_closing)

def main():
    show_login()

    set_connection()

    try:
        while True:
            window.mainloop()
            
    except KeyboardInterrupt:
        print("Client shutting down.")
    finally:
        client.close()

if __name__ == "__main__":
    main()
