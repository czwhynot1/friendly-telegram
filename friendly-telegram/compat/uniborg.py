from .util import get_cmd_name, MarkdownBotPassthrough
from .. import loader

from functools import wraps

import logging
import telethon
import sys
import re
import datetime
import tempfile
import asyncio

logger = logging.getLogger(__name__)


class UniborgClient:
    instance_count = 0

    class __UniborgShimMod__Base(loader.Module):
        def __init__(self, borg):
            self._borg = borg
            self.commands = borg._commands
            self.name = type(self).__name__

        async def watcher(self, message):
            for w in self._borg._watchers:
                await w(message)

        async def client_ready(self, client, db):
            self._client = client

    def registerfunc(self, cb):
        self._wrapper = type("UniborgShim__" + self._module, (self.__UniborgShimMod__Base,), dict())(self)
        cb(self._wrapper)

    def __init__(self, module_name):
        self.instance_id = -1
        self._storage = None  # TODO
        self._config = UniborgConfig()
        self._commands = {}
        self._watchers = []
        self._unknowns = []
        self._wrapper = None  # Set in registerfunc
        self._module = module_name
        sys.modules[self._module].__dict__["logger"] = logging.getLogger(self._module)
        sys.modules[self._module].__dict__["storage"] = self._storage
        sys.modules[self._module].__dict__["Config"] = self._config

    def _ensure_unknowns(self):
        if self.instance_id < 0:
            type(self).instance_count += 1
            self.instance_id = type(self).instance_count
        self._commands["borgcmd" + str(self.instance_id)] = self._unknown_command

    def _unknown_command(self, message):
        message.message = "." + message.message[len("borgcmd" + str(self.instance_id)) + 1:]
        return asyncio.gather(*[uk(message, "") for uk in self._unknowns])

    def on(self, event):
        def subreg(func):
            logger.debug(event)

            self._module = func.__module__
            sys.modules[self._module].__dict__["register"] = self.registerfunc

            if event.outgoing:
                # Command based thing
                use_unknown = False
                if not event.pattern:
                    self._ensure_unknowns()
                    use_unknown = True
                cmd = get_cmd_name(event.pattern.__self__.pattern)
                if not cmd:
                    self._ensure_unknowns()
                    use_unknown = True

                @wraps(func)
                def commandhandler(message, pre="."):
                    """Closure to execute command when handler activated and regex matched"""
                    logger.debug("Command triggered")
                    match = re.match(event.pattern.__self__.pattern, pre + message.message, re.I)
                    if match:
                        logger.debug("and matched")
                        message.message = pre + message.message  # Framework strips prefix, give them a generic one
                        event2 = MarkdownBotPassthrough(message)
                        # Try to emulate the expected format for an event
                        event2.text = list(str(message.message))
                        event2.pattern_match = match
                        event2.message = MarkdownBotPassthrough(message)
                        # Put it off as long as possible so event handlers register
                        sys.modules[self._module].__dict__["borg"] = self._wrapper._client

                        return func(event2)
                        # Return a coroutine
                    else:
                        logger.debug("but not matched cmd " + message.message
                                     + " regex " + event.pattern.__self__.pattern)
                if use_unknown:
                    self._unknowns += [commandhandler]
                else:
                    self._commands[cmd] = commandhandler
            elif event.incoming:
                @wraps(func)
                def watcherhandler(message):
                    """Closure to execute watcher when handler activated and regex matched"""
                    match = re.match(event.pattern.__self__.pattern, message.message, re.I)
                    if match:
                        logger.debug("and matched")
                        message.message = message.message  # Framework strips prefix, give them a generic one
                        event2 = MarkdownBotPassthrough(message)
                        # Try to emulate the expected format for an event
                        event2.text = list(str(message.message))
                        event2.pattern_match = match
                        event2.message = MarkdownBotPassthrough(message)

                        return func(event2)
                    return asyncio.gather()
                    # Return a coroutine
                self._watchers += [watcherhandler]  # Add to list of watchers so we can call later.
            else:
                logger.error("event not incoming or outgoing")
                return func
            return func
        return subreg


class Uniborg:
    def __init__(self, clients):
        self.__all__ = "util"


class UniborgUtil:
    def __init__(self, clients):
        pass

    def admin_cmd(self, *args, **kwargs):
        """Uniborg uses this for sudo users but we don't have that concept."""
        if len(args) > 0:
            if len(args) != 1:
                raise TypeError("Takes exactly 0 or 1 args")
            kwargs["pattern"] = args[0]
        if not (kwargs["pattern"].startswith(".") or kwargs["pattern"].startswith(r"\.")):
            kwargs["pattern"] = r"\." + kwargs["pattern"]
        if not ("incoming" in kwargs.keys() or "outgoing" in kwargs.keys()):
            kwargs["outgoing"] = True
        return telethon.events.NewMessage(**kwargs)

    async def progress(self, *args, **kwargs):
        pass

    async def is_read(self, *args, **kwargs):
        return False  # Meh.

    def humanbytes(self, size):
        return str(size) + " bytes"  # Meh.

    def time_formatter(ms):
        return str(datetime.timedelta(milliseconds=ms))


class UniborgConfig:
    TMP_DOWNLOAD_DIRECTORY = tempfile.mkdtemp()

    GOOGLE_CHROME_BIN = None
    SCREEN_SHOT_LAYER_ACCESS_KEY = None
    PRIVATE_GROUP_BOT_API_ID = None
    IBM_WATSON_CRED_USERNAME = None
    IBM_WATSON_CRED_PASSWORD = None
    HASH_TO_TORRENT_API = None
    TELEGRAPH_SHORT_NAME = "UniborgShimFriendlyTelegram"
    OCR_SPACE_API_KEY = None
    G_BAN_LOGGER_GROUP = None
    TG_GLOBAL_ALBUM_LIMIT = 9  # What does this do o.O?
    TG_BOT_TOKEN_BF_HER = None
    TG_BOT_USER_NAME_BF_HER = None
    ANTI_FLOOD_WARN_MODE = None
    MAX_ANTI_FLOOD_MESSAGES = 10
    CHATS_TO_MONITOR_FOR_ANTI_FLOOD = []
    REM_BG_API_KEY = None
    NO_P_M_SPAM = False
    MAX_FLOOD_IN_P_M_s = 3  # Default from spechide
    NC_LOG_P_M_S = False
    PM_LOGGR_BOT_API_ID = -100
    DB_URI = None
    NO_OF_BUTTONS_DISPLAYED_IN_H_ME_CMD = 5
    COMMAND_HAND_LER = r"\."
    SUDO_USERS = set()  # Don't add anyone here!
    VERY_STREAM_LOGIN = None
    VERY_STREAM_KEY = None
    G_DRIVE_CLIENT_ID = None
    G_DRIVE_CLIENT_SECRET = None
    G_DRIVE_AUTH_TOKEN_DATA = None
    TELE_GRAM_2FA_CODE = None
    GROUP_REG_SED_EX_BOT_S = None
    OPEN_LOAD_LOGIN = None
    OPEN_LOAD_KEY = None
    GOOGLE_CHROME_DRIVER = None

    # === SNIP ===
    # this stuff should never get changed, because its either unused or dangerous
    MAX_MESSAGE_SIZE_LIMIT = 4095
    UB_BLACK_LIST_CHAT = set()
    LOAD = []
    NO_LOAD = []
    CHROME_DRIVER = GOOGLE_CHROME_DRIVER
    CHROME_BIN = GOOGLE_CHROME_BIN
    TEMP_DIR = TMP_DOWNLOAD_DIRECTORY
