"""
Copyright 2021-2021 The jdh99 Authors. All rights reserved.
接收到连接时处理
Authors: jdh99 <jdh821@163.com>
"""

from dcompy.callback import *
from dcompy.block_tx import *


def rx_con(protocol: int, port: int, src_ia: int, frame: Frame):
    """
    接收到连接帧时处理函数
    """
    resp, err = service_callback(protocol, frame.control_word.rid, frame.payload)

    # NON不需要应答
    if frame.control_word.code == CODE_NON:
        return

    if err != SYSTEM_OK:
        send_rst_frame(protocol, port, src_ia, err, frame.control_word.rid, frame.control_word.token)
        return

    if resp and len(resp) > SINGLE_FRAME_SIZE_MAX:
        # 长度过长启动块传输
        block_tx(protocol, port, src_ia, CODE_ACK, frame.control_word.rid, frame.control_word.token, resp)
        return

    ack_frame = Frame()
    ack_frame.control_word.code = CODE_ACK
    ack_frame.control_word.block_flag = 0
    ack_frame.control_word.rid = frame.control_word.rid
    ack_frame.control_word.token = frame.control_word.token
    if resp:
        ack_frame.control_word.payload_len = len(resp)
        ack_frame.payload.extend(resp)
    else:
        ack_frame.control_word.payload_len = 0
    send(protocol, port, src_ia, ack_frame)
