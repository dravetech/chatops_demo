"""Something."""

import difflib


def diff_filter(orig_string, new_string):
    """Return string with the diff between orig_string and new_string."""
    orig_string = orig_string.splitlines(1)
    new_string = new_string.splitlines(1)

    diff = difflib.unified_diff(orig_string, new_string)
    return '        '.join(diff)


def indent_text(text, indentation='    '):
    """Indent text."""
    return '\n{}'.format(indentation).join(text.split('\n'))
