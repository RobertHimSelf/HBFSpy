#!/usr/bin/python
# -*- coding: utf-8 -*-

from hashlib import file_digest as _hash
from os import PathLike, chdir as _chdir, getcwd as _getcwd, makedirs as _makedirs, walk as _walk, listdir as _listdir, remove as _remove
from os.path import abspath as _abspath, join as _join, exists as _exists, isdir as _isdir, dirname as _dirname
from shutil import copy2 as _copy
from json import dump as _dump, load as _load
from datetime import datetime as _dt

__all__ = ["make_snapshot", "recover_from_snapshot", "remove_unused_backupfile"]

type FSPath = str | PathLike

def _get_hash(path: FSPath) -> str:
    '''Input a file's path, get the sha256 hash of the file.'''
    with open(path, 'rb') as f:
        digest = _hash(f, "sha256")
    return digest.hexdigest()

class _cd():
    '''在循环中重复进行 os.chdir 操作的同时，如果还要同时支持“相对路径”，那简直就是噩梦。
所以我写了这个“上下文管理器”对象。'''
    def __init__(self, change_dir_to):
        self.BeforeDir = _getcwd()
        self.AfterDir = _abspath(change_dir_to)
    def __enter__(self) -> None:
        _chdir(self.AfterDir)
    def __exit__(self, *args) -> None:
        _chdir(self.BeforeDir)

def make_snapshot(original_path: FSPath, backup_path: FSPath) -> str:
    '''对 "{original_path}" 中所有文件和子文件夹中的文件。记其基本信息如下：
路径： "{original_path}\\{opposite_filepath}"；
哈希值："{file_hash}"。

本函数会将文件复制到 "{backup_path}\\files\\{file_hash[:2]}\\{file_hash}"，并创建一个
字典，记录形如 "{file_hash}": "opposite_filepath" 的键值对。

然后将字典以 JSON 的形式，保存到 "{backup_path}/snapshot/{当前时间的时间戳}.json"，并返
回保存的 .json 文件的路径。
'''
    #创建 hash: path 对照表，并保存到 backup_path/snapshot/time.json 里。
    #将所备份的文件按其 hash 复制到 backup_path/hash[:2]/hash 的位置。
    record = dict()
    record["OriginalSyncPath"] = _abspath(original_path)
    record["files"] = dict()
    _makedirs(_join(backup_path, "snapshots"), exist_ok=True)
    with _cd(original_path):
        for folder in _walk("."):
            with _cd(folder[0]):
                for file in folder[2]:
                    file_hash = _get_hash(file)
                    record["files"][file_hash] = _join(folder[0], file)
                    sync_to = _join(backup_path, "files", file_hash[:2], file_hash)
                    if not _exists(sync_to):
                        _makedirs(_join(backup_path, "files", file_hash[:2]), exist_ok=True)
                        _copy(file, sync_to, follow_symlinks=False)
    record_name = _join(backup_path, "snapshots", _dt.today().isoformat(timespec='seconds').replace(":","").replace("-","") + ".json")
    with open(record_name, 'x', encoding="utf-8") as f:
        _dump(record, f)
    print(f"Sync Finished, details saved to {record_name}")
    return record_name

def recover_from_snapshot(snapshot_path: FSPath, recover_to: FSPath|None = None) -> None:
    '''{snapshot_path} 应该传入 make_snapshot 函数的返回值。
本函数会在 "{recover_to}" 位置创建一份调用 make_snapshot 时指定的 "{original_path}" 文
件夹的备份。如果 {recover_to} 留空，则默认 {recover_to} = {original_path}
'''
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
        _makedirs(_dirname(recovering_to), exist_ok=True)
        _copy(_join(hashed_file_folder, file_hash[:2], file_hash), recovering_to)
        print("Success")
    print(f"Recovered All Files To {recover_to}")

def remove_unused_backupfile(backup_path: FSPath) -> None:
    """在删除快照时，一些文件可能同时是其它快照的文件。本方法将自动删除“不属于任何快照”的
文件，以清理空间。"""
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
