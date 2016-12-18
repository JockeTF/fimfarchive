"""
Flavor tests.
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


from fimfarchive.flavors import Flavor


class TestFlavor:
    """
    Flavor tests.
    """

    def assert_flavor(self, flavor):
        """
        Asserts for standard flavor behavior.

        Args:
            flavor: Flavor class with A and B members.
        """
        a = flavor.A
        b = flavor.B

        assert type(a) == flavor
        assert type(b) == flavor
        assert a.value == 1
        assert b.value == 2
        assert a is flavor.A
        assert b is flavor.B
        assert a is not b
        assert a != b
        assert a in {a}
        assert b not in {a}

    def test_flavor_with_empty_values(self):
        """
        Tests generated flavor values.
        """
        class MyFlavor(Flavor):
            A = ()
            B = ()

        self.assert_flavor(MyFlavor)

    def test_flavor_with_custom_values(self):
        """
        Tests custom flavor values.
        """
        class MyFlavor(Flavor):
            A = (1)
            B = (1, 2)

            def __init__(self, one, two=2):
                self.one = one
                self.two = two

        self.assert_flavor(MyFlavor)

        assert MyFlavor.A.one == 1
        assert MyFlavor.A.two == 2
        assert MyFlavor.B.one == 1
        assert MyFlavor.B.two == 2

    def test_instance_representation(self):
        """
        Tests `repr` for flavor instances.
        """
        class MyFlavor(Flavor):
            A = ()
            B = ()

        template = "<flavor 'MyFlavor.{}'>"

        assert repr(MyFlavor.A) == template.format('A')
        assert repr(MyFlavor.B) == template.format('B')
