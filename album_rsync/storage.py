import os
import re
from tempfile import NamedTemporaryFile
from abc import abstractmethod

class Storage:

    @abstractmethod
    def list_folders(self):
        pass

    @abstractmethod
    def list_files(self, folder):
        pass

    @abstractmethod
    def copy_file(self, file_, folder_name, dest_storage):
        pass

    @abstractmethod
    def delete_file(self, file_, folder_name):
        pass

    @abstractmethod
    def delete_folder(self, folder):
        pass

    @abstractmethod
    def logout(self):
        pass

    def mkdirp(self, path):
        """
        Creates all missing folders in the path

        Args:
            path: A file system path to create, may include a filename (ignored)
        """
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path), exist_ok=True)

    def _should_include(self, name, include_pattern, exclude_pattern):
        return ((not include_pattern or re.search(include_pattern, name, flags=re.IGNORECASE)) and
                (not exclude_pattern or not re.search(exclude_pattern, name, flags=re.IGNORECASE)))

class RemoteStorage(Storage):

    @abstractmethod
    def download(self, file_, dest):
        pass

    @abstractmethod
    def upload(self, src, folder_name, file_name, checksum):
        pass

    def copy_file(self, file_, folder_name, dest_storage):
        if isinstance(dest_storage, RemoteStorage):
            temp_file = NamedTemporaryFile()
            self.download(file_, temp_file.name)
            dest_storage.upload(temp_file.name, folder_name, file_.name, file_.checksum)
            temp_file.close()
        else:
            dest = os.path.join(dest_storage.path, folder_name, file_.name)
            self.download(file_, dest)
