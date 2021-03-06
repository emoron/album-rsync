# -*- coding: utf-8 -*-
#pylint: disable=wrong-import-position, attribute-defined-outside-init
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from unittest.mock import MagicMock, patch, call
import pytest
import tests.helpers
from album_rsync.tree_walker import TreeWalker
from album_rsync.file import File
from album_rsync.folder import Folder, RootFolder

class TestTreeWalker:

    def setup_method(self):
        self.print_patch = patch('album_rsync.tree_walker.print', create=True)
        self.mock_print = self.print_patch.start()
        self.logger_patch = patch('album_rsync.tree_walker.logger', create=True)
        self.mock_logger = self.logger_patch.start()
        self.time_patch = patch('album_rsync.tree_walker.time.time', create=True)
        self.time_patch.start().return_value = 0

        self.config = MagicMock()
        self.config.root_files = False
        self.config.list_folders = False
        self.config.list_sort = False
        self.storage = MagicMock()
        self.folder_one = Folder(id=1, name='A Folder')
        self.folder_two = Folder(id=2, name='B Folder')
        self.folder_three = Folder(id=3, name='C Folder')
        self.folder_four = Folder(id=4, name='D Folder')
        self.root_folder = RootFolder()
        self.file_one = File(id=1, name='A File')
        self.file_two = File(id=2, name='B File')
        self.file_three = File(id=3, name='C File', checksum='abc123')

    def teardown_method(self):
        self.print_patch.stop()
        self.logger_patch.stop()
        self.time_patch.stop()

    def test_should_print_wrapper_only_given_no_folders(self):
        walker = TreeWalker(self.config, self.storage)

        walker.walk()

        self.mock_print.assert_not_called()
        self.mock_logger.info.assert_called_once_with("0 directories, 0 files read in 0 sec")

    def test_should_print_wrapper_only_given_empty_folders(self):
        walker = TreeWalker(self.config, self.storage)
        tests.helpers.setup_storage(self.storage, [
            {'folder': self.root_folder, 'files': []},
            {'folder': self.folder_one, 'files': []}
        ])

        walker.walk()

        self.mock_print.assert_not_called()
        self.mock_logger.info.assert_called_once_with("0 directories, 0 files (excluding 1 empty directories) read in 0 sec")

    def test_should_print_root_files_given_root_files_enabled(self):
        self.config.root_files = True
        walker = TreeWalker(self.config, self.storage)
        tests.helpers.setup_storage(self.storage, [
            {'folder': self.root_folder, 'files': [self.file_one, self.file_two]}
        ])

        walker.walk()

        self.mock_print.assert_has_calls_exactly([
            call("├─── A File"),
            call("└─── B File")
        ])
        self.mock_logger.info.assert_called_once_with("0 directories, 2 files read in 0 sec")

    @pytest.mark.skip(reason="Ligitimately broken, I just don't have a good fix for it")
    def test_should_not_print_connector_when_printing_root_files_given_folders_are_hidden(self):
        self.config.root_files = True
        walker = TreeWalker(self.config, self.storage)
        tests.helpers.setup_storage(self.storage, [
            {'folder': self.root_folder, 'files': [self.file_one, self.file_two]},
            {'folder': self.folder_one, 'files': []}
        ])

        walker.walk()

        self.mock_print.assert_has_calls_exactly([
            call("├─── A File"),
            call("└─── B File")
        ])
        self.mock_logger.info.assert_called_once_with("0 directories, 2 files (excluding 1 empty directories) read in 0 sec")

    def test_should_not_print_root_files_given_root_files_disabled(self):
        self.config.root_files = False
        walker = TreeWalker(self.config, self.storage)
        tests.helpers.setup_storage(self.storage, [
            {'folder': self.root_folder, 'files': [self.file_one, self.file_two]}
        ])

        walker.walk()

        self.mock_print.assert_not_called()
        self.mock_logger.info.assert_called_once_with("0 directories, 0 files read in 0 sec")

    def test_should_print_root_files_given_root_files_enabled_and_folders_exist(self):
        self.config.root_files = True
        self.config.list_sort = False
        walker = TreeWalker(self.config, self.storage)
        tests.helpers.setup_storage(self.storage, [
            {'folder': self.root_folder, 'files': [self.file_three]},
            {'folder': self.folder_one, 'files': [self.file_one]}
        ])

        walker.walk()

        self.mock_print.assert_has_calls([
            call("├─── C File [abc123]"),
            call("│   "),
            call("└─── A Folder"),
            call("    └─── A File")
        ])
        self.mock_logger.info.assert_called_once_with("1 directories, 2 files read in 0 sec")

    def test_should_print_folder_files(self):
        walker = TreeWalker(self.config, self.storage)
        tests.helpers.setup_storage(self.storage, [
            {'folder': self.folder_one, 'files': [self.file_one, self.file_two]}
        ])

        walker.walk()

        self.mock_print.assert_has_calls([
            call("└─── A Folder"),
            call("    ├─── A File"),
            call("    └─── B File")
        ])
        self.mock_logger.info.assert_called_once_with("1 directories, 2 files read in 0 sec")

    def test_should_print_all_folders(self):
        walker = TreeWalker(self.config, self.storage)
        tests.helpers.setup_storage(self.storage, [
            {'folder': self.folder_one, 'files': [self.file_one]},
            {'folder': self.folder_two, 'files': [self.file_two]}
        ])

        walker.walk()

        self.mock_print.assert_has_calls([
            call("├─── A Folder"),
            call("│   └─── A File"),
            call("│   "),
            call("└─── B Folder"),
            call("    └─── B File")
        ])
        self.mock_logger.info.assert_called_once_with("2 directories, 2 files read in 0 sec")

    def test_should_print_checksum_given_file_has_checksum(self):
        walker = TreeWalker(self.config, self.storage)
        tests.helpers.setup_storage(self.storage, [
            {'folder': self.folder_one, 'files': [self.file_three]}
        ])

        walker.walk()

        self.mock_print.assert_has_calls([
            call("└─── A Folder"),
            call("    └─── C File [abc123]")
        ])
        self.mock_logger.info.assert_called_once_with("1 directories, 1 files read in 0 sec")

    def test_should_sort_folders_and_files_given_sort_enabled(self):
        self.config.list_sort = True
        walker = TreeWalker(self.config, self.storage)
        tests.helpers.setup_storage(self.storage, [
            {'folder': self.folder_two, 'files': [self.file_three, self.file_two]},
            {'folder': self.folder_one, 'files': [self.file_one]}
        ])

        walker.walk()

        self.mock_print.assert_has_calls([
            call("├─── A Folder"),
            call("│   └─── A File"),
            call("│   "),
            call("└─── B Folder"),
            call("    ├─── B File"),
            call("    └─── C File [abc123]")
        ])
        self.mock_logger.info.assert_called_once_with("2 directories, 3 files read in 0 sec")

    def test_should_not_sort_folders_and_files_given_sort_disabled(self):
        self.config.list_sort = False
        walker = TreeWalker(self.config, self.storage)
        tests.helpers.setup_storage(self.storage, [
            {'folder': self.folder_two, 'files': [self.file_three, self.file_two]},
            {'folder': self.folder_one, 'files': [self.file_one]}
        ])

        walker.walk()

        self.mock_print.assert_has_calls([
            call("├─── B Folder"),
            call("│   ├─── C File [abc123]"),
            call("│   └─── B File"),
            call("│   "),
            call("└─── A Folder"),
            call("    └─── A File")
        ])
        self.mock_logger.info.assert_called_once_with("2 directories, 3 files read in 0 sec")

    def test_should_print_only_folders_given_list_folders_enabled(self):
        self.config.list_folders = True
        walker = TreeWalker(self.config, self.storage)
        tests.helpers.setup_storage(self.storage, [
            {'folder': self.folder_two, 'files': [self.file_three, self.file_two]},
            {'folder': self.folder_one, 'files': [self.file_one]}
        ])

        walker.walk()

        self.mock_print.assert_has_calls([
            call("├─── B Folder"),
            call("└─── A Folder")
        ])
        self.mock_logger.info.assert_called_once_with("2 directories read in 0 sec")

    def test_should_sort_folders_and_files_given_sort_enabled2(self):
        self.config.list_sort = True
        self.config.list_folders = True
        walker = TreeWalker(self.config, self.storage)
        tests.helpers.setup_storage(self.storage, [
            {'folder': self.folder_two, 'files': [self.file_three, self.file_two]},
            {'folder': self.folder_one, 'files': [self.file_one]}
        ])

        walker.walk()

        self.mock_print.assert_has_calls([
            call("├─── A Folder"),
            call("└─── B Folder")
        ])
        self.mock_logger.info.assert_called_once_with("2 directories read in 0 sec")
