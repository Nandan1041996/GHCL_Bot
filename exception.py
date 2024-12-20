
class FileNotAvailable(Exception):
    'File Not Available.'
    def __init__(self):
        self.msg = 'File Not Available.'
    def __str__(self):
        return self.msg


