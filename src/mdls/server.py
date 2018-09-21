from pathlib import Path

from jsonrpc.dispatchers import MethodDispatcher
from jsonrpc.endpoint import Endpoint
from jsonrpc.streams import JsonRpcStreamReader, JsonRpcStreamWriter

from loggerbyclass import get_logger_by_class

from .completion import HeadingLinkProvider, FootnoteLinkProvider
from .workspace import Document, Workspace


class Mdls(MethodDispatcher):

    def __init__(self, rx, tx):
        self._logger = get_logger_by_class(self.__class__)
        self._jsonrpc_stream_reader = JsonRpcStreamReader(rx)
        self._jsonrpc_stream_writer = JsonRpcStreamWriter(tx)
        self._endpoint = Endpoint(self, self._jsonrpc_stream_writer.write,
                                  max_workers=64)

        self._completion_providers = [
            HeadingLinkProvider(),
            FootnoteLinkProvider(),
        ]

        self._client_capabilities = {}

        self._workspace = None

        self._shutdown = False

    def start(self):
        self._jsonrpc_stream_reader.listen(self._endpoint.consume)

    def _capabilities(self):
        return {
            'completionProvider': {
                'resolveProvider': False,
                'triggerCharacters': [c
                                      for p in self._completion_providers
                                      for c in p.get_trigger_characters()],
            }
        }

    def m_initialize(self,
                     processId=None,
                     rootUri=None,
                     rootPath=None,
                     initializationOptions=None,
                     capabilities=None,
                     workspaceFolders=None,
                     **kwargs):
        self._logger.debug('Received initialization request')

        if rootUri is None:
            rootUri = Path(rootPath).as_uri() if rootPath is not None else ''
        self._logger.debug('Using rootUri %s', rootUri)
        self.workspace = Workspace(rootUri)

        self._client_capabilities = capabilities

        server_capabilities = self._capabilities()
        self._logger.debug('Returning capabilities:\n%s', server_capabilities)
        return {'capabilities': server_capabilities}

    def m_initialized(self, **_kwargs):
        pass

    def m_shutdown(self, **_kwargs):
        self._shutdown = True
        return None

    def m_exit(self, **_kwargs):
        self._endpoint.shutdown()
        self._jsonrpc_stream_reader.close()
        self._jsonrpc_stream_writer.close()

    def m_text_document__did_open(self, textDocument=None, **_kwargs):
        self.workspace.put_document(
            Document(textDocument['uri'],
                     textDocument['text'],
                     version=textDocument.get('version')))

    def m_text_document__did_change(self, contentChanges=None,
                                    textDocument=None, **_kwargs):
        for change in contentChanges:
            self._logger.debug('Applying change %s to document with URI %s',
                               change, textDocument['uri'])
            document = self.workspace.get_document(textDocument['uri'])
            self._logger.debug('Contents before change:\n%s', document.text)
            document.update(change, version=textDocument.get('version'))
            self._logger.debug('Contents after change:\n%s', document.text)

    def m_text_document__did_close(self, textDocument=None, **_kwargs):
        self.workspace.remove_document(textDocument['uri'])

    def m_text_document__did_save(self, textDocument=None, **_kwargs):
        pass

    def m_text_document__completion(self, textDocument=None,
                                    position=None, **_kwargs):
        document = self.workspace.get_document(textDocument['uri'])
        completions = []
        for provider in self._completion_providers:
            completions.extend(provider.provide(document, position))
        self._logger.debug('Collected completions:\n%s', completions)
        return {
            'isIncomplete': False,
            'items': completions,
        }
