#!/usr/bin/python
# -*- coding: utf-8 -*-

from hashlib import file_digest as _hash
from os import PathLike, chdir as _chdir, getcwd as _getcwd, makedirs as _makedirs, walk as _walk, listdir as _listdir, remove as _remove
from os.path import abspath as _abspath, join as _join, exists as _exists, isdir as _isdir, dirname as _dirname
from shutil import copy2 as _copy
from json import dump as _dump, load as _load
from datetime import datetime as _dt

type FSPath = str | PathLike

def _get_hash(path: FSPath) -> str:
    '''Input a file's path, get the sha256 hash of the file.'''
    with open(path, 'rb') as f:
        digest = _hash(f, "sha256")
    return digest.hexdigest()

class _cd():
    '''I Simply Made This Because I Refuse To Remember
Which Path Is The Current Workpath, But I Still Have To
Deal With Opposite Path.'''
    def __init__(self, change_dir_to):
        self.BeforeDir = _getcwd()
        self.AfterDir = _abspath(change_dir_to)
    def __enter__(self) -> None:
        _chdir(self.AfterDir)
    def __exit__(self, *args) -> None:
        _chdir(self.BeforeDir)

def make_snapshot(original_path: FSPath, backup_path: FSPath) -> None:
    '''Copy all files to {backup_path}/files/{file_hash[:2]}/{file_hash},
witch file_hash is the hash of the file. Creating a dict contains 
({file_hash}: {file_original_opposite_path}), and save the dict to 
{backup_path}/snapshot/{now_time}.json.'''
    #创建 hash: path 对照表，并保存到 backup_path/snapshot/time.json 里。
    #将所备份的文件按其 hash 复制到 backup_path/hash[:2]/hash 的位置。
    record = dict()
    record["OriginalSyncPath"] = _abspath(original_path)
    record["files"] = dict()
    _makedirs(_join(backup_path,"snapshots"))
    with _cd(original_path):
        for folder in _walk("."):
            with _cd(folder[0]):
                for file in folder[2]:
                    file_hash = _get_hash(file)
                    record["files"][file_hash] = _join(folder[0], file)
                    sync_to = _join(backup_path, "files", file_hash[:2], file_hash)
                    if not _exists(sync_to):
                        _makedirs(_join(backup_path, "files", file_hash[:2]))
                        _copy(file, sync_to, follow_symlinks=False)
    record_name = _join(backup_path, "snapshots", _dt.today().isoformat(timespec='seconds').replace(":","").replace("-","") + ".json")
    with open(record_name, 'x', encoding="utf-8") as f:
        _dump(record, f)
    print(f"Sync Finished, details saved to {record_name}")

def recover_from_snapshot(snapshot_path: FSPath, recover_to: FSPath|None = None) -> None:
    """Recover All File That Marked in {snapshot} To
{recover_to} Folder. {recover_to} will be set to the
original folder which has been taken this snapshot.
"""
    hashed_file_folder = _abspath(_join(snapshot_path,"..","..","files"))
    with open(snapshot_path, 'r', encoding="utf-8") as f:
        record = _load(f)
    if recover_to == None:
        recover_to = record["OriginalSyncPath"]
    
    if _exists(recover_to):
        if _isdir(recover_to):
            if len(_listdir(recover_to)) != 0:
                raise FileExistsError(f"Cannot recover to folder '{_abspath(recover_to)}' because it is not empty.")
        else:
            raise FileExistsError(f"Cannot recover to a file '{_abspath(recover_to)}', please input a folder path instead.")

    for file_hash in record["files"]:
        file_path = _join(recover_to, record["files"][file_hash])
        print(f"Recovering {file_path} ...", end="")
        recovering_to = _join(recover_to, record["files"][file_hash])
        _makedirs(_dirname(recovering_to))
        _copy(_join(hashed_file_folder, file_hash[:2], file_hash), recovering_to)
    print("Success")
    print(f"Recovered All Files To {recover_to}")

def remove_unused_backupfile(backup_path: FSPath) -> None:
    """Remove The Files in file folder which isn't in
any snapshots that exists now."""
    file_list = []
    for folder in _walk(_join(backup_path,"files")):
        file_list += folder[2]
    with _cd(_join(backup_path,"snapshots")):
        for snapshot in _listdir():
            with open(snapshot, "r", encoding="utf-8") as f:
                record = _load(f)
                for hash in record:
                    if hash in file_list:
                        file_list.remove(hash)
    for hash in file_list:
        _remove(_join(backup_path,"files",hash[:2],hash))
