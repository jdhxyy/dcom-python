"""
Copyright 2021-2021 The jdh99 Authors. All rights reserved.
发送模块
Authors: jdh99 <jdh821@163.com>
"""

from dcompy.common import *


def send(protocol: int, port: int, dst_ia: int, frame: Frame):
    """
    发送数据
    """
    load_param = get_load_param()
    if not load_param.is_allow_send(port):
        return
    load_param.send(protocol, port, dst_ia, frame_to_bytes(frame))


def block_send(protocol: int, port: int, dst_ia: int, frame: BlockFrame):
    """
    块传输发送数据
    """
    load_param = get_load_param()
    if not load_param.is_allow_send(port):
        return
    load_param.send(protocol, port, dst_ia, block_frame_to_bytes(frame))


def send_rst_frame(protocol: int, port: int, dst_ia: int, error_code: int, rid: int, token: int):
    """
    发送错误码
    """
    frame = Frame()
    frame.control_word.code = CODE_RST
    frame.control_word.block_flag = 0
    frame.control_word.rid = rid
    frame.control_word.token = token
    frame.control_word.payload_len = 1
    frame.payload.append((error_code | 0x80) & 0xff)
    send(protocol, port, dst_ia, frame)
