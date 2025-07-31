"""
模块名: tcp_blocking

提供阻塞式 TCP 客户端/服务端接口，带消息长度前缀（默认 4 字节）。
支持直接发送和接收 torch.Tensor。
可在其他项目中通过 `import tcp_blocking` 或 `from tcp_blocking import TCPServer, TCPClient` 调用。
"""

import socket
import threading
import io
try:
    import torch
except ImportError:
    torch = None


def send_all(sock: socket.socket, data: bytes):
    """阻塞式发送完整数据"""
    total_sent = 0
    length = len(data)
    while total_sent < length:
        sent = sock.send(data[total_sent:])
        if sent == 0:
            raise RuntimeError("Socket connection broken during send")
        total_sent += sent


def recv_all(sock: socket.socket, size: int) -> bytes:
    """阻塞式接收指定长度的数据"""
    chunks = []
    bytes_recd = 0
    while bytes_recd < size:
        chunk = sock.recv(min(size - bytes_recd, 2048))
        if not chunk:
            raise RuntimeError("Socket connection broken during recv")
        chunks.append(chunk)
        bytes_recd += len(chunk)
    return b"".join(chunks)


class TCPServer:
    """
    阻塞式 TCP 服务端

    示例:
        server = TCPServer('0.0.0.0', 50007)
        server.register()
        tensor = server.recv_tensor()
        server.send_tensor(tensor)
        server.close()
    """
    def __init__(self, host: str, port: int, backlog: int = 4, prefix_size: int = 1):
        self.host = host
        self.port = port
        self.backlog = backlog
        self.prefix_size = prefix_size
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn = None
        self.addr = None

    def register(self):
        """绑定并接受第一个客户端连接"""
        self.sock.bind((self.host, self.port))
        self.sock.listen(self.backlog)
        self.conn, self.addr = self.sock.accept()

    def send(self, data: bytes):
        """发送原始字节数据，自动附加长度前缀"""
        prefix = len(data).to_bytes(self.prefix_size, 'big')
        send_all(self.conn, prefix + data)

    def recv(self) -> bytes:
        """接收原始字节数据，自动读取长度前缀并返回完整数据"""
        raw_len = recv_all(self.conn, self.prefix_size)
        size = int.from_bytes(raw_len, 'big')
        return recv_all(self.conn, size)

    def send_tensor(self, tensor):
        """直接发送 torch.Tensor 对象"""
        if torch is None:
            raise ImportError("torch 未安装，无法发送 tensor")
        buf = io.BytesIO()
        torch.save(tensor, buf)
        payload = buf.getvalue()
        self.send(payload)

    def recv_tensor(self):
        """直接接收 torch.Tensor 对象"""
        if torch is None:
            raise ImportError("torch 未安装，无法接收 tensor")
        raw = self.recv()
        buf = io.BytesIO(raw)
        buf.seek(0)
        return torch.load(buf)

    def close(self):
        """关闭连接和监听 socket"""
        if self.conn:
            self.conn.close()
        self.sock.close()


class TCPClient:
    """
    阻塞式 TCP 客户端

    示例:
        client = TCPClient('server_ip', 50007)
        client.register()
        client.send_tensor(torch.tensor([1,2,3]))
        tensor = client.recv_tensor()
        client.close()
    """
    def __init__(self, host: str, port: int, prefix_size: int = 1):
        self.host = host
        self.port = port
        self.prefix_size = prefix_size
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def register(self):
        """连接到服务端"""
        self.sock.connect((self.host, self.port))

    def send(self, data: bytes):
        """发送原始字节数据，自动附加长度前缀"""
        prefix = len(data).to_bytes(self.prefix_size, 'big')
        send_all(self.sock, prefix + data)

    def recv(self) -> bytes:
        """接收原始字节数据，自动读取长度前缀并返回完整数据"""
        raw_len = recv_all(self.sock, self.prefix_size)
        size = int.from_bytes(raw_len, 'big')
        return recv_all(self.sock, size)

    def send_tensor(self, tensor):
        """直接发送 torch.Tensor 对象"""
        if torch is None:
            raise ImportError("torch 未安装，无法发送 tensor")
        buf = io.BytesIO()
        torch.save(tensor, buf)
        payload = buf.getvalue()
        self.send(payload)

    def recv_tensor(self):
        """直接接收 torch.Tensor 对象"""
        if torch is None:
            raise ImportError("torch 未安装，无法接收 tensor")
        raw = self.recv()
        buf = io.BytesIO(raw)
        buf.seek(0)
        return torch.load(buf)

    def close(self):
        """关闭 socket"""
        self.sock.close()


# 如果直接运行此模块，会输出 tensor 发送/接收示例流程
if __name__ == '__main__':
    if torch is None:
        print('请先安装 torch')
    else:
        server = TCPServer('127.0.0.1', 50007)
        client = TCPClient('127.0.0.1', 50007)

        def srv():
            server.register()
            tensor = server.recv_tensor()
            print('Server received tensor:', tensor)
            server.send_tensor(tensor * 2)
            server.close()

        threading.Thread(target=srv, daemon=True).start()

        client.register()
        t = torch.arange(5)
        client.send_tensor(t)
        resp = client.recv_tensor()
        print('Client received tensor:', resp)
        client.close()
