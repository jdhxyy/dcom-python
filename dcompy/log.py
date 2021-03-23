"""
Copyright 2021-2021 The jdh99 Authors. All rights reserved.
日志模块
Authors: jdh99 <jdh821@163.com>
"""

import lagan

_TAG = "dcom"

_filter_level = lagan.LEVEL_OFF


def set_filter_level(level):
    """设置日志过滤级别"""
    global _filter_level
    _filter_level = level


def debug(msg: str, *args, **kwarg):
    """打印debug信息"""
    if _filter_level == lagan.LEVEL_OFF or lagan.LEVEL_DEBUG < _filter_level:
        return
    lagan.debug(_TAG, msg, *args, **kwarg)


def info(msg: str, *args, **kwarg):
    """打印info信息"""
    if _filter_level == lagan.LEVEL_OFF or lagan.LEVEL_INFO < _filter_level:
        return
    lagan.info(_TAG, msg, *args, **kwarg)


def warn(msg: str, *args, **kwarg):
    """打印warn信息"""
    if _filter_level == lagan.LEVEL_OFF or lagan.LEVEL_WARN < _filter_level:
        return
    lagan.warn(_TAG, msg, *args, **kwarg)


def error(msg: str, *args, **kwarg):
    """打印debug信息"""
    if _filter_level == lagan.LEVEL_OFF or lagan.LEVEL_ERROR < _filter_level:
        return
    lagan.error(_TAG, msg, *args, **kwarg)
