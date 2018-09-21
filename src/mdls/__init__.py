import argparse
import logging
import logging.config
import socketserver
import sys
from typing import IO, Optional

from .server import Mdls


def parse_arguments(argv=None):
    parser = argparse.ArgumentParser(
        prog='mdls',
        description='A language server for markdown files',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    tcp_group = parser.add_argument_group('TCP mode options')
    tcp_group.add_argument(
        '--port',
        type=int,
        default=2402,
        help='Port to listen on in TCP mode')
    tcp_group.add_argument(
        '--host',
        default='127.0.0.1',
        help='Bind to this IP address when listening')

    parser.add_argument(
        '-l', '--logging-config',
        type=argparse.FileType('r'),
        help='Configuration file for the logging system')

    parser.add_argument(
        'mode',
        choices=['stdio', 'tcp'],
        help='Communication mode between server and clients')

    return parser.parse_args(argv)


def configure_logging(config_file: Optional[IO]=None):

    if config_file:
        logging.config.fileConfig(config_file)
    else:
        logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)


class TcpServerHandler(socketserver.StreamRequestHandler):

    def setup(self):
        super().setup()
        self.delegate = Mdls(self.rfile, self.wfile)

    def handle(self):
        self.delegate.start()


def main():
    args = parse_arguments()
    configure_logging(args.logging_config)

    logger = logging.getLogger('mdls.main')

    if args.mode == 'stdio':
        logger.info('Using stdio')
        server = Mdls(sys.stdin.buffer, sys.stdout.buffer)
        server.start()
    elif args.mode == 'tcp':
        server = socketserver.TCPServer((args.host, args.port),
                                        TcpServerHandler)
        server.allow_reuse_address = True
        try:
            logger.info('Serving (%s, %s)', args.host, args.port)
            server.serve_forever()
        finally:
            logger.info('Shutting down')
            server.server_close()
    else:
        raise ArgumentError('Unknown mode {}'.format(args.mode))
