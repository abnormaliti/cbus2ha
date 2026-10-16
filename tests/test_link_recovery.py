#!/usr/bin/env python
# test_link_recovery.py - Tests for re-initialising a silent or rebooted PCI.
#
# This library is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import unittest
from unittest import mock

from cbus.daemon import cmqttd


class FakeSerial:
    out_waiting = 0


class FakeTransport:
    """Collects everything written to the PCI."""

    def __init__(self):
        self.written = bytearray()
        self.serial = FakeSerial()

    def write(self, data):
        self.written += data

    def get_write_buffer_size(self):
        return 0

    def resets(self):
        return self.written.count(b'~')


class LinkRecoveryTest(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.transport = FakeTransport()
        self.handler = cmqttd.CBusHandler(
            labels=None, link_check_interval=0.05, timesync_frequency=0,
            connection_lost_future=asyncio.get_running_loop().create_future())
        self.handler.connection_made(self.transport)
        self.addAsyncCleanup(self._stop)

    async def _stop(self):
        self.handler.stop_link_monitor()
        for task in asyncio.all_tasks():
            if task is not asyncio.current_task():
                task.cancel()

    def test_connect_resets_pci(self):
        self.assertEqual(3, self.transport.resets())

    @mock.patch.object(cmqttd, '_LINK_PROBE_WAIT', 0.01)
    @mock.patch.object(cmqttd, '_LINK_REINIT_EVERY', 2)
    async def test_reinit_when_link_down(self):
        # Probe every ~0.06 s; down after 2 misses, re-init then and every 2 more.
        while self.handler.link_up:
            await asyncio.sleep(0.01)
        self.assertEqual(6, self.transport.resets())

        await asyncio.sleep(0.15)  # 2 more unanswered probes
        self.assertEqual(9, self.transport.resets())

    async def test_power_up_reinitialises_once(self):
        self.handler.last_reset_time -= cmqttd._POWER_UP_SETTLE
        # The PCI sends the power-up notification twice.
        self.handler.data_received(b'++')
        self.assertEqual(6, self.transport.resets())

    async def test_power_up_after_own_reset_ignored(self):
        self.handler.data_received(b'+')
        self.assertEqual(3, self.transport.resets())

    async def test_any_data_marks_link_up(self):
        self.handler.link_up = False
        self.handler.data_received(b'+')
        self.assertTrue(self.handler.link_up)

    def test_tx_backlog_note(self):
        self.transport.serial.out_waiting = 7
        self.assertEqual(7, self.handler.tx_backlog())
        self.assertIn('7 bytes waiting', self.handler._tx_backlog_note())

    def test_tx_backlog_unknown_without_serial(self):
        self.transport.serial = None
        self.assertIsNone(self.handler.tx_backlog())
        self.assertEqual('', self.handler._tx_backlog_note())


if __name__ == '__main__':
    unittest.main()
