class AudioElement:
    def __init__(self, path: str, start: float, volume: float):
        self._path = path
        self._start = start
        self._volume = volume

    @property
    def path(self):
        return self._path
    
    @property
    def start(self):
        return self._start

    @property
    def volume(self):
        return self._volume
