import abc

from loggerbyclass import get_logger_by_class


class CompletionProvider(abc.ABC):

    @abc.abstractmethod
    def provide(self, document, position):
        pass

    @abc.abstractmethod
    def get_trigger_characters(self):
        pass

    def ast_walk(self, ast, hook):
        recurse = hook(ast)
        if 'children' in ast and recurse:
            for child in ast['children']:
                self.ast_walk(child, hook)


class FootnoteLinkProvider(CompletionProvider):

    def __init__(self):
        self._logger = get_logger_by_class(self.__class__)

    def get_trigger_characters(self):
        return ['[']

    def provide(self, document, position):
        self._logger.debug('Providing completions for %s at %s',
                           document.uri, position)

        completions = []

        for label, detail in document.ast.get('footnotes', {}).items():
            completions.append({
                'label': '[{}]'.format(label),
                'detail': '{}'.format(detail),
                'textEdit': {
                    'range': {
                        'start': {
                            'line': position['line'],
                            'character': position['character'] - 1,
                        },
                        'end': {
                            'line': position['line'],
                            'character': position['character'],
                        },
                    },
                    'newText': '[{}]'.format(label)
                },
            })

        return completions


class HeadingLinkProvider(CompletionProvider):

    def __init__(self):
        self._logger = get_logger_by_class(self.__class__)

    def get_trigger_characters(self):
        return ['#']

    def provide(self, document, position):
        self._logger.debug('Providing completions for %s at %s',
                           document.uri, position)

        # collect current headlines
        entries = []

        def collect(ast):
            if ast['type'] == 'Heading':
                entries.append(
                    {
                        'level': ast['level'],
                        'text': ' '.join(
                            [c['content']
                             for c in ast['children']
                             if c['type'] == 'RawText']),
                    })
                return False
            return True

        self.ast_walk(document.ast, collect)

        self._logger.debug('Collected headings: %s', entries)

        completions = []

        for heading in entries:
            text = '#{}'.format(heading['text'].lower().replace(' ', '-'))
            completions.append({
                'label': text,
                'detail': '{} {}'.format('#' * heading['level'],
                                         heading['text']),
                'textEdit': {
                    'range': {
                        'start': {
                            'line': position['line'],
                            'character': position['character'] - 1,
                        },
                        'end': {
                            'line': position['line'],
                            'character': position['character'],
                        },
                    },
                    'newText': text,
                },
            })

        return completions
