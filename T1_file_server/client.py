import socket
import os
import sys
SIZE = 1024

eof_token = ""
def receive_message_ending_with_token(active_socket, buffer_size, eof_token):
    """
    Same implementation as in receive_message_ending_with_token() in server.py
    A helper method to receives a bytearray message of arbitrary size sent on the socket.
    This method returns the message WITHOUT the eof_token at the end of the last packet.
    :param active_socket: a socket object that is connected to the server
    :param buffer_size: the buffer size of each recv() call
    :param eof_token: a token that denotes the end of the message.
    :return: a bytearray message with the eof_token stripped from the end.
    """
    final_message = bytes(b'')
    while True:
        message = active_socket.recv(buffer_size)
        if(eof_token.encode() in message):#or message.endswith(eof_token)) :
            val = message.decode()
            val = val[:len(message)-10]
            final_message += val.encode()
            break;
        final_message += message
    return final_message   


def initialize(host, port):
    """
    1) Creates a socket object and connects to the server.
    2) receives the random token (10 bytes) used to indicate end of messages.
    3) Displays the current working directory returned from the server (output of get_working_directory_info() at the server).
    Use the helper method: receive_message_ending_with_token() to receive the message from the server.
    :param host: the ip address of the server
    :param port: the port number of the server
    :return: the created socket object
    """

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    print('[CONNECTED] Client Connected to server at IP:', host, 'and Port:', port)
    global eof_token
    eof_token = s.recv(SIZE).decode()
    print('Handshake Done. EOF is:', eof_token)

    curent_working_directory = receive_message_ending_with_token(s, SIZE, eof_token)
    print(curent_working_directory.decode())

    return s


def issue_cd(command_and_arg, client_socket, eof_token):
    """
    Sends the full cd command entered by the user to the server. The server changes its cwd accordingly and sends back
    the new cwd info.
    Use the helper method: receive_message_ending_with_token() to receive the message from the server.
    :param command_and_arg: full command (with argument) provided by the user.
    :param client_socket: the active client socket object.
    :param eof_token: a token to indicate the end of the message.
    """
    client_socket.sendall((command_and_arg+eof_token).encode())
    server_data = receive_message_ending_with_token(client_socket, SIZE, eof_token)
    print(server_data.decode())
        


def issue_mkdir(command_and_arg, client_socket, eof_token):
    """
    Sends the full mkdir command entered by the user to the server. The server creates the sub directory and sends back
    the new cwd info.
    Use the helper method: receive_message_ending_with_token() to receive the message from the server.
    :param command_and_arg: full command (with argument) provided by the user.
    :param client_socket: the active client socket object.
    :param eof_token: a token to indicate the end of the message.
    """
    client_socket.sendall((command_and_arg+eof_token).encode())
    server_data = receive_message_ending_with_token(client_socket, SIZE, eof_token)
    print(server_data.decode())


def issue_rm(command_and_arg, client_socket, eof_token):
    """
    Sends the full rm command entered by the user to the server. The server removes the file or directory and sends back
    the new cwd info.
    Use the helper method: receive_message_ending_with_token() to receive the message from the server.
    :param command_and_arg: full command (with argument) provided by the user.
    :param client_socket: the active client socket object.
    :param eof_token: a token to indicate the end of the message.
    """
    client_socket.sendall((command_and_arg+eof_token).encode())
    server_data = receive_message_ending_with_token(client_socket, SIZE, eof_token)
    print(server_data.decode())


def issue_ul(command_and_arg, client_socket, eof_token):
    """
    Sends the full ul command entered by the user to the server. Then, it reads the file to be uploaded as binary
    and sends it to the server. The server creates the file on its end and sends back the new cwd info.
    Use the helper method: receive_message_ending_with_token() to receive the message from the server.
    :param command_and_arg: full command (with argument) provided by the user.
    :param client_socket: the active client socket object.
    :param eof_token: a token to indicate the end of the message.
    """
    client_socket.sendall((command_and_arg+eof_token).encode())
    value = receive_message_ending_with_token(client_socket, SIZE, eof_token)
    print(value.decode())
    file_data = open(command_and_arg[command_and_arg.index(' ')+1:], "rb").read()
    file_data = file_data[:len(file_data)]+eof_token.encode()
    client_socket.sendall(file_data)
    server_data = receive_message_ending_with_token(client_socket, SIZE, eof_token)
    print(server_data.decode())


def issue_dl(command_and_arg, client_socket, eof_token):
    """
    Sends the full dl command entered by the user to the server. Then, it receives the content of the file via the
    socket and re-creates the file in the local directory of the client. Finally, it receives the latest cwd info from
    the server.
    Use the helper method: receive_message_ending_with_token() to receive the message from the server.
    :param command_and_arg: full command (with argument) provided by the user.
    :param client_socket: the active client socket object.
    :param eof_token: a token to indicate the end of the message.
    :return:
    """
    client_socket.sendall((command_and_arg+eof_token).encode())
    file = open(command_and_arg[3:], "wb")
    value = receive_message_ending_with_token(client_socket, SIZE, eof_token)
    file.write(value)
    client_socket.sendall(("Downloaded Successfully in client"+eof_token).encode());
    path = receive_message_ending_with_token(client_socket, SIZE, eof_token)
    print("Downloaded Successfully from the server")
    print(path.decode())


def main():
    HOST = "172.18.0.2"  # The server's hostname or IP address
    PORT = 50444 # The port used by the server


    # initialize
    socket = initialize(HOST, PORT)
    print("\n\nList of available Commands :\n 1. cd - (To change the directory) \n 2. rm - (To remove a file or directoy) \n 3. ul - (To upload the file to server) \n 4. dl - (To download a file from server) \n 5. mkdir - (To create a new directory)\n\n")
        
    while True:
        
        command_To_Be_Executed = input('Enter the command to be executed on the server...')
        if command_To_Be_Executed[:2].lower() == "cd".lower() :
            issue_cd(command_To_Be_Executed, socket, eof_token)
        elif command_To_Be_Executed[:2].lower() == "rm".lower() :
            issue_rm(command_To_Be_Executed, socket, eof_token)
        elif command_To_Be_Executed[:2].lower() == "ul".lower() :
            issue_ul(command_To_Be_Executed, socket, eof_token)
        elif command_To_Be_Executed[:2].lower() == "dl".lower() :
            issue_dl(command_To_Be_Executed, socket, eof_token)
        elif command_To_Be_Executed[:5].lower() == "mkdir".lower() :
            issue_mkdir(command_To_Be_Executed, socket, eof_token)
        elif command_To_Be_Executed[:4].lower() == "exit".lower() :
            print('[EXIT] Exiting the application.')
            break;
        else :
            print("[IMPROPER] Kindly Enter the proper command....")
        # server_path = receive_message_ending_with_token(socket, SIZE, eof_token)
        # print(server_path)
    socket.close()


if __name__ == '__main__':
    main()
