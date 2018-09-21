import io

from loggerbyclass import get_logger_by_class

import mistletoe
import mistletoe.ast_renderer


class Document:

    def __init__(self, uri, text, version):
        self._uri = uri
        self._text = text
        self._version = version
        self._ast = None
        self._ast_outdated = True

    @property
    def uri(self):
        return self._uri

    @property
    def lines(self):
        return self._text.splitlines(True)

    @property
    def text(self):
        return self._text

    @property
    def ast(self):
        if self._ast_outdated:
            self._ast = mistletoe.ast_renderer.get_ast(
                mistletoe.Document(self.text))
            self._ast_outdated = False
        return self._ast

    def update(self, change, version=None):
        text = change['text']
        change_range = change.get('range')

        self._ast_outdated = True

        if version:
            self._version = version

        if not change_range:
            self._text = text
            return

        start_line = change_range['start']['line']
        start_col = change_range['start']['character']
        end_line = change_range['end']['line']
        end_col = change_range['end']['character']

        # handle additions at the end of the file
        if start_line == len(self.lines):
            self._text = self._text + text
            return

        # usual change of chunks
        new = io.StringIO()

        # Iterate over the existing document until we hit the edit range,
        # at which point we write the new text, then loop until we hit
        # the end of the range and continue writing.
        for i, line in enumerate(self.lines):
            if i < start_line:
                new.write(line)
                continue

            if i > end_line:
                new.write(line)
                continue

            if i == start_line:
                new.write(line[:start_col])
                new.write(text)

            if i == end_line:
                new.write(line[end_col:])

        self._text = new.getValue()


class Workspace:

    def __init__(self, rootUri):
        self._logger = get_logger_by_class(self.__class__)
        self._rootUri = rootUri
        self._documents = {}

    def put_document(self, document):
        if document.uri in self._documents:
            self._logger.debug('Replacing document with URI %s', document.uri)
        else:
            self._logger.debug('Adding document with URI %s', document.uri)

        self._documents[document.uri] = document

    def remove_document(self, uri):
        self._logger.debug('Removing document with URI %s', uri)
        if uri not in self._documents:
            self._logger.warn('Document with URI %s was not opened', uri)
        del self._documents[uri]

    def get_document(self, uri):
        return self._documents[uri]
