#pylint: disable=wrong-import-position, attribute-defined-outside-init
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from unittest.mock import MagicMock
import pytest
from album_rsync.google_storage import GoogleStorage
from album_rsync.folder import Folder, RootFolder

class TestGoogleStorage:

    def setup_method(self):
        self.config = MagicMock()
        self.config.include = ''
        self.config.exclude = ''
        self.config.include_dir = ''
        self.config.exclude_dir = ''
        self.api = MagicMock()

    @pytest.fixture
    def folders_fixture(self):
        return [
            {
                'id': '123',
                'title': 'Folder 1'
            },
            {
                'id': '456',
                'title': 'Folder 2'
            }]

    def test_list_folders_should_return_folders_given_there_are_folders(self, folders_fixture):
        self.api.list_albums.return_value = folders_fixture
        storage = GoogleStorage(self.config, self.api)
        folders = list(storage.list_folders())

        assert len(folders) == 2

    def test_list_folders_should_not_list_folder_given_its_excluded(self, folders_fixture):
        self.config.exclude_dir = 'Folder 1'
        self.api.list_albums.return_value = folders_fixture
        storage = GoogleStorage(self.config, self.api)
        folders = list(storage.list_folders())

        assert len(folders) == 1
        assert folders[0].name == 'Folder 2'

    def test_list_folders_should_not_list_folder_given_its_not_included(self, folders_fixture):
        self.config.include_dir = 'Folder 1'
        self.api.list_albums.return_value = folders_fixture
        storage = GoogleStorage(self.config, self.api)
        folders = list(storage.list_folders())

        assert len(folders) == 1
        assert folders[0].name == 'Folder 1'

    def test_list_folders_should_return_nothing_given_there_are_no_folders(self):
        self.api.list_albums.return_value = []
        storage = GoogleStorage(self.config, self.api)
        folders = list(storage.list_folders())

        assert not folders

    @pytest.fixture
    def files_fixture(self):
        return [
            {
                'id': '123',
                'filename': 'image1.jpg',
                'baseUrl': 'https://example.com'
            },
            {
                'id': '456',
                'filename': 'image2.jpg',
                'baseUrl': 'https://example.com'
            }]

    def test_list_files_should_return_files_given_there_are_files(self, files_fixture):
        self.api.get_media_in_folder.return_value = files_fixture
        storage = GoogleStorage(self.config, self.api)
        folder = Folder(id=123, name='test')
        files = list(storage.list_files(folder))

        assert len(files) == 2

    def test_list_files_should_raise_not_implemented_when_root_folder_is_passed(self):
        storage = GoogleStorage(self.config, self.api)
        folder = RootFolder()
        with pytest.raises(NotImplementedError):
            _ = list(storage.list_files(folder))

    def test_list_files_should_not_list_file_given_its_excluded(self, files_fixture):
        self.config.exclude = 'image1'
        self.api.get_media_in_folder.return_value = files_fixture
        storage = GoogleStorage(self.config, self.api)
        folder = Folder(id=123, name='test')
        files = list(storage.list_files(folder))

        assert len(files) == 1
        assert files[0].name == 'image2.jpg'

    def test_list_files_should_not_list_file_given_its_not_included(self, files_fixture):
        self.config.include = 'image1'
        self.api.get_media_in_folder.return_value = files_fixture
        storage = GoogleStorage(self.config, self.api)
        folder = Folder(id=123, name='test')
        files = list(storage.list_files(folder))

        assert len(files) == 1
        assert files[0].name == 'image1.jpg'

    def test_list_files_should_not_list_files_given_there_are_no_files(self):
        self.api.get_media_in_folder.return_value = []
        storage = GoogleStorage(self.config, self.api)
        folder = Folder(id=123, name='test')
        files = list(storage.list_files(folder))

        assert not files

    def test_upload_should_not_fetch_folder_given_its_cached(self, folders_fixture):
        self.api.list_albums.return_value = folders_fixture
        storage = GoogleStorage(self.config, self.api)
        _ = list(storage.list_folders())
        folder = folders_fixture[0]
        storage.upload('/', folder['title'], 'micky.jpg', None)

        self.api.list_albums.assert_called_once()
        self.api.create_album.assert_not_called()
        self.api.upload.assert_called_once_with('/', 'micky.jpg', folder['id'])

    def test_upload_should_fetch_folder_given_its_not_cached(self, folders_fixture):
        self.api.list_albums.return_value = folders_fixture
        storage = GoogleStorage(self.config, self.api)
        folder = folders_fixture[0]
        storage.upload('/', folder['title'], 'micky.jpg', None)

        self.api.list_albums.assert_called_once()
        self.api.create_album.assert_not_called()
        self.api.upload.assert_called_once_with('/', 'micky.jpg', folder['id'])

    def test_upload_should_create_folder_given_it_doesnt_exist(self, folders_fixture):
        self.api.list_albums.return_value = []
        self.api.create_album.return_value = folders_fixture[0]
        storage = GoogleStorage(self.config, self.api)
        folder = folders_fixture[0]
        storage.upload('/', folder['title'], 'micky.jpg', None)

        self.api.list_albums.assert_called_once()
        self.api.create_album.assert_called_once()
        self.api.upload.assert_called_once_with('/', 'micky.jpg', folder['id'])
