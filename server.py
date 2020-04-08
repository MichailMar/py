import asyncio
from asyncio import transports
from typing import Optional


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport
    last_ms: list = []

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        print(data)

        decoded = data.decode()

        if self.login is not None:
            self.send_message(decoded).replace("\r\n", "")
        else:
            if decoded.startswith("/login"):
                templogn = decoded.replace("/login", "").replace("\r\n", "")
                for user in self.server.clients:
                    if user.login == templogn:
                        self.transport.write(f"Логин {templogn} занят. Используйте другой!\r\n".encode())
                        break
                    else:
                        self.login = templogn
                        self.transport.write(f"Привет, {self.login}!\r\n".encode())
                        self.send_history()
                        break

            else:
                self.transport.write("Пожалуйста, введите логин\r\n".encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Новое подключение ")

    def connection_lost(self, exc: Optional[Exception]):
        self.server.clients.remove(self)
        print("Отключение")

    def send_history(self):
        for msg in self.last_ms:
            self.transport.write(f"{msg}".encode())

    def send_message(self, content: str):
        message = f"{self.login}: {content}\r\n"
        if len(self.last_ms) == 10:
            self.last_ms.pop(0)

        self.last_ms.append(message)

        for user in self.server.clients:
            user.transport.write(message.encode())


class Server:
    clients: list

    def __init__(self):
        self.clients = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        corountine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print("Сервер запущен...")

        await corountine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер выключен.")
