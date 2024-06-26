# HBFSpy
一个基于文件哈希值的文件快照生成器 Python 模块。

它会在生成快照时，将所有文件按照哈希值保存到快照文件夹中。使得：
* 可以在不同快照中保存同名文件至同一个快照文件夹中；
* 各快照中的同样文件、哪怕不同名，也只会被保存一份。

之所以写这个，是因为[阿里云盘的自动同步做得像一坨屎](https://www.zhihu.com/question/430549529/answer/3460904078)。

当然，对于自动同步的内容，直接用 git 动不动就 push 一下一般是更好的。

## 系统要求
本模块所使用的以下内容是 Python 3.11 新加入的：
* hashlib.file_digest

请在 Python >= 3.11 的版本使用本模块。

## 安装
把这个项目里面的“HBFSpy”文件夹下载下来，然后拷贝到你的项目文件夹里面。然后在项目中使用：

`from HBFSpy import *`

应当就能正常使用了。

## 使用
本模块总共只提供了三个函数。

### 创建快照
`make_snapshot(original_path, backup_path)`

在 "{backup_path}" 中创建一份 "{original_path}" 文件夹的快照。

快照的具体信息将被保存至 "{backup_path}/snapshots/{当前时间戳}.json"，

返回“快照具体信息”的路径。

### 从快照重建文件
`recover_from_snapshot(snapshot_path, recover_to)`

snapshot_path 应当传入创建快照时，快照具体信息的路径，

recover_to 应传入恢复文件的位置，应当为空文件夹的路径、或不存在（但可以被创建）的路径

### 删除快照
如果只创建了一个快照，直接删除快照文件夹即可。

如果在同一个文件夹创建了多于一个快照，总共需要两个步骤来删除快照：

第一步：删除想要删除的快照所对应的具体信息文件，形如这种的："{backup_path}/snapshots/当前时间戳.json"

第二步：执行以下函数

`remove_unused_backupfile(backup_path)`

输入创建快照时的快照文件夹，删除其中所有“未在任意快照中被使用”的文件。
