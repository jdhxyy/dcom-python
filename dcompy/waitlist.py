"""
Copyright 2021-2021 The jdh99 Authors. All rights reserved.
等待队列
Authors: jdh99 <jdh821@163.com>
"""

from dcompy.block_tx import *
from dcompy.system_error import *

from typing import Callable
import threading


class _Item:
    def __init__(self):
        self.port = 0
        self.timeout = 0
        self.req = bytearray()
        self.resp = bytearray()
        self.time_start = 0
        # 回调函数.存在则是异步调用
        self.ack_callback = None

        self.dst_ia = 0
        self.rid = 0
        self.token = 0
        self.is_rx_ack = False
        self.result = SYSTEM_OK


_items = list()
_lock = threading.Lock()


async def waitlist_run():
    """
    模块运行
    """
    while True:
        _lock.acquire()
        _delete_timeout_item()
        _lock.release()
        await asyncio.sleep(INTERVAL)


def _delete_timeout_item():
    now = get_time()
    for item in _items:
        if item.ack_callback is None:
            # 同步调用自己管理超时
            continue

        if now - item.time_start > item.timeout:
            item.ack_callback(bytearray(), SYSTEM_ERROR_RX_TIMEOUT)
            _items.remove(item)


def call(port: int, dst_ia: int, rid: int, timeout: int, req: bytearray) -> (bytearray, int):
    """
    RPC同步调用
    :param port: 通信端口号
    :param dst_ia: 目标ia地址
    :param rid: 服务号
    :param timeout: 超时时间,单位:ms.为0表示不需要应答
    :param req: 请求数据.无数据可填bytearray()或者None
    :return: 返回值是应答字节流和错误码.错误码非SYSTEM_OK表示调用失败
    """
    code = CODE_CON if timeout > 0 else CODE_NON
    if not req:
        req = bytearray()

    token = get_token()
    _send_frame(port, dst_ia, code, rid, token, req)

    if code == CODE_NON:
        return bytearray(), SYSTEM_OK

    item = _Item()
    item.port = port
    item.timeout = timeout * 1000
    item.req = req
    item.time_start = get_time()

    item.dst_ia = dst_ia
    item.rid = rid
    item.token = token

    _lock.acquire()
    _items.append(item)
    _lock.release()

    while True:
        if item.is_rx_ack:
            break
        if get_time() - item.time_start > item.timeout:
            item.result = SYSTEM_ERROR_RX_TIMEOUT
            break

    _lock.acquire()
    _items.remove(item)
    _lock.release()
    return item.resp, item.result


def call_async(port: int, dst_ia: int, rid: int, timeout: int, req: bytearray,
               ack_callback: Callable[[bytearray, int], None]):
    """
    RPC异步调用
    :param port: 通信端口号
    :param dst_ia: 目标ia地址
    :param rid: 服务号
    :param timeout: 超时时间,单位:ms.为0表示不需要应答
    :param req: 请求数据.无数据可填bytearray()或者None
    :param ack_callback: 回调函数.原型func(resp: bytearray, error: int).参数是应答字节流和错误码.错误码非SYSTEM_OK表示调用失败
    """
    code = CODE_CON
    if timeout == 0 or not callable(ack_callback):
        code = CODE_NON
    if not req:
        req = bytearray()

    token = get_token()
    _send_frame(port, dst_ia, code, rid, token, req)

    if code == CODE_NON:
        return

    item = _Item()
    item.ack_callback = ack_callback
    item.port = port
    item.timeout = timeout * 1000
    item.req = req
    item.time_start = get_time()

    item.dst_ia = dst_ia
    item.rid = rid
    item.token = token

    _lock.acquire()
    _items.append(item)
    _lock.release()


def _send_frame(port: int, dst_ia: int, code: int, rid: int, token: int, data: bytearray):
    if len(data) >= SINGLE_FRAME_SIZE_MAX:
        block_tx(port, dst_ia, code, rid, token, data)
        return

    frame = Frame()
    frame.control_word.code = code
    frame.control_word.block_flag = 0
    frame.control_word.rid = rid
    frame.control_word.token = token
    frame.control_word.payload_len = len(data)
    frame.payload.extend(data)
    send(port, dst_ia, frame)


def rx_ack_frame(port: int, src_ia: int, frame: Frame):
    """
    接收到ACK帧时处理函数
    """
    _lock.acquire()

    for item in _items:
        if _check_item_and_deal_ack_frame(port, src_ia, frame, item):
            break

    _lock.release()


def _check_item_and_deal_ack_frame(port: int, src_ia: int, frame: Frame, item: _Item) -> bool:
    if item.port != port or item.dst_ia != src_ia or item.rid != frame.control_word.rid \
            or item.token != frame.control_word.token:
        return False

    if item.ack_callback:
        # 回调方式
        item.ack_callback(frame.payload, SYSTEM_OK)
        _items.remove(item)
    else:
        # 同步调用
        item.is_rx_ack = True
        item.result = SYSTEM_OK
        item.resp = frame.payload
    return True


def rx_rst_frame(port: int, src_ia: int, frame: Frame):
    """
    接收到RST帧时处理函数
    """
    _lock.acquire()

    for item in _items:
        _deal_rst_frame(port, src_ia, frame, item)

    _lock.release()


def _deal_rst_frame(port: int, src_ia: int, frame: Frame, item: _Item):
    if item.port != port or item.dst_ia != src_ia or item.rid != frame.control_word.rid or \
            item.token != frame.control_word.token:
        return False
    result = frame.payload[0]

    if item.ack_callback:
        # 回调方式
        item.ack_callback(bytearray(), result)
        _items.remove(item)
    else:
        # 同步调用
        item.is_rx_ack = True
        item.result = result
    return True
