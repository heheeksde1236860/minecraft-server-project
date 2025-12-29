import requests
from PySide6 import QtCore


class UUIDFetcher(QtCore.QObject):
    finished = QtCore.Signal(str, str, str)

    def __init__(self, username, proxy=None):
        super().__init__()
        self.username = username
        self.proxy = proxy

    def run(self):
        try:
            url = f"https://playerdb.co/api/player/minecraft/{self.username}"
            proxies = None
            if self.proxy:
                proxies = {
                    "http": self.proxy,
                    "https": self.proxy,
                }
            response = requests.get(url, timeout=5, proxies=proxies)
            response.raise_for_status()
            data = response.json()
            
            if data["code"] == "player.found":
                uuid = data["data"]["player"]["id"]
                self.finished.emit(self.username, uuid, "")
            else:
                self.finished.emit(self.username, "", "Player not found")
                
        except Exception as e:
            self.finished.emit(self.username, "", str(e))


