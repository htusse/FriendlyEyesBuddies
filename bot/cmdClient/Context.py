from collections import namedtuple

import datetime
import discord
import asyncio  # noqa
# from .logger import log
from . import lib

from . import cmdClient  # noqa
from .Command import Command  # noqa


FlatContext = namedtuple(
    'FlatContext',
    ('msg',
     'ch',
     'guild',
     'arg_str',
     'cmd',
     'alias',
     'author',
     'prefix',
     'cleanup_on_edit',
     'reparse_on_edit',
     'sent_messages')
)


class Context(object):
    __slots__ = (
        'client',
        'msg',
        'ch',
        'guild',
        'objects',
        'args',
        'arg_str',
        'cmd',
        'alias',
        'author',
        'prefix',
        'sent_messages',
        'cleanup_on_edit',
        'reparse_on_edit',
        'tasks'
    )

    def __init__(self, client, **kwargs):
        self.client = client  # type: cmdClient.cmdClient

        self.msg = kwargs.pop("message", None)  # type: discord.Message

        self.ch = self.msg.channel if self.msg is not None else kwargs.pop("channel", None)  # type: discord.Channel
        self.guild = self.msg.guild if self.msg is not None else kwargs.pop("guild", None)  # type: discord.Guild
        self.author = self.msg.author if self.msg is not None else kwargs.pop("author", None)  # type: discord.User

        self.arg_str = kwargs.pop("arg_str", None)  # type: str
        self.cmd = kwargs.pop("cmd", None)  # type: Command
        self.alias = kwargs.pop("alias", None)  # type: str
        self.prefix = kwargs.pop("prefix", None)  # type: str

        self.cleanup_on_edit = kwargs.pop(
            "cleanup_on_edit",
            self.cmd.handle_edits if self.cmd is not None else True
        )

        self.reparse_on_edit = kwargs.pop(
            "reparse_on_edit",
            self.cmd.handle_edits if self.cmd is not None else True
        )

        # Argument string, intended to be overriden by argument parsers
        self.args = self.arg_str  # type:str

        # Cache of messages sent in this context.
        self.sent_messages = []  # type: List[discord.Message]

        # Context tasks, including for the final wrapped command
        self.tasks = []  # type: List[asyncio.Task]

    @classmethod
    def util(cls, util_func):
        """
        Decorator to make a utility function available as a Context instance method
        """
        setattr(cls, util_func.__name__, util_func)

    def flatten(self):
        """
        Returns a flat version of the current context for debugging or caching.
        Does not store `objects`.
        Intended to be overriden if different cache data is needed.
        """
        return FlatContext(
            msg=self.msg.id if self.msg else None,
            ch=self.ch.id if self.ch else None,
            guild=self.guild.id if self.guild else None,
            arg_str=self.arg_str,
            cmd=self.cmd.name if self.cmd else None,
            alias=self.alias,
            author=self.author.id if self.author else None,
            prefix=self.prefix,
            cleanup_on_edit=self.cleanup_on_edit,
            reparse_on_edit=self.reparse_on_edit,
            sent_messages=tuple([message.id for message in self.sent_messages])
        )


@Context.util
async def reply(ctx, content=None, allow_everyone=False, **kwargs):
    """
    Helper function to reply in the current channel.
    """
    if not allow_everyone:
        if content:
            content = lib.sterilise_content(content)

    message = await ctx.ch.send(content=content, **kwargs)
    ctx.sent_messages.append(message)
    return message


@Context.util
async def error_reply(ctx, error_str):
    """
    Notify the user of a user level error.
    Typically, this will occur in a red embed, posted in the command channel.
    """
    embed = discord.Embed(
        colour=discord.Colour.red(),
        description=error_str,
        timestamp=datetime.datetime.utcnow()
    )
    try:
        message = await ctx.ch.send(embed=embed)
        ctx.sent_messages.append(message)
        return message
    except discord.Forbidden:
        message = await ctx.reply(error_str)
        ctx.sent_messages.append(message)
        return message
