"""
Utility tests.
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


from fimfarchive.utils import Empty


class TestEmpty:
    """
    Empty tests.
    """

    def test_empty_class_is_not_none(self):
        """
        Tests `Empty` class is different from `None`.
        """
        assert Empty is not None
        assert Empty != None  # noqa

    def test_empty_class_evaluates_to_false(self):
        """
        Tests `Empty` class evaluates to `False`.
        """
        assert not Empty

    def test_empty_class_is_empty(self):
        """
        Tests `Empty` class can be identified.
        """
        assert Empty is Empty
        assert Empty == Empty

    def test_empty_instance_evaluates_to_false(self):
        """
        Tests `Empty` instance evaulates to `False`
        """
        assert not Empty()

    def test_empty_instance_is_unique(self):
        """
        Tests `Empty` instances are unique.
        """
        empty = Empty()

        assert isinstance(empty, Empty)
        assert empty is not Empty
        assert empty != Empty
        assert empty is not Empty()
        assert empty != Empty()
        assert empty is empty
        assert empty == empty
