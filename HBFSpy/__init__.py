#!/usr/bin/python
# -*- coding: utf-8 -*-

from hashlib import file_digest as _hash
from shutil import copy2 as _copy, rmtree as _rmdirs
from os import walk as _walk, getcwd as _cwd, chdir as _cd, listdir as _hasfile, makedirs as _mkdirs, chmod as _chmod, remove as _rmfile
from os.path import join as _join, exists as _has, abspath as _abs, isdir as _hasdir, dirname as _dirname
from stat import S_IWRITE as _writeable
from datetime import datetime as _dt
from json import dump as _dump, load as _load

__all__ = ["make_snapshot", "recover_from_snapshot", "remove_unused_backupfile"]

def _get_hash(path: str) -> str:
    '''Input a file's path, get the sha256 hash of the file.'''
    with open(path, 'rb') as f:
        digest = _hash(f, "sha256")
    return digest.hexdigest()

class _changeWorkpathTo():
    '''I Simply Made This Because I Refuse To Remember
Witch Path Is The Current Workpath, But I Still Have To
Deal With Opposite Path.'''
    def __init__(self, change_dir_to):
        self.BeforeDir = _cwd()
        self.AfterDir = _abs(change_dir_to)
    def __enter__(self):
        _cd(self.AfterDir)
    def __exit__(self, *args):
        _cd(self.BeforeDir)

def _make_dir(path: str, cleardir = False) -> bool:
    '''Writing this Function is a Fault, but I Refused
to Remove this.'''
    if _hasdir(path):
        if cleardir:
            if len(_hasfile(path)) != 0:
                if input(f"There is still something in {path}, and this action will delete everything in {path}, continue?(y/n)").lower() == "y":
                    _rmdirs(path, onexc=_remove_readonly)
                    _mkdirs(path)
                    return True
                else:
                    print("Recover Stoped: User Abortion")
                    return False
        else:
            return True
    else:
        _mkdirs(path)
    return True

def make_snapshot(original_path: str, backup_path: str) -> None:
    '''Copy all files to {backup_path}/files/{file_hash[:2]}/{file_hash},
witch file_hash is the hash of the file. Creating a dict contains 
({file_hash}: {file_original_opposite_path}), and save the dict to 
{backup_path}/snapshot/{now_time}.json.'''
    #创建 hash: path 对照表，并保存到 backup_path/snapshot/time.json 里。
    #将所备份的文件按其 hash 复制到 backup_path/hash[:2]/hash 的位置。
    record = dict()
    record["OriginalSyncPath"] = original_path
    record["files"] = dict()

    _make_dir(_join(backup_path,"files"))
    _make_dir(_join(backup_path,"snapshots"))

    with _changeWorkpathTo(original_path):
        for folder in _walk("."):
            with _changeWorkpathTo(folder[0]):
                for file in folder[2]:
                    file_hash = _get_hash(file)
                    record["files"][file_hash] = _join(folder[0], file)
                    sync_to = _join(backup_path, "files", file_hash[:2], file_hash)
                    if not _has(sync_to):
                        _make_dir(_join(backup_path, "files", file_hash[:2]))
                        _copy(file, sync_to, follow_symlinks=False)
    record_name = _join(backup_path, "snapshots", _dt.today().isoformat(timespec='seconds').replace(":","").replace("-","") + ".json")
    with open(record_name, 'x', encoding="utf-8") as f:
        _dump(record, f)
    print(f"Sync Finished, details saved to {record_name}")

def _remove_readonly(func, path, _):
    "Clear the readonly bit and reattempt the removal"
    _chmod(path, _writeable)
    func(path)

def recover_from_snapshot(snapshot_path: str, recover_to: str|None = None) -> None:
    """Recover All File That Marked in {snapshot} To
{recover_to} Folder. {recover_to} will be set to the
original folder which has been taken this snapshot.
"""
    hashed_file_folder = _abs(_join(snapshot_path,"..","..","files"))
    with open(snapshot_path, 'r', encoding="utf-8") as f:
        record = _load(f)
    if recover_to == None:
        recover_to = record["OriginalSyncPath"]
    if _make_dir(recover_to, cleardir = True):
        for file_hash in record["files"]:
            file_path = _join(recover_to, record["files"][file_hash])
            print(f"Recovering {file_path} ...", end="")
            recovering_to = _join(recover_to, record["files"][file_hash])
            _make_dir(_dirname(recovering_to))
            _copy(_join(hashed_file_folder, file_hash[:2], file_hash), recovering_to)
            print("Success")
        print(f"Recovered All Files To {recover_to}")

def remove_unused_backupfile(backup_path: str) -> None:
    """Remove The Files in file folder which isn't in
any snapshots that exists now."""
    file_list = []
    for folder in _walk(_join(backup_path,"files")):
        file_list += folder[2]
    with _changeWorkpathTo(_join(backup_path,"snapshots")):
        for snapshot in _hasfile():
            with open(snapshot, "r", encoding="utf-8") as f:
                record = _load(f)
                for hash in record:
                    if hash in file_list:
                        file_list.remove(hash)
    for hash in file_list:
        _rmfile(_join(backup_path,"files",hash[:2],hash))
