import inspect
import re
import collections

valid_command_re = re.compile(r"^\w+$")


class _Hook():
    """
    :type function: function
    :type type: str
    :type kwargs: dict[str, unknown]
    """

    def __init__(self, function, _type):
        """
        :type function: function
        :type _type: str
        """
        self.function = function
        self.type = _type
        self.kwargs = {}

    def _add_hook(self, kwargs):
        """
        :type kwargs: dict[str, unknown]
        """
        # update kwargs, overwriting duplicates
        self.kwargs.update(kwargs)


class _CommandHook(_Hook):
    """
    :type main_alias: str
    :type aliases: set[str]
    """

    def __init__(self, function):
        """
        :type function: function
        """
        _Hook.__init__(self, function, "command")
        self.aliases = set()
        self.main_alias = None

        if function.__doc__:
            self.doc = function.__doc__.split('\n', 1)[0]
        else:
            self.doc = None

    def add_hook(self, alias_param, kwargs):
        """
        :type alias_param: list[str] | str
        """
        self._add_hook(kwargs)

        if not alias_param:
            alias_param = self.function.__name__
        if isinstance(alias_param, str):
            alias_param = [alias_param]
        if not self.main_alias:
            self.main_alias = alias_param[0]
        for alias in alias_param:
            if not valid_command_re.match(alias):
                raise ValueError("Invalid command name {}".format(alias))
        self.aliases.update(alias_param)


class _RegexHook(_Hook):
    """
    :type regexes: list[re.__Regex]
    """

    def __init__(self, function):
        """
        :type function: function
        """
        _Hook.__init__(self, function, "regex")
        self.regexes = []

    def add_hook(self, regex_param, regex_flags, kwargs):
        """
        :type regex_param: Iterable[str | re.__Regex] | str | re.__Regex
        :type kwargs: dict[str, unknown]
        """
        self._add_hook(kwargs)
        # add all regex_parameters to valid regexes
        if isinstance(regex_param, str):
            # if the parameter is a string, compile and add
            self.regexes.append(re.compile(regex_param, regex_flags))
        elif hasattr(regex_param, "search"):
            # if the parameter is an re.__Regex, just add it
            # we only use regex.search anyways, so this is a good determiner
            self.regexes.append(regex_param)
        else:
            assert isinstance(regex_param, collections.Iterable)
            # if the parameter is a list, add each one
            for re_to_match in regex_param:
                if isinstance(re_to_match, str):
                    re_to_match = re.compile(re_to_match, regex_flags)
                else:
                    # make sure that the param is either a compiled regex, or has a search attribute.
                    assert hasattr(regex_param, "search")
                self.regexes.append(re_to_match)


class _RawHook(_Hook):
    """
    :type triggers: set[str]
    """

    def __init__(self, function):
        """
        :type function: function
        """
        _Hook.__init__(self, function, "irc_raw")
        self.triggers = set()

    def add_hook(self, event_param, kwargs):
        """
        :type event_param: list[str] | str
        :type kwargs: dict[str, unknown]
        """
        self._add_hook(kwargs)

        if isinstance(event_param, str):
            self.triggers.add(event_param)
        else:
            assert isinstance(event_param, list)
            self.triggers.update(event_param)


def _add_hook(func, hook):
    if not hasattr(func, "_cloudbot_hook"):
        func._cloudbot_hook = {}
    else:
        assert hook.type not in func._cloudbot_hook  # in this case the hook should be using the add_hook method
    func._cloudbot_hook[hook.type] = hook


def _get_hook(func, hook_type):
    if hasattr(func, "_cloudbot_hook") and hook_type in func._cloudbot_hook:
        return func._cloudbot_hook[hook_type]

    return None


def _process_options(func, kwargs):
    if not hasattr(func, "_cloudbot_hook"):
        func._cloudbot_hook = {}

    if not "options" in func._cloudbot_hook:
        func._cloudbot_hook["options"] = {}

    options = func._cloudbot_hook["options"]
    if "threaded" in kwargs:
        options["threaded"] = kwargs["threaded"]
    if "async" in kwargs:
        options["threaded"] = not kwargs["async"]


