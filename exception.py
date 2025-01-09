
class FileNotAvailable(Exception):
    'File Not Available.'
    def __init__(self):
        self.msg = 'File Not Available in google drive.'
    def __str__(self):
        return self.msg
    

class FolderNotAvailable(Exception):
    'Folder Not Available.'
    def __init__(self):
        self.msg = 'In Google Drive Folder Not Available.'
    def __str__(self):
        return self.msg

    
class EmailExist(Exception):
    'Email already exist.'
    def __init__(self):
        self.msg = 'Email already exist.'
    def __str__(self):
        return self.msg


