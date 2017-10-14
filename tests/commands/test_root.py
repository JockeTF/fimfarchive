"""
Root command tests.
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


from unittest.mock import MagicMock, PropertyMock

import pytest

from fimfarchive.commands import Command, RootCommand


@pytest.fixture
def success():
    """
    Returns a command that succeeds.
    """
    class cls(Command):
        """
        Command that returns 0.

        With a truncated documentation line.
        """
        __call__ = MagicMock(return_value=0)

    return cls()


@pytest.fixture
def failure():
    """
    Returns a command that fails.
    """
    class cls(Command):
        """
        Command that returns 1.

        With a truncated documentation line.
        """
        __call__ = MagicMock(return_value=1)

    return cls()


@pytest.fixture
def root(success, failure):
    """
    Returns a root command with custom subcommands.
    """
    class cls(RootCommand):
        """
        Custom root command.
        """
        commands = {
            'success': type(success),
            'failure': type(failure),
        }

    return cls()


@pytest.fixture
def args():
    """
    Returns random command line arguments.
    """
    return [object() for i in range(3)]


class TestRootCommanad():
    """
    Tests the root command.
    """

    def mock_usage(self, cmd):
        """
        Returns a mocked usage property for the command.
        """
        usage = PropertyMock()
        type(cmd).usage = usage
        return usage

    def test_root_usage(self, root):
        """
        Tests usage contains first line of class documentation.
        """
        doc = root.usage
        assert "success  Command that returns 0." in doc
        assert "failure  Command that returns 1." in doc
        assert "truncated documentation line" not in doc

    def test_root_usage_without_commands(self, root):
        """
        Tests usage contains text when no commands are available.
        """
        type(root).commands = dict()
        assert root.usage.strip()

    def test_root_call_without_args(self, root, success, failure):
        """
        Tests `SystemExit` is raised if called without arguments.
        """
        usage = self.mock_usage(root)

        with pytest.raises(SystemExit):
            root()

        usage.assert_called_once_with()
        success.__call__.assert_not_called()
        failure.__call__.assert_not_called()

    def test_root_call_with_args(self, root, success, failure, args):
        """
        Tests `SystemExit` is raised if called with invalid arguments.
        """
        usage = self.mock_usage(root)

        with pytest.raises(SystemExit):
            root(*args)

        usage.assert_called_once_with()
        success.__call__.assert_not_called()
        failure.__call__.assert_not_called()

    def test_success_usage(self, root):
        """
        Tests success usage contains first line of class documentation.
        """
        doc = root.doc('success', adjust=9, indent=0)
        assert "success  Command that returns 0." == doc

    def test_success_call_without_args(self, root, success, failure):
        """
        Tests success can be called without arguments.
        """
        usage = self.mock_usage(root)
        code = root('success')
        success.__call__.assert_called_once_with()
        failure.__call__.assert_not_called()
        usage.assert_not_called()
        assert code == 0

    def test_success_call_with_args(self, root, success, failure, args):
        """
        Tests success can be called with arguments.
        """
        usage = self.mock_usage(root)
        code = root('success', *args)
        success.__call__.assert_called_once_with(*args)
        failure.__call__.assert_not_called()
        usage.assert_not_called()
        assert code == 0

    def test_failure_usage(self, root):
        """
        Tests failure usage contains first line of class documentation.
        """
        doc = root.doc('failure', adjust=9, indent=0)
        assert "failure  Command that returns 1." == doc

    def test_failure_call_without_args(self, root, success, failure):
        """
        Tests failure can be called without arguments.
        """
        usage = self.mock_usage(root)
        code = root('failure')
        success.__call__.assert_not_called()
        failure.__call__.assert_called_once_with()
        usage.assert_not_called()
        assert code == 1

    def test_failure_call_with_args(self, root, success, failure, args):
        """
        Tests failure can be called with arguments.
        """
        usage = self.mock_usage(root)
        code = root('failure', *args)
        success.__call__.assert_not_called()
        failure.__call__.assert_called_once_with(*args)
        usage.assert_not_called()
        assert code == 1
