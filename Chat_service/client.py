from tkinter import Tk, Frame, Scrollbar, Label, END, Entry, Text, VERTICAL, Button
import socket
import threading
import json
from tkinter import messagebox


class Client:
    # Define socket host and port
    SERVER_HOST = '127.0.0.1'
    SERVER_PORT = 8000
    is_running = None
    client_socket = None

    def __init__(self, master):
        self.root = master
        self.chat_transcript_area = None
        self.rooms_transcript_area = None
        self.name_widget = None
        self.enter_text_widget = None
        self.join_button = None
        self.initialize_socket()
        self.initialize_gui()
        self.listen_for_incoming_messages_in_a_thread()

    def initialize_socket(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.SERVER_HOST, self.SERVER_PORT))

    def initialize_gui(self):
        self.root.title("Socket Chat")
        self.root.resizable(0, 0)
        self.display_room_list()
        self.display_chat_box()
        self.display_name_section()
        self.display_chat_entry_box()

    def listen_for_incoming_messages_in_a_thread(self):
        self.is_running = True
        thread = threading.Thread(target=self.receive_message_from_server, args=(self.client_socket,))
        thread.start()

    def receive_message_from_server(self, so):
        while self.is_running:
            buffer = so.recv(256)
            if not buffer:
                break
            message = buffer.decode('utf-8')
            print(message)
            if "Welcome" in message:
                self.clear_chat()
                self.chat_transcript_area.insert('end', message + '\n', "server")
                self.chat_transcript_area.yview(END)
            elif "Commands available" in message:
                self.clear_chat()
                self.chat_transcript_area.insert('end', message + '\n', "server")
                self.chat_transcript_area.yview(END)
            elif "NameExist" in message:
                message = message.split(":")[1]
                self.name_widget.config(state='normal')
                self.enter_text_widget.config(state='disabled')
                self.chat_transcript_area.insert('end', message + '\n', "warning")
                self.chat_transcript_area.yview(END)
            elif "Server" in message:
                message = message.split(":")[1]
                self.chat_transcript_area.insert('end', message + '\n', "server")
                self.chat_transcript_area.yview(END)
            elif "Error" in message:
                message = message.split(":")[1]
                self.chat_transcript_area.insert('end', message + '\n', "erro")
                self.chat_transcript_area.yview(END)
            elif "Ban" in message or "Kick" in message or "leftRoom" in message:
                message = message.split(":")[1]
                self.chat_transcript_area.insert('end', message + '\n', "warning")
                self.chat_transcript_area.yview(END)
            elif "Clear" in message:
                self.clear_chat()
            elif '["#geral"' in message:
                self.rooms_transcript_area.delete('1.0', END)
                list = json.loads(message)
                print(list)
                for i in list:
                    self.rooms_transcript_area.insert('end', i + '\n')
                self.rooms_transcript_area.yview(END)
            else:
                self.chat_transcript_area.insert('end', message + '\n')
                self.chat_transcript_area.yview(END)
        so.close()

    def display_chat_box(self):
        frame = Frame()
        Label(frame, text='Chat Box:', font=("Serif", 12)).pack(side='top', anchor='w')
        self.chat_transcript_area = Text(frame, width=60, height=10, font=("Serif", 12))
        scrollbar = Scrollbar(frame, command=self.chat_transcript_area.yview, orient=VERTICAL)
        self.chat_transcript_area.config(yscrollcommand=scrollbar.set)
        self.chat_transcript_area.tag_config('warning', background="yellow", foreground="red")
        self.chat_transcript_area.tag_config('server', foreground="green")
        self.chat_transcript_area.tag_config('erro', foreground="red")
        self.chat_transcript_area.bind('<KeyPress>', lambda e: 'break')
        self.chat_transcript_area.pack(side='left', padx=10)
        scrollbar.pack(side='right', fill='y')
        frame.pack(side='top')

    def display_name_section(self):
        frame = Frame()
        Label(frame, text='Enter your name:', font=("Helvetica", 14)).pack(side='left', padx=10)
        self.name_widget = Entry(frame, width=30, borderwidth=2)
        self.name_widget.pack(side='left', anchor='e')
        self.join_button = Button(frame, text="Join", width=10, command=self.on_join).pack(side='left')
        frame.pack(side='top', anchor='nw')

    def display_chat_entry_box(self):
        frame = Frame()
        Label(frame, text='Enter message:', font=("Serif", 12)).pack(side='top', anchor='w')
        self.enter_text_widget = Text(frame, width=60, height=3, state='disabled', font=("Serif", 12))
        self.enter_text_widget.pack(side='left', pady=15)
        self.enter_text_widget.bind('<Return>', self.on_enter_key_pressed)
        frame.pack(side='top')

    def display_room_list(self):
        frame = Frame()
        Label(frame, text='Room List:', font=("Serif", 12)).pack(padx=5, side='top', anchor='w')
        self.rooms_transcript_area = Text(frame, width=10, height=20, font=("Serif", 12))
        scrollbar = Scrollbar(frame, command=self.rooms_transcript_area.yview, orient=VERTICAL)
        self.rooms_transcript_area.config(yscrollcommand=scrollbar.set)
        self.rooms_transcript_area.bind('<KeyPress>', lambda e: 'break')
        self.rooms_transcript_area.pack(side='right', padx=10)
        frame.pack(side='right', anchor='nw')

    def on_join(self):
        if len(self.name_widget.get()) == 0:
            messagebox.showerror(
                "Enter your name", "Enter your name to send a message")
            return
        self.name_widget.config(state='disabled')
        self.client_socket.sendall((self.name_widget.get()).encode('utf-8'))
        self.enter_text_widget.config(state='normal')

    def on_enter_key_pressed(self, event):
        if len(self.name_widget.get()) == 0:
            messagebox.showerror(
                "Enter your name", "Enter your name to send a message")
            return
        self.send_chat()
        self.clear_text()

    def clear_text(self):
        self.enter_text_widget.delete(1.0, 'end')

    def clear_chat(self):
        self.chat_transcript_area.delete(1.0, 'end')

    def send_chat(self):
        senders_name = self.name_widget.get().strip() + ": "
        data = self.enter_text_widget.get(1.0, 'end').strip()
        message = (senders_name + data).encode('utf-8')
        self.chat_transcript_area.insert('end', message.decode('utf-8') + '\n')
        self.chat_transcript_area.yview(END)
        self.client_socket.send(message)
        self.enter_text_widget.delete(1.0, 'end')
        return 'break'

    def on_close_window(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.root.destroy()
            self.client_socket.close()
            exit(0)


if __name__ == '__main__':
    root = Tk()
    client = Client(root)
    root.protocol("WM_DELETE_WINDOW", client.on_close_window)
    root.mainloop()