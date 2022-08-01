"""Library for consistent and visually appealing terminal output."""

import sys
from re import compile

import colorama
from colorama import Fore, Style


class _Prefix:
    """The Prefix class represents text which is prepended to text output.

    Prefixes have an associated colorama color which the prefix text will have.

    Attributes
    ----------
    text : str
        Text displayed as a prefix for a message.
    color : colorama color constant
        Color in which the prefix text will be highlighted.
    """

    # This class variable holds all created Prefix objects.
    _all_prefixes = []

    def __init__(self, prefix_text, colorama_color):
        self.text = prefix_text
        self.color = colorama_color
        _Prefix._all_prefixes.append(self)

    def get_max_length():
        """Returns the number of characters of the longest existing prefix.

        If no prefixes exist, returns 0.
        """

        longest_prefix_length = 0
        for prefix in _Prefix._all_prefixes:
            if len(prefix.text) > longest_prefix_length:
                longest_prefix_length = len(prefix.text)

        return longest_prefix_length


_prefix_info = _Prefix("INFO", Fore.WHITE)
_prefix_ok = _Prefix("OK", Fore.GREEN)
_prefix_success = _Prefix("SUCCESS", Fore.GREEN)
_prefix_debug = _Prefix("DEBUG", Fore.BLUE)
_prefix_input = _Prefix("PROMPT", Fore.CYAN)
_prefix_warning = _Prefix("WARNING", Fore.YELLOW)
_prefix_error = _Prefix("ERROR", Fore.RED)
_prefix_failure = _Prefix("FAILURE", Fore.RED)