def async(param=None):
    """External async decorator. Can be used directly as a decorator, or with args to return a decorator.
    :type param: function
    """

    def _async_hook(func):
        if not hasattr(func, "_cloudbot_hook"):
            func._cloudbot_hook = {}
        if not "options" in func._cloudbot_hook:
            func._cloudbot_hook["options"] = {}
        options = func._cloudbot_hook["options"]
        options["threaded"] = False
        return func

    if callable(param):  # this decorator is being used directly
        return _async_hook(param)
    else:  # this decorator is being used indirectly, so return a decorator function
        return lambda func: _async_hook(func)


def threaded(param=None):
    """External async decorator. Can be used directly as a decorator, or with args to return a decorator.
    :type param: function
    """

    def _async_hook(func):
        if not hasattr(func, "_cloudbot_hook"):
            func._cloudbot_hook = {}
        if not "options" in func._cloudbot_hook:
            func._cloudbot_hook["options"] = {}
        options = func._cloudbot_hook["options"]
        options["threaded"] = True
        return func

    if callable(param):  # this decorator is being used directly
        return _async_hook(param)
    else:  # this decorator is being used indirectly, so return a decorator function
        return lambda func: _async_hook(func)


def command(param=None, **kwargs):
    """External command decorator. Can be used directly as a decorator, or with args to return a decorator.
    :type param: str | list[str] | function
    """

    def _command_hook(func, alias_param=None):
        hook = _get_hook(func, "command")
        if hook is None:
            hook = _CommandHook(func)
            _add_hook(func, hook)

        hook.add_hook(alias_param, kwargs)
        return func

    if callable(param):  # this decorator is being used directly
        return _command_hook(param)
    else:  # this decorator is being used indirectly, so return a decorator function
        return lambda func: _command_hook(func, alias_param=param)


def event(triggers_param, **kwargs):
    """External event decorator. Must be used as a function to return a decorator
    :type triggers_param: str | list[str]
    """

    def _raw_hook(func):
        hook = _get_hook(func, "irc_raw")
        if hook is None:
            hook = _RawHook(func)
            _add_hook(func, hook)

        hook.add_hook(triggers_param, kwargs)
        return func

    if callable(triggers_param):  # this decorator is being used directly, which isn't good
        raise TypeError("@irc_raw() must be used as a function that returns a decorator")
    else:  # this decorator is being used as a function, so return a decorator
        return lambda func: _raw_hook(func)


def regex(regex_param, flags=0, **kwargs):
    """External regex decorator. Must be used as a function to return a decorator.
    :type regex_param: str | re.__Regex | list[str | re.__Regex]
    :type flags: int
    """

    def _regex_hook(func):
        hook = _get_hook(func, "regex")
        if hook is None:
            hook = _RegexHook(func)
            _add_hook(func, _RegexHook(func))

        hook.add_hook(regex_param, flags, kwargs)
        return func

    if callable(regex_param):  # this decorator is being used directly, which isn't good
        raise TypeError("@regex() hook must be used as a function that returns a decorator")
    else:  # this decorator is being used as a function, so return a decorator
        return lambda func: _regex_hook(func)


def sieve(param=None, **kwargs):
    """External sieve decorator. Can be used directly as a decorator, or with args to return a decorator
    :type param: function | None
    """

    def _sieve_hook(func):
        assert len(inspect.getargspec(func).args) == 3, \
            "Sieve plugin has incorrect argument count. Needs params: bot, input, plugin"

        hook = _get_hook(func, "sieve")
        if hook is None:
            hook = _Hook(func, "sieve")  # there's no need to have a specific SieveHook object
            _add_hook(func, hook)

        hook._add_hook(kwargs)
        return func

    if callable(param):
        return _sieve_hook(param)
    else:
        return lambda func: _sieve_hook(func)


def onload(param=None, **kwargs):
    """External onload decorator. Can be used directly as a decorator, or with args to return a decorator
    :type param: function | None
    """

    def _onload_hook(func):
        hook = _get_hook(func, "onload")
        if hook is None:
            hook = _Hook(func, "onload")
            _add_hook(func, hook)

        hook._add_hook(kwargs)
        return func

    if callable(param):
        return _onload_hook(param)
    else:
        return lambda func: _onload_hook(func)
