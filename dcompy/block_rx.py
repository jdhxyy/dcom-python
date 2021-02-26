"""
Copyright 2021-2021 The jdh99 Authors. All rights reserved.
块传输接收模块
Authors: jdh99 <jdh821@163.com>
"""

from dcompy.tx import *
from dcompy.system_error import *
from dcompy.common import *
from dcompy.config import *

import asyncio
import crcmodbus
import threading


class _Item:
    def __init__(self):
        self.protocol = 0
        self.port = 0
        self.src_ia = 0
        self.frame = Frame()
        self.block_header = BlockHeader()
        # 上次发送时间
        self.last_tx_time = 0
        self.retry_nums = 0


_items = list()
_lock = threading.Lock()
_block_recv = None


async def block_rx_run():
    """
    块传输接收模块运行协程
    """
    while True:
        _lock.acquire()
        _send_all_back_frame()
        _lock.release()

        await asyncio.sleep(INTERVAL)


def _send_all_back_frame():
    now = get_time()
    load_param = get_load_param()
    interval = load_param.block_retry_interval * 1000

    for i in _items:
        if now - i.last_tx_time < interval:
            continue
        if i.retry_nums > load_param.block_retry_max_num:
            _items.remove(i)
            continue
        # 超时重发
        if not load_param.is_allow_send(i.port):
            continue
        _send_back_frame(i)


def _send_back_frame(item: _Item):
    frame = Frame()
    frame.control_word.code = CODE_BACK
    frame.control_word.block_flag = 0
    frame.control_word.rid = item.frame.control_word.rid
    frame.control_word.token = item.frame.control_word.token
    frame.control_word.payload_len = 2
    frame.payload.append((item.block_header.offset >> 8) & 0xff)
    frame.payload.append(item.block_header.offset & 0xff)
    send(item.protocol, item.port, item.src_ia, frame)

    item.retry_nums += 1
    item.last_tx_time = get_time()


def block_rx_set_callback(recv_func):
    """
    设置接收回调函数
    :param recv_func:格式func(port: int, src_ia: int, frame Frame)
    """
    global _block_recv
    _block_recv = recv_func


def block_rx_receive(protocol: int, port: int, src_ia: int, frame: BlockFrame):
    """
    块传输接收数据
    """
    _lock.acquire()
    item, err = _get_item(protocol, port, src_ia, frame)
    if not err:
        _create_and_append_item(protocol, port, src_ia, frame)
    else:
        _edit_item(protocol, port, item, frame)
    _lock.release()


def _get_item(protocol: int, port: int, src_ia: int, frame: BlockFrame) -> (_Item, bool):
    for i in _items:
        if i.protocol == protocol and i.port == port and i.src_ia == src_ia \
                and i.frame.control_word.token == frame.control_word.token \
                and i.frame.control_word.rid == frame.control_word.rid \
                and i.frame.control_word.code == frame.control_word.code:
            return i, True
    return _Item(), False


def _create_and_append_item(protocol: int, port: int, src_ia: int, frame: BlockFrame):
    if frame.block_header.offset != 0:
        send_rst_frame(protocol, port, src_ia, SYSTEM_ERROR_WRONG_BLOCK_OFFSET, frame.control_word.rid,
                       frame.control_word.token)
        return

    item = _Item()
    item.protocol = protocol
    item.port = port
    item.src_ia = src_ia
    item.frame.control_word = frame.control_word
    item.block_header = frame.block_header
    item.frame.payload += frame.payload
    item.block_header.offset = len(frame.payload)
    _items.append(item)
    _send_back_frame(item)


def _edit_item(protocol: int, port: int, item: _Item, frame: BlockFrame):
    global _block_recv

    if item.block_header.offset != frame.block_header.offset or item.protocol != protocol or item.port != port:
        return

    item.frame.payload.extend(frame.payload)
    item.block_header.offset += len(frame.payload)

    item.retry_nums = 0
    _send_back_frame(item)

    if item.block_header.offset >= item.block_header.total:
        crc_calc = crcmodbus.checksum(item.frame.payload)
        if crc_calc != item.block_header.crc16:
            _items.remove(item)
            return
        if _block_recv is not None:
            _block_recv(item.protocol, item.port, item.src_ia, item.frame)
        _items.remove(item)


def block_rx_deal_rst_frame(protocol: int, port: int, src_ia: int, frame: Frame):
    """
    块传输接收模块处理复位连接帧
    """
    _lock.acquire()

    for i in _items:
        if i.protocol == protocol and i.port == port and i.src_ia == src_ia \
                and i.frame.control_word.token == frame.control_word.token \
                and i.frame.control_word.rid == frame.control_word.rid:
            _items.remove(i)
            break

    _lock.release()