class Printer:
    """Printer objects print prefixed output to the specified output stream."""

    # These class variables are needed to keep track of whether colorama has
    # been initialized.
    _num_of_active_printers = 0
    _colorama_previously_initialized = False

    def __init__(self, file=sys.stdout):
        """Constructs a Printer object and sets its default behaviour.

        If the created Printer is the first printer that has been created,
        colorama is initialized.
        If the newly created Printer is the only printer in existence, but
        other Printers have existed previously (as indicated by the
        '_colorama_previously_initialized' class variable), colorama is
        re-initialized.

        Parameters
        ----------
        file : File object
            The file to which the Printer prints text by default (defaults to
            stdout).
        """

        # check if colorama needs to be initialized
        if not Printer._colorama_previously_initialized:
            colorama.init()
            Printer._colorama_previously_initialized = True
        else:
            if Printer._num_of_active_printers == 0:
                colorama.reinit()

        Printer._num_of_active_printers += 1

        self.file = file

    def __del__(self):
        """Deconstructs a Printer object.

        If the deleted Printer is the last one in existence, colorama is
        de-initialized.
        """

        # check if colorama should be de-initialized
        if Printer._num_of_active_printers == 1:
            colorama.deinit()

        Printer._num_of_active_printers -= 1

    def _print_prefixed_output(self, prefix, *args, color_enabled=True,
                               **kwargs):
        """Prints the output with the specified prefix prepended.

        This method works the same as the standard library print() function,
        but with the colored text specified by the input prefix object
        prepended to the printed output.
        The output stream to which the output is printed is the one specified
        in this Printer object's file attribute.

        Parameters
        ----------
        prefix : Prefix object
            The prefix prepended to the output.
        *args : various
            The printable object(s) to be printed.
        color_enabled : bool
            If True, the printed output prefix is colored.
            If False, the printed output prefix is not colored.
        **kwargs : various
            The same keywords which the builtin print() function accepts, with
            the exception of the "file" argument.
        """

        prefix_str = ""
        prefix_text = prefix.text.center(_Prefix.get_max_length())

        if color_enabled:
            prefix_str = f"[{prefix.color}{prefix_text}{Style.RESET_ALL}] "
        else:
            prefix_str = f"[{prefix_text}] "

        print(prefix_str, end='', sep='', file=self.file)
        print(*args, **kwargs, file=self.file)

    def _get_prefixed_input(self, prefix, *args, color_enabled=True, **kwargs):
        """Prints the input prompt with the specified prefix prepended.

        This method works the same as the standard library input() function,
        but with the colored text specified by the input prefix object
        prepended to the printed output.
        The output stream to which the output is printed is always stdout.

        Parameters
        ----------
        prefix : Prefix object
            The prefix prepended to the output.
        *args : various
            The printable object(s) to be printed.
        color_enabled : bool
            If True, the printed output prefix is colored.
            If False, the printed output prefix is not colored.
        **kwargs : various
            The same keywords which the builtin print() function accepts, with
            the exception of the "file" argument.
        """

        prefix_str = ""
        prefix_text = prefix.text.center(_Prefix.get_max_length())

        if color_enabled:
            prefix_str = f"[{prefix.color}{prefix_text}{Style.RESET_ALL}] "
        else:
            prefix_str = f"[{prefix_text}] "

        print(prefix_str, end='', sep='', file=sys.stdout)
        return input(*args, **kwargs)

    def info(self, *args, color_enabled=True, **kwargs):
        """Prints the specified input with an "[INFO] " prefix prepended.

        Parameters
        ----------
        *args : various
            The printable object(s) to be printed.
        color_enabled : Bool
            Whether or not the prefix text is colored.
        **kwargs : various
            The same keywords which the builtin print() function accepts, with
            the exception of the "file" argument.
        """

        self._print_prefixed_output(
            _prefix_info,
            *args,
            color_enabled=color_enabled,
            **kwargs
        )

    def ok(self, *args, color_enabled=True, **kwargs):
        """Prints the specified input with an "[OK] " prefix prepended.

        Parameters
        ----------
        *args : various
            The printable object(s) to be printed.
        color_enabled : Bool
            Whether or not the prefix text is colored.
        **kwargs : various
            The same keywords which the builtin print() function accepts, with
            the exception of the "file" argument.
        """

        self._print_prefixed_output(
            _prefix_ok,
            *args,
            color_enabled=color_enabled,
            **kwargs
        )

    def success(self, *args, color_enabled=True, **kwargs):
        """Prints the specified input with a "[SUCCESS] " prefix prepended.

        Parameters
        ----------
        *args : various
            The printable object(s) to be printed.
        color_enabled : Bool
            Whether or not the prefix text is colored.
        **kwargs : various
            The same keywords which the builtin print() function accepts, with
            the exception of the "file" argument.
        """

        self._print_prefixed_output(
            _prefix_success,
            *args,
            color_enabled=color_enabled,
            **kwargs
        )

    def debug(self, *args, color_enabled=True, **kwargs):
        """Prints the specified input with a "[DEBUG] " prefix prepended.

        Parameters
        ----------
        *args : various
            The printable object(s) to be printed.
        color_enabled : Bool
            Whether or not the prefix text is colored.
        **kwargs : various
            The same keywords which the builtin print() function accepts, with
            the exception of the "file" argument.
        """

        self._print_prefixed_output(
            _prefix_debug,
            *args,
            color_enabled=color_enabled,
            **kwargs
        )

    def warning(self, *args, color_enabled=True, **kwargs):
        """Prints the specified output with a "[WARNING] " prefix prepended.

        Parameters
        ----------
        *args : various
            The printable object(s) to be printed.
        color_enabled : Bool
            Whether or not the prefix text is colored.
        **kwargs : various
            The same keywords which the builtin print() function accepts, with
            the exception of the "file" argument.
        """

        self._print_prefixed_output(
            _prefix_warning,
            *args,
            color_enabled=color_enabled,
            **kwargs
        )

    def error(self, *args, color_enabled=True, **kwargs):
        """Prints the specified output with an "[ERROR] " prefix prepended.

        Parameters
        ----------
        *args : various
            The printable object(s) to be printed.
        color_enabled : Bool
            Whether or not the prefix text is colored.
        **kwargs : various
            The same keywords which the builtin print() function accepts, with
            the exception of the "file" argument.
        """

        self._print_prefixed_output(
            _prefix_error,
            *args,
            color_enabled=color_enabled,
            **kwargs
        )

    def failure(self, *args, color_enabled=True, **kwargs):
        """Prints the specified output with a "[FAILURE] " prefix prepended.

        Parameters
        ----------
        *args : various
            The printable object(s) to be printed.
        color_enabled : Bool
            Whether or not the prefix text is colored.
        **kwargs : various
            The same keywords which the builtin print() function accepts, with
            the exception of the "file" argument.
        """

        self._print_prefixed_output(
            _prefix_failure,
            *args,
            color_enabled=color_enabled,
            **kwargs
        )

    def input(self, *args, color_enabled=True, **kwargs):
        """Prompts the user for input with the "[PROMPT] " prefix prepended.

        Parameters
        ----------
        *args : various
            The printable object(s) to be printed.
        color_enabled : Bool
            Whether or not the prefix text is colored.
        **kwargs : various
            The same keywords which the builtin input() function accepts.
        """

        return self._get_prefixed_input(
            _prefix_input,
            *args,
            color_enabled=color_enabled,
            **kwargs
        )


    def prompt_yes_or_no(self, question: str, ask_until_valid: bool = False):
        """Prompts the user for an answer to the specified yes/no question.

        If 'ask_until_valid' is True, keeps repeating the prompt until the user
        provides recognizable input to answer the question.

        Parameters
        ----------
        question : str
            The question to ask the user while prompting. The string is suffixed
            with " (Yes/No) ".
        ask_until_valid : bool
            If this is set to True and the user provides an ambiguous answer, keeps
            prompting indefinitely until an unambiguous answer is read.

        Returns
        -------
        True : bool
            If the user has answered 'yes'.
        False : bool
            If the user has answered 'no'.
        None : None
            If 'ask_until_valid' is False and the user has provided an ambiguous
            response to the prompt.
        """

        user_input_is_valid = False

        regex_yes = compile(r"^(y)$|^(Y)$|^(YES)$|^(Yes)$|^(yes)$")
        regex_no = compile(r"^(n)$|^(N)$|^(NO)$|^(No)$|^(no)$")

        while(not user_input_is_valid):
            user_input = self.input(f"{question} (Yes/No): ")

            if (regex_yes.match(user_input)):
                return True
            elif (regex_no.match(user_input)):
                return False
            elif (not ask_until_valid):
                return None
