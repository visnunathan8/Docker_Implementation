from ctypes.wintypes import SIZE
from pickle import GLOBAL
import socket
import random
from threading import Thread
import os
import shutil
from pathlib import Path
import string
import random
import shutil
import threading
from tkinter import E
import sys


SIZE = 1024
SIZE_OF_TOKEN = 8
GLOBAL_PATH = os.getcwd()


def get_working_directory_info(working_directory):
    """
    Creates a string representation of a working directory and its contents.
    :param working_directory: path to the directory
    :return: string of the directory and its contents.
    """
    dirs = '\n-- ' + '\n-- '.join([i.name for i in Path(working_directory).iterdir() if i.is_dir()])
    files = '\n-- ' + '\n-- '.join([i.name for i in Path(working_directory).iterdir() if i.is_file()])
    dir_info = f'Current Directory: {working_directory}:\n|{dirs}{files}'
    return dir_info


def generate_random_eof_token():
    """Helper method to generates a random token that starts with '<' and ends with '>'.
     The total length of the token (including '<' and '>') should be 10.
     Examples: '<1f56xc5d>', '<KfOVnVMV>'
     return: the generated token.
     """
    eof_token = ''.join(random.choices(string.ascii_uppercase + string.digits, k=SIZE_OF_TOKEN))
    eof_token = "<"+str(eof_token)+">"
    return eof_token


def receive_message_ending_with_token(active_socket, buffer_size, eof_token):
    """
    Same implementation as in receive_message_ending_with_token() in client.py
    A helper method to receives a bytearray message of arbitrary size sent on the socket.
    This method returns the message WITHOUT the eof_token at the end of the last packet.
    :param active_socket: a socket object that is connected to the server
    :param buffer_size: the buffer size of each recv() call
    :param eof_token: a token that denotes the end of the message.
    :return: a bytearray message with the eof_token stripped from the end.
    """
    final_message = bytearray()
    while True:
        message = active_socket.recv(buffer_size)
        if len(message) == 0:
            final_message += message
            break
        if message[-10:] == eof_token.encode():
            final_message += message[:-10]
            break
        final_message += message
    return final_message


def handle_cd(current_working_directory, new_working_directory):
    """
    Handles the client cd commands. Reads the client command and changes the current_working_directory variable 
    accordingly. Returns the absolute path of the new current working directory.
    :param current_working_directory: string of current working directory
    :param new_working_directory: name of the sub directory or '..' for parent
    :return: absolute path of new current working directory
    """
    
    try:
        os.chdir((os.path.join(current_working_directory, new_working_directory)).encode())
    except:
        return "[IMPROPER] The given file/directory is not valid"
    if (new_working_directory != "..") and (new_working_directory != "../"):
        path =  os.path.join(current_working_directory, new_working_directory)
    else :
        length = len(current_working_directory)
        if (new_working_directory == "../"):
            slicedlength = current_working_directory[:-1].rfind('/')
        else :
            slicedlength = current_working_directory.rfind('/')
        path = current_working_directory[:-(length-slicedlength)]
    return path
    
    


def handle_mkdir(current_working_directory, directory_name):
    """
    Handles the client mkdir commands. Creates a new sub directory with the given name in the current working directory.
    :param current_working_directory: string of current working directory
    :param directory_name: name of new sub directory
    """
    path =  os.path.join(current_working_directory, directory_name)
    print(path)
    try:
        os.mkdir(path)
    except:
        return "[IMPROPER] The given file/directory is not valid"

    return "Created successfully"


def handle_rm(current_working_directory, object_name):
    """
    Handles the client rm commands. Removes the given file or sub directory. Uses the appropriate removal method
    based on the object type (directory/file).
    :param current_working_directory: string of current working directory
    :param object_name: name of sub directory or file to remove
    """
    path =  os.path.join(current_working_directory, object_name)
    try:
        if(os.path.isfile(path)):
            os.remove(path)
        elif(os.path.isdir(path)):
            shutil.rmtree(path)
        else:
            return "[IMPROPER] The given file/directory is not valid".encode()
    except:
        return "[IMPROPER] The given file/directory is not valid".encode()
    return "Removed successfully".encode()


