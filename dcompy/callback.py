"""
Copyright 2021-2021 The jdh99 Authors. All rights reserved.
回调模块主文件
Authors: jdh99 <jdh821@163.com>
"""

from dcompy.system_error import *

_services = dict()


def register(protocol: int, rid: int, callback):
    """
    注册DCOM服务回调函数
    :param protocol: 协议号
    :param rid: 服务号
    :param callback: 回调函数.格式: func(req bytearray) (bytearray, int)
    :return: 返回值是应答和错误码.错误码为0表示回调成功,否则是错误码
    """
    rid += protocol << 16
    _services[rid] = callback


def service_callback(protocol: int, rid: int, req: bytearray) -> (bytearray, int):
    """
    回调资源号rid对应的函数
    """
    rid += protocol << 16
    if rid not in _services:
        return None, SYSTEM_ERROR_INVALID_RID
    return _services[rid](req)
