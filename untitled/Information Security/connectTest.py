import socket

print(socket.gethostbyaddr("8.8.8.8"))
print(socket.gethostbyname("www.daum.net"))

host='192.168.110.116'
mysock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
addr=(host,8027)
mysock.connect(addr)

try:
    msg=b"This is a test\n"
    mysock.sendall(msg)
except socket.errno as e:
    print("Socket error ", e)
finally:
    mysock.close()