def handle_ul(current_working_directory, file_name, service_socket, eof_token):
    """
    Handles the client ul commands. First, it reads the payload, i.e. file content from the client, then creates the
    file in the current working directory.
    Use the helper method: receive_message_ending_with_token() to receive the message from the client.
    :param current_working_directory: string of current working directory
    :param file_name: name of the file to be created.
    :param service_socket: active socket with the client to read the payload/contents from.
    :param eof_token: a token to indicate the end of the message.
    """
    service_socket.sendall(("Uploading on progress..."+eof_token).encode())
    file = open(file_name, "wb") 
    value = receive_message_ending_with_token(service_socket, SIZE, eof_token)
    file.write(value)
    service_socket.sendall(("File uploaded successfully\n"+get_working_directory_info(current_working_directory)+eof_token).encode())

def handle_dl(current_working_directory, file_name, service_socket, eof_token):
    """
    Handles the client dl commands. First, it loads the given file as binary, then sends it to the client via the
    given socket.
    :param current_working_directory: string of current working directory
    :param file_name: name of the file to be sent to client
    :param service_socket: active service socket with the client
    :param eof_token: a token to indicate the end of the message.
    """
    file_data = open(file_name, "rb").read()
    service_socket.sendall(file_data[:len(file_data)-1]+eof_token.encode())
    value = receive_message_ending_with_token(service_socket, SIZE, eof_token)
    print(value.decode())
    service_socket.sendall((get_working_directory_info(current_working_directory)+eof_token).encode())


class ClientThread(Thread):
    localVal = threading.local()

    def __init__(self, service_socket : socket.socket, address : str, path : str):
        Thread.__init__(self)
        self.service_socket = service_socket
        self.address = address
        self.path = path

    def run(self):
        print ("[CONNECTING] Connection from : ", self.address)

        # initialize the connection
        eof_token = generate_random_eof_token()

        # send random eof token
        self.service_socket.sendall(eof_token.encode())

        # establish working directory
        self.localVal.path = self.path

        # send the current dir info
        self.service_socket.sendall((get_working_directory_info(self.localVal.path)).encode()+" ".encode()+eof_token.encode())
        exit = False
        while True:
            
            # get the command and arguments and call the corresponding method
            dataValue = receive_message_ending_with_token(self.service_socket, SIZE, eof_token)
            command = dataValue.decode()
            current_dir = self.localVal.path
            if command[:2].lower() == "cd".lower() :
                new_dir = command[3:]
                new_dir = new_dir.replace(current_dir, "")
                new_cd = handle_cd(current_dir, new_dir)
                if(new_cd == "[IMPROPER] The given file/directory is not valid") :
                    self.service_socket.sendall((new_cd+"\n"+get_working_directory_info(current_dir)+eof_token).encode())
                else :
                    current_dir = new_cd
                    self.localVal.path = new_cd
                    self.service_socket.sendall((get_working_directory_info(new_cd)+eof_token).encode())
            elif command[:2].lower() == "rm".lower() :
                remove_data = handle_rm(current_dir, command[3:])
                if(remove_data.decode() == "[IMPROPER] The given file/directory is not valid") :
                    self.service_socket.sendall(remove_data+("\n"+get_working_directory_info(current_dir)+eof_token).encode())
                else :
                    self.service_socket.sendall(remove_data+(eof_token).encode())
            elif command[:2].lower() == "ul".lower() :
                handle_ul(current_dir, command[3:], self.service_socket, eof_token)
            elif command[:2].lower() == "dl".lower() :
                handle_dl(current_dir, command[3:], self.service_socket, eof_token)
            elif command[:5].lower() == "mkdir".lower() :
                mkdir_data = handle_mkdir(current_dir, command[6:])
                if(mkdir_data == "[IMPROPER] The given file/directory is not valid") :
                    self.service_socket.sendall((mkdir_data+"\n"+get_working_directory_info(current_dir)+eof_token).encode())
                else :
                    self.service_socket.sendall((mkdir_data+"\n"+get_working_directory_info(current_dir)+eof_token).encode())
            elif command[:4].lower() == "exit".lower() :
                exit = True
            else :
                exit = True

            if exit:
                break;
        self.service_socket.close()
        print('[CLOSING] Connection closed from:', self.address)
            
        # send current dir info
        

        


def main():
    HOST = "172.18.0.2"
    PORT = 50444

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        print("[STARTING] Server is starting.....\n")
        s.bind((HOST, PORT))
        s.listen()
        print("[LISTENING] Server is listening on "+str(HOST)+":"+str(PORT)+"\n")
        while True:
            conn, addr = s.accept()
            client_thread = ClientThread(conn, addr, GLOBAL_PATH)
            client_thread.start()
            print("[ACTIVE CONNECTIONS]"+str(threading.activeCount()-1))


if __name__ == '__main__':
    main()


