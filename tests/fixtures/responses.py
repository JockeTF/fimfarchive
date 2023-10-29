"""
Requests mocking fixture.
"""


#
# Fimfarchive, preserves stories from Fimfiction.
# Copyright (C) 2018  Joakim Soderlund
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


import json
from json import JSONDecodeError
from os import environ
from pathlib import Path
from typing import Any, ContextManager, Dict, Iterator, Optional, Union, Type

import pytest
from importlib.resources import as_file, files
from pytest import FixtureRequest
from requests import Session, Response
from requests.sessions import PreparedRequest
from requests_mock import Mocker

from fimfarchive.utils import JayWalker


__all__ = (
    'responses',
)


NAMESPACE = 'responses'


class Recorder(ContextManager['Recorder']):
    """
    Records responses for mocking.
    """

    def __init__(self, path: Path) -> None:
        """
        Constructor.

        Args:
            path: File to record to.
        """
        self.original = Session.send
        self.responses: Dict = dict()
        self.walker: Optional[JayWalker] = None
        self.path = path

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        """
        Yields all responses in a JSON-friendly format.
        """
        responses = [v for k, v in sorted(self.responses.items())]

        for request, response, exception in responses:
            if exception is not None:
                raise exception

            data = {
                'method': request.method,
                'status_code': response.status_code,
                'url': request.url,
            }

            try:
                data['json'] = response.json()
            except JSONDecodeError:
                data['text'] = response.text

            yield data

    def __call__(
            self,
            session: Session,
            request: PreparedRequest,
            **kwargs
            ) -> Response:
        """
        Performs a request and records the response.

        Args:
            session: The current session.
            request: The current request.
            **kwargs: Other arguments.

        Returns:
            A response instance.
        """
        key = (request.url, request.method)

        try:
            response = self.original(session, request, **kwargs)
            self.responses[key] = (request, response, None)
            return response
        except Exception as exception:
            self.responses[key] = (request, None, exception)
            raise exception

    def __enter__(self) -> 'Recorder':
        """
        Overrides the session send method.
        """
        def send(session, request, **kwargs):
            return self(session, request, **kwargs)

        Session.send = send  # type: ignore

        return self

    def __exit__(self, *args) -> None:
        """
        Restores the send method and persists responses.
        """
        Session.send = self.original  # type: ignore

        data = {NAMESPACE: list(self)}
        walker = self.walker

        if walker is not None:
            walker.walk(data)

        with open(self.path, 'wt') as fobj:
            json.dump(data, fobj, sort_keys=True, indent=4)


class Responder(Mocker, ContextManager['Responder']):
    """
    Mocks previously recorded responses.
    """

    def __init__(self, path: Path) -> None:
        """
        Constructor.

        Args:
            path: File containing the responses.
        """
        super().__init__()
        self.path = path

    def __enter__(self) -> 'Responder':
        """
        Enables the responder.
        """
        with open(self.path, 'rt') as fobj:
            data = json.load(fobj)

        mock = super().__enter__()
        assert mock is self

        for response in data[NAMESPACE]:
            self.register_uri(**response)

        return self


@pytest.fixture(scope='module')
def responses(request: FixtureRequest) -> Iterator[Union[Recorder, Responder]]:
    """
    Mocks or saves HTTP responses.
    """
    real = environ.get('REAL_HTTP', '').lower()
    name = request.path.with_suffix('.json').name
    package = files(request.module.__package__)
    resource = package.joinpath(name)

    context: Type[Union[Recorder, Responder]]

    if real in ('1', 'true', 'yes'):
        context = Recorder
    else:
        context = Responder

    with as_file(resource) as path:
        with context(path) as handler:
            yield handler
