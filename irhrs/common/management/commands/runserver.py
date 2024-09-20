import datetime
import os
import sys
from django.conf import settings
from django.core.management.commands.runserver import \
    Command as RunserverCommand
from django.core.management.base import CommandError

from channels.management.commands.runserver import Command as ChannelsRunServer

from channels import __version__
from daphne.endpoints import build_endpoint_description_strings


# Generate a self signed key using
# openssl req -newkey rsa:2048 -new -nodes -x509 -days 3650 -keyout key.pem -out cert.pem
# on chrome : chrome://flags/#allow-insecure-localhost

class Command(ChannelsRunServer):
    def get_ssl_string(self):
        key = os.environ.get('DEV_SSL_PRIVATE_KEY')
        cert = os.environ.get('DEV_SSL_CERT_KEY')
        # key = getattr(settings, 'DEV_SSL_PRIVATE_KEY', None)
        # cert = getattr(settings, 'DEV_SSL_CERT_KEY', None)
        if not (key and cert):
            raise CommandError(
                "PrivateKey and Certificate location is not configured for SSL")
        if not os.path.exists(key):
            raise CommandError("Couldn't find key at %s" % key)
        if not os.path.exists(cert):
            raise CommandError("Couldn't find certificate at %s" % key)
        _string = "ssl:{}:privateKey={}:certKey={}".format(
            self.port, key, cert
        )
        return [_string]

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--ssl",
            action="store_true",
            dest="use_ssl",
            default=False,
            help="Run on SSL",
        )

    def inner_run(self, *args, **options):
        if not options.get("use_asgi", True):
            if hasattr(RunserverCommand, "server_cls"):
                self.server_cls = RunserverCommand.server_cls
            return RunserverCommand.inner_run(self, *args, **options)
        elif options.get('use_ssl'):
            self.protocol = 'https'

        self.stdout.write("Performing system checks...\n\n")
        self.check(display_num_errors=True)
        self.stdout.write("Performing migrations checks...\n\n")
        self.check_migrations()
        quit_command = "CTRL-BREAK" if sys.platform == "win32" else "CONTROL-C"
        now = datetime.datetime.now().strftime("%B %d, %Y - %X")
        self.stdout.write(now)
        if options.get('use_ssl'):
            self.stdout.write(
                "******* Starting SSL Server *******"
            )
        self.stdout.write(
            (
                "Django version %(version)s, using settings %(settings)r\n"
                "Starting ASGI/Channels version %(channels_version)s development server"
                " at %(protocol)s://%(addr)s:%(port)s/\n"
                "Quit the server with %(quit_command)s.\n"
            )
            % {
                "version": self.get_version(),
                "channels_version": __version__,
                "settings": settings.SETTINGS_MODULE,
                "protocol": self.protocol,
                "addr": "[%s]" % self.addr if self._raw_ipv6 else self.addr,
                "port": self.port,
                "quit_command": quit_command,
            }
        )
        endpoints = self.get_ssl_string() if options.get('use_ssl') else \
            build_endpoint_description_strings(host=self.addr,
                                               port=self.port)

        try:
            self.server_cls(
                application=self.get_application(options),
                endpoints=endpoints,
                signal_handlers=not options["use_reloader"],
                action_logger=self.log_action,
                http_timeout=self.http_timeout,
                root_path=getattr(settings, "FORCE_SCRIPT_NAME", "") or "",
                websocket_handshake_timeout=self.websocket_handshake_timeout,
            ).run()
        except KeyboardInterrupt:
            shutdown_message = options.get("shutdown_message", "")
            if shutdown_message:
                self.stdout.write(shutdown_message)
            return

    def get_application(self, options):
        application = super().get_application(options)

        # startup commands
        from irhrs.websocket.consumers.global_consumer import UserOnline
        UserOnline.reset_user_sockets_count()

        return application
