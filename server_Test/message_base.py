#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# @author yufb116689@hanslaser.com
# @date 2016-05-05
#

import struct
import string

def struct_pack_string(str):
    str_len = len(str)
    data = struct.pack("!I", str_len)
    data += struct.pack("!%ds" % str_len, str)
    return data

def struct_unpack_string(data):
    str_len = struct.unpack_from(">I", data, 0)[0]
    str = struct.unpack_from(">%ds" % str_len, data, 4)[0]
    return str, str_len + 4

def struct_unpack_number(format, data, offset):
    if format[0] not in [">", "<", "="]:
    	return (None, 0)

    number_size = 0
    if format[1] in ["c", "b", "B", "?"]:
    	number_size = 1
    elif format[1] in ["h", "H"]:
        number_size = 2
    elif format[1] in ["i", "I", "l", "L", "f"]:
        number_size = 4
    elif format[1] in ["q", "Q", "d"]:
        number_size = 8
    else:
        return (None, 0)

    number = struct.unpack_from(format, data, offset)[0]

    return (number, offset + number_size)

class MessageHeader(object):
    """
    struct MessageHeader
    {
        uint32_t   length;              /* message total length */
        uint8_t    ctype                /* client type */
        uint32_t   cid;                 /* client id */
        uint32_t   did;                 /* destination id */
        uint64_t   seq;                 /* message sequence */
        uint16_t   cmd;                 /* request command */
    };
    """
    LENGTH = 23
    def __init__(self, length=0, ctype=0, cid=0, did=0, cmd=0, seq=0):
        self.length = length
        self.ctype = ctype
        self.cid = cid
        self.did = did
        self.cmd = cmd
        self.seq = seq

    def get_body_len(self):
        return self.length - self.__class__.LENGTH

    def pack(self):
        data = struct.pack("=IBIIQH", self.length, self.ctype, self.cid, self.did, self.seq, self.cmd)
        return data

    def unpack(self, data):
        self.length, self.ctype, self.cid, self.did, self.seq, self.cmd = struct.unpack("=IBIIQH", data);
        return self.LENGTH;

    def __str__(self):
        return "{ length: %d, ctype: %d, cid: %d, did: %d, seq: %x, cmd: %d }" % (self.length, self.ctype, self.cid, self.did, self.seq, self.cmd)

class BinaryMessage(object):
    def __init__(self):
        self.hdr = None
        self.data = ""

    def AppendData(self, data):
        feeds = 0
        if len(self.data) < MessageHeader.LENGTH:
            feeds = MessageHeader.LENGTH - len(self.data);
            feeds = min(feeds, len(data))
            self.data += data[:feeds]
        if self.hdr is None and len(self.data) >= MessageHeader.LENGTH:
            self.DecodeHeader(self.data)
        if self.hdr is not None:
            begin = feeds
            more = self.hdr.length - len(self.data)
            feeds += more
            feeds = min(feeds, len(data))
            self.data += data[begin:feeds]
        return feeds

    def DecodeHeader(self, data):
        self.hdr = MessageHeader()
        self.hdr.unpack(data)

    def Header(self):
        return self.hdr

    def NeedMoreSize(self):
        data_size = len(self.data)
        return MessageHeader.LENGTH - data_size if data_size < MessageHeader.LENGTH else self.hdr.length - data_size

    def Payload(self):
        return self.data[MessageHeader.LENGTH:] if self.hdr is not None else None

    def PayloadSize(self):
        return self.hdr.length - MessageHeader.LENGTH if self.hdr is not None else 0

    def Whole(self):
        return len(self.data) == self.hdr.length if self.hdr is not None else False

    def Size(self):
        return len(self.data)
    
    def Clear(self):
        self.hdr = None
        self.data = ""

class MQ(object):
    def __init__(self):
        self.queue = []

    def Size(self):
        return len(self.queue)

    def Empty(self):
        return self.Size() == 0

    def Clear(self):
        self.queue = []

    def First(self):
        if self.Empty():
            self.Push(BinaryMessage())
        return self.queue[0]

    def Push(self, msg):
        self.queue.append(msg)

    def Last(self):
        if self.Empty():
            self.Push(BinaryMessage())
        return self.queue[-1]

    def EraseFirst(self):
        del self.queue[0]

    def NeedMore(self):
        return self.Last().NeedMoreSize()

    def AppendData(self, data):
        feeds = 0
        size = len(data)
        while feeds < size:
            if self.Last().Whole():
                self.Push(BinaryMessage())

            feeds += self.Last().AppendData(data[feeds:])
            #if self.Last().Whole():
            #    print "Received a whole message, size: %d" % self.Last().Size()

    def Apply(self, fn):
        while not self.Empty() and self.First().Whole():
            fn(self.First())
            self.EraseFirst()


class BaseRequest(MessageHeader):
    def __init__(self):
        pass

class BaseResponse(MessageHeader):
    """
    struct ResponseHeader
    {
        uint16_t     errcode;
        std::string  errmsg;
    };
    """

    def __init__(self, errcode=0, errmsg=""):
        self.errcode = errcode
        self.errmsg = errmsg

    def pack(self):
        data = struct.pack("!H", self.errcode)
        if self.errcode != 0:
            data += struct_pack_string(self.errmsg)
        return data

    def unpack(self, data):
        offset = 0
        self.errcode = struct.unpack_from(">H", data, offset)[0]
        offset += 4
        if self.errcode != 0:
            self.errmsg, offset = struct_unpack_string(data)
        return offset

    def to_string(self):
        ret_str = "{ errcode: %d, errmsg: %s }" % (self.errcode, self.errmsg)
        return ret_str

    def __str__(self):
        return self.to_string()
