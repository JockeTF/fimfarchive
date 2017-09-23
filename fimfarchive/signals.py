"""
Signals for Fimfarchive.
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


import blinker


__all__ = (
    'Signal',
    'SignalBinder',
    'SignalSender',
    'SignalReceiver',
    'find_related',
    'find_sources',
    'find_targets',
    'find_matches',
)


class Signal(blinker.Signal):
    """
    Blinker signal with positional arguments.
    """

    def __init__(self, *spec):
        """
        Constructor.

        Args:
            spec: Names of the signal arguments.
        """
        if 'sender' in spec:
            raise ValueError("Reserved argument name: 'sender'")

        self.spec = ('sender', *spec)
        super().__init__(doc=repr(self))

    def __call__(self, *args, **kwargs):
        """
        Raises an error regarding unbound signals.
        """
        raise ValueError(
            "Unbound signal. Forgot {}'s initializer?"
            .format(type(SignalSender).__name__)
        )

    def __repr__(self):
        return "<signal ({})>".format(', '.join(self.spec))

    def send(self, *args, **kwargs):
        """
        Emits this signal on behalf of its sender.

        Args:
            sender: Object sending the signal.
            *args: Values to pass to the receiver.

        Returns:
            A list of 2-tuples. Each tuple contains the
            signal's receiver and its returned values.
        """

        if len(self.spec) < len(args):
            raise ValueError(
                "Expected at most {} arguments, got {}."
                .format(len(self.spec), len(args))
            )

        data = {self.spec[i]: v for i, v in enumerate(args)}
        duplicates = set(data.keys()).intersection(kwargs.keys())

        if duplicates:
            raise ValueError(
                "Got duplicate values for: '{}'"
                .format("', '".join(duplicates))
            )

        data.update(kwargs)
        sender = data.pop('sender', None)

        return super().send(sender, **data)


class SignalBinder:
    """
    Bound transparent proxy for signals.
    """

    def __init__(self, signal, sender):
        """
        Constructor.

        Args:
            signal: Object to bind for.
            sender: Object to bind to.
        """
        self.signal = signal
        self.sender = sender

    def __call__(self, *args, **kwargs):
        return self.send(self.sender, *args, **kwargs)

    def __getattr__(self, attr):
        return getattr(self.signal, attr)

    def __repr__(self):
        return "<bound {} of {}>".format(self.signal, self.sender)


class SignalSender:
    """
    Automatically binds unbound signals on init.
    """

    def __init__(self):
        """
        Constructor.
        """
        for key, source in find_sources(self):
            if not isinstance(source, SignalBinder):
                binding = SignalBinder(source, self)
                setattr(self, key, binding)


class SignalReceiver:
    """
    Automatically connects signals on enter.
    """

    def __init__(self, sender):
        """
        Constructor.

        Args:
            sender: Object to connect to.
        """
        self.sender = sender

    def __enter__(self):
        for key, source, target in find_matches(self.sender, self):
            source.connect(target, sender=self.sender)

        return self

    def __exit__(self, *args):
        for key, source, target in find_matches(self.sender, self):
            source.disconnect(target, sender=self.sender)


def find_related(obj):
    """
    Yields all source or target candidates.
    """
    for key in dir(obj):
        if key.startswith('on_'):
            yield key, getattr(obj, key)


def find_sources(sender):
    """
    Yields all source signals in a sender.
    """
    for key, value in find_related(sender):
        connect = getattr(value, 'connect', None)
        disconnect = getattr(value, 'disconnect', None)

        if callable(connect) and callable(disconnect):
            yield key, value


def find_targets(receiver):
    """
    Yields all target methods in a receiver.
    """
    for key, value in find_related(receiver):
        if callable(value):
            yield key, value


def find_matches(sender, receiver):
    """
    Yields all matching signal connections.
    """
    sources = dict(find_sources(sender))
    targets = dict(find_targets(receiver))

    for key in sources.keys() & targets.keys():
        yield key, sources[key], targets[key]
