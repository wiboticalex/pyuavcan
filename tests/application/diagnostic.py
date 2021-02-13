# Copyright (c) 2020 UAVCAN Consortium
# This software is distributed under the terms of the MIT License.
# Author: Pavel Kirienko <pavel@uavcan.org>

import re
import typing
import asyncio
import logging
import pytest
import pyuavcan
from pyuavcan.transport.loopback import LoopbackTransport
from pyuavcan.presentation import Presentation
from pyuavcan.application import Node, NodeInfo


@pytest.mark.asyncio  # type: ignore
async def _unittest_slow_diagnostic_subscriber(
    compiled: typing.List[pyuavcan.dsdl.GeneratedPackageInfo], caplog: typing.Any
) -> None:
    from pyuavcan.application import diagnostic
    from uavcan.time import SynchronizedTimestamp_1_0

    assert compiled
    asyncio.get_running_loop().slow_callback_duration = 1.0

    node = Node(Presentation(LoopbackTransport(2222)), NodeInfo())
    pub = node.make_publisher(diagnostic.Record)
    diag = diagnostic.DiagnosticSubscriber(node)

    diag.start()

    caplog.clear()
    await pub.publish(
        diagnostic.Record(
            timestamp=SynchronizedTimestamp_1_0(123456789),
            severity=diagnostic.Severity(diagnostic.Severity.INFO),
            text="Hello world!",
        )
    )
    await asyncio.sleep(1.0)
    print("Captured log records:")
    for lr in caplog.records:
        print("   ", lr)
        assert isinstance(lr, logging.LogRecord)
        pat = r"uavcan\.diagnostic\.Record: node=2222 severity=2 ts_sync=123\.456789 ts_local=\S+:\nHello world!"
        if lr.levelno == logging.INFO and re.match(pat, lr.message):
            break
    else:
        assert False, "Expected log message not captured"

    diag.close()
    pub.close()
    node.close()
    await asyncio.sleep(1.0)  # Let the background tasks terminate.
