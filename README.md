# dcompy
欢迎前往社区交流：[海萤物联网社区](http://www.ztziot.com)

## 简介
RPC：Remote Procedure Call，远程过程调用。使用RPC可以让一台计算机的程序程调用另一台计算机的上的程序。

RPC通过把网络通讯抽象为远程的过程调用，调用远程的过程就像调用本地的子程序一样方便，从而屏蔽了通讯复杂性，使开发人员可以无需关注网络编程的细节，将更多的时间和精力放在业务逻辑本身的实现上，提高工作效率。

DCOM：Device Communication Protocol(DCOM)，设备间通信协议。DCOM是针对物联网使用场景开发的RPC框架，主要有如下特点：

- 协议开销极小仅4字节。物联网很多场景都是几十字节的短帧，RPC协议本身的开销如果过大会导致在这些场景无法应用
- 可以跨语言通信。DCOM协议在设计上与语言无关，无论C，Golang，Python等都可以使用DCOM
- 可以跨通信介质通信。DCOM协议可以工作在以太网，串口，wifi，小无线等一切通信介质之上

在海萤物联网中，节点间使用DCOM来通信。本文介绍Python语言开发的DCOM包的使用方法。

## 开源
- [github上的项目地址](https://github.com/jdhxyy/dcom-python)
- [gitee上的项目地址](https://gitee.com/jdhxyy/dcom-python)

## 安装
```text
pip install dcompy
```

## 基础概念
查看文档 [海萤物联网教程：Go SDK](https://blog.csdn.net/jdh99/article/details/115329550) 基础概念章节。


## API
```python
def load(param: LoadParam)
	"""模块载入"""

def register(protocol: int, rid: int, callback):
    """
    注册DCOM服务回调函数
    :param protocol: 协议号
    :param rid: 服务号
    :param callback: 回调函数.格式: func(pipe: int, src_ia: int, req: bytearray) (bytearray, int)
    :return: 返回值是应答和错误码.错误码为0表示回调成功,否则是错误码
    """

def receive(protocol: int, pipe: int, src_ia: int, data: bytearray):
    """
    接收数据.应用模块接收到数据后需调用本函数,本函数接收帧的格式为DCOM协议数据
    """

def register(protocol: int, rid: int, callback):
    """
    注册DCOM服务回调函数
    :param protocol: 协议号
    :param rid: 服务号
    :param callback: 回调函数.格式: func(pipe: int, src_ia: int, req: bytearray) (bytearray, int)
    :return: 返回值是应答和错误码.错误码为0表示回调成功,否则是错误码
    """

def call(protocol: int, pipe: int, dst_ia: int, rid: int, timeout: int, req: bytearray) -> (bytearray, int):
    """
    RPC同步调用
    :param protocol: 协议号
    :param pipe: 通信管道
    :param dst_ia: 目标ia地址
    :param rid: 服务号
    :param timeout: 超时时间,单位:ms.为0表示不需要应答
    :param req: 请求数据.无数据可填bytearray()或者None
    :return: 返回值是应答字节流和错误码.错误码非SYSTEM_OK表示调用失败
    """
```

- 数据结构
```python
class LoadParam:
    """
    载入参数
    """

    def __init__(self):
        # 块传输帧重试间隔.单位:ms
        self.block_retry_interval = 0
        # 块传输帧重试最大次数
        self.block_retry_max_num = 0

        # API接口
        # 是否允许发送.函数原型:func(pipe: int) bool
        self.is_allow_send = None  # type: Callable[[int], bool]
        # 发送的是DCOM协议数据.函数原型:func(protocol: int, pipe: int, dst_ia: int, bytes: bytearray)
        self.send = None  # type: Callable[[int, int, int, bytearray], None]
```

- 系统错误码
```python
# 系统错误码
# 正确值
SYSTEM_OK = 0
# 接收超时
SYSTEM_ERROR_RX_TIMEOUT = 0x10
# 发送超时
SYSTEM_ERROR_TX_TIMEOUT = 0x11
# 内存不足
SYSTEM_ERROR_NOT_ENOUGH_MEMORY = 0x12
# 没有对应的资源ID
SYSTEM_ERROR_INVALID_RID = 0x13
# 块传输校验错误
SYSTEM_ERROR_WRONG_BLOCK_CHECK = 0x14
# 块传输偏移地址错误
SYSTEM_ERROR_WRONG_BLOCK_OFFSET = 0x15
# 参数错误
SYSTEM_ERROR_PARAM_INVALID = 0x16
```

### load：模块载入
在使用DCOM前必须要初始化。DCOM支持重传，所以在初始化时需输入重传间隔以及重传最大次数。

DCOM与通信介质无关，不同介质可定义不同的管道号。应用程序需要在是否允许发送函数（is_allow_send），以及发送函数（send）中编写不同管道的操作。

- 示例：某节点有两个管道
```python
if __name__ == '__main__':
	param = dcompy.LoadParam()
    param.block_retry_max_num = 5
    param.block_retry_interval = 1000
    param.is_allow_send = is_allow_send
    param.send = send
    dcompy.load(param)


def is_allow_send(pipe: int) -> bool:
    if pipe == 1:
    	return is_pipe1_allow_send()
    else:
    	return is_pipe2_allow_send()


def send(protocol: int, pipe: int, dst_ia: int, data: bytearray):
    if pipe == 1:
    	pipe1_send(data)
    else:
    	pipe2_send(data)
```

protocol，dst_ia等字段根据需求处理。

### receive 接收数据
应用程序接收到数据需要调用receive函数，将数据发送给DCOM。

- 示例：某节点有两个管道都可接收
```python
def pipe1_receive(data: bytearray):
	dcom.receive(0, 1, 0x2140000000000101, data)

def pipe2_receive(data: bytearray):
	dcom.Receive(0, 2, 0x2140000000000101, data)
```

协议号protocol示例中填写的是0，应用时根据实际场景填写。

### register：服务注册
节点可以通过注册服务开放自身的能力。

- 示例：假设节点2140::101是智能插座，提供控制和读取开关状态两个服务：

```python
dcom.register(0, 1, control_service)
dcom.register(0, 2, get_state_service)

// control_service控制开关服务
// 返回值是应答和错误码.错误码为0表示回调成功,否则是错误码
def control_service(pipe: int, src_ia: int, req: bytearray) -> (bytearray, int):
	if req[0] == 0:
		off()
	else:
		on()
	return None, dcom.SystemOK

// get_state_service 读取开关状态服务
// 返回值是应答和错误码.错误码为0表示回调成功,否则是错误码
def get_state_service(pipe: int, src_ia: int, req: bytearray) -> (bytearray, int):
	return bytearray([state()]), dcom.SystemOK
```

### call：同步调用
```python
def call(protocol: int, pipe: int, dst_ia: int, rid: int, timeout: int, req: bytearray) -> (bytearray, int):
    """
    RPC同步调用
    :param protocol: 协议号
    :param pipe: 通信管道
    :param dst_ia: 目标ia地址
    :param rid: 服务号
    :param timeout: 超时时间,单位:ms.为0表示不需要应答
    :param req: 请求数据.无数据可填bytearray()或者None
    :return: 返回值是应答字节流和错误码.错误码非SYSTEM_OK表示调用失败
    """
```

同步调用会在获取到结果之前阻塞。节点可以通过同步调用，调用目标节点的函数或者服务。timeout字段是超时时间，单位是毫秒。如果目标节点超时未回复，则会调用失败。如果超时时间填0，则表示不需要目标节点回复。

- 示例：2141::102节点控制智能插座2141::101开关状态为开

```python
resp, errCode = dcom.call(0, 1, 0x2140000000000101, 3000, bytearray([1]))
```

- 示例：2141::102节点读取智能插座2141::101开关状态

```python
resp, errCode = dcom.call(0, 2, 0x2140000000000101, 3000, None)
if errCode == dcom.SystemOK:
	print("开关状态:", resp[0])
```

## 请求和应答数据格式
DCOM通信双方发送的数据流都是二进制，请求（req）和应答（resp）的数据类型都是[]uint8。

二进制不利于应用处理，所以会将二进制转换为其他数据类型来处理。常用的有以下三种：
- 结构体
- json
- 字符串

在物联网中，硬件节点的资源有限，且大部分都是使用C语言编写代码。所以建议使用C语言结构体来通信。结构体约定使用1字节对齐，小端模式。

海萤物联网提供sbc库用来进行C语言结构体和二进制流的转换，详情可以查看文档：[海萤物联网教程：sbc：基于python的C语言格式结构体和二进制转换库](https://blog.csdn.net/jdh99/article/details/115388883)
