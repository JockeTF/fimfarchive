"""
Signal tests.
"""


#
# Fimfarchive, preserves stories from Fimfiction.
# Copyright (C) 2015  Joakim Soderlund
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#


from collections import OrderedDict
from unittest.mock import patch, Mock

import blinker
import pytest

from fimfarchive.signals import (
    Signal, SignalBinder, SignalSender, SignalReceiver
)


@pytest.fixture
def params():
    """
    Returns an ordered dict of parameters.
    """
    data = (
        ('a', 1),
        ('b', 2),
        ('c', 3),
    )

    return OrderedDict(data)


@pytest.fixture
def signal(params):
    """
    Returns an unbound signal instance.
    """
    return Signal(*params.keys())


@pytest.fixture
def sender(signal):
    """
    Returns a signal sender instance.
    """
    class Sender(SignalSender):
        on_signal = signal

    return Sender()


@pytest.fixture
def receiver(sender):
    """
    Returns a connected signal receiver intance.
    """
    class Receiver(SignalReceiver):
        on_signal = Mock('on_signal')

    with Receiver(sender) as receiver:
        yield receiver


@pytest.fixture
def binder(sender):
    """
    Returns a bound signal instance.
    """
    return sender.on_signal


class TestSignal:
    """
    Signal tests.
    """

    def test_reserved_value_names(self):
        """
        Tests `ValueError` is raised for reserved value names.
        """
        with pytest.raises(ValueError):
            Signal('sender')

    def test_send_unbound_signal(self, params, signal):
        """
        Tests `ValueError` is raised when calling unbound signals.
        """
        with pytest.raises(ValueError):
            signal(*params.values())

    def test_parameter_mapping(self, params, signal, sender):
        """
        Tests positional parameters maps to named parameters.
        """
        with patch.object(blinker.Signal, 'send') as m:
            signal.send(sender, *params.values())
            m.assert_called_once_with(sender, **params)

    def test_parameter_overflow(self, params, signal, sender):
        """
        Tests `ValueError` is raised on too many parameters.
        """
        with pytest.raises(ValueError):
            signal.send(sender, *params.values(), 'alpaca')

    def test_duplicate_parameter(self, params, signal, sender):
        """
        Tests `ValueError` is raised on duplicate parameters.
        """
        duplicate = dict(tuple(params.items())[:1])

        with pytest.raises(ValueError):
            signal.send(sender, *params.values(), **duplicate)


class TestSignalBinder:
    """
    SignalBinder tests.
    """

    def test_send(self, params, sender, binder):
        """
        Tests sender is passed to signal.
        """
        with patch.object(Signal, 'send') as m:
            binder(*params.values())
            m.assert_called_once_with(sender, *params.values())


class TestSignalSender:
    """
    SignalSender tests.
    """

    def test_bind(self, signal, sender, binder):
        """
        Tests signal is bound on init.
        """
        cls = type(sender)

        assert isinstance(cls.on_signal, Signal)
        assert isinstance(sender.on_signal, SignalBinder)

        assert signal == cls.on_signal
        assert binder == sender.on_signal

    def test_send(self, params, sender):
        """
        Tests sender is passed to signal
        """
        with patch.object(Signal, 'send') as m:
            sender.on_signal(*params.values())
            m.assert_called_once_with(sender, *params.values())


class TestSignalReceiver:
    """
    SignalReceiver tests.
    """

    def test_connect(self, signal, receiver):
        """
        Tests receiver connects to signal automatically.
        """
        assert receiver.on_signal in signal.receivers

    def test_send(self, params, sender, receiver):
        """
        Tests receiver receives emitted signal.
        """
        sender.on_signal(*params.values())
        receiver.on_signal.assert_called_once_with(sender, **params)
