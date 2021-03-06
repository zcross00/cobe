# Copyright (C) 2012 Peter Teichman

import abc
import re
import types


class Tokenizer(object):
    """Base class for a Tokenizer

    A Tokenizer includes methods for converting a text string to and
    from a list of tokens.

    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def split(self, text):  # pragma: no cover
        pass

    @abc.abstractmethod
    def join(self, tokens):  # pragma: no cover
        pass


class WhitespaceTokenizer(Tokenizer):
    """A simple tokenizer that splits and joins with spaces.

    This is useful during testing or in applications that don't need
    to handle punctuation separately from words.

    """
    def split(self, text):
        return text.split()

    def join(self, tokens):
        return " ".join(tokens)


class MegaHALTokenizer(Tokenizer):
    """A traditional MegaHAL style tokenizer.

    This considers any of these to be a token:
    * one or more consecutive alpha characters (plus apostrophe)
    * one or more consecutive numeric characters
    * one or more consecutive punctuation/space characters (not apostrophe)

    This tokenizer ignores differences in capitalization.

    """
    def split(self, phrase):
        if not isinstance(phrase, types.UnicodeType):
            raise TypeError("Input must be Unicode")

        if len(phrase) == 0:
            return []

        # add ending punctuation if it is missing
        if phrase[-1] not in ".!?":
            phrase = phrase + "."

        words = re.findall("([A-Z']+|[0-9]+|[^A-Z'0-9]+)", phrase.upper(),
                           re.UNICODE)
        return words

    def join(self, words):
        """Re-join a MegaHAL style response.

        Capitalizes the first alpha character in the reply and any
        alpha character that follows [.?!] and a space.

        """
        chars = list(u"".join(words))
        start = True

        for i in xrange(len(chars)):
            char = chars[i]
            if char.isalpha():
                if start:
                    chars[i] = char.upper()
                else:
                    chars[i] = char.lower()

                start = False
            else:
                if i > 2 and chars[i - 1] in ".?!" and char.isspace():
                    start = True

        return u"".join(chars)


class CobeTokenizer(Tokenizer):
    """A tokenizer that is somewhat improved from MegaHAL.

    These are considered tokens:
    * one or more consecutive Unicode word characters (plus apostrophe
      and dash)
    * one or more consecutive Unicode non-word characters, possibly with
      internal whitespace
    * the whitespace between word or non-word tokens
    * an HTTP url, [word]: followed by any run of non-space characters.

    This tokenizer collapses multiple spaces in a whitespace token
    into a single space character.

    It preserves differences in case. foo, Foo, and FOO are different
    tokens.

    """
    def __init__(self):
        # Add hyphen to the list of possible word characters, so hyphenated
        # words become one token (e.g. hy-phen). But don't remove it from
        # the list of non-word characters, so if it's found entirely within
        # punctuation it's a normal non-word (e.g. :-( )

        self.regex = re.compile("(\w+:\S+"  # urls
                                "|[\w'-]+"  # words
                                "|[^\w\s][^\w]*[^\w\s]"  # multiple punctuation
                                "|[^\w\s]"  # a single punctuation character
                                "|\s+)",    # whitespace
                                re.UNICODE)

    def split(self, phrase):
        if not isinstance(phrase, types.UnicodeType):
            raise TypeError("Input must be Unicode")

        # Strip leading and trailing whitespace. This might not be the
        # correct choice long-term, but in the brain it prevents edges
        # from the root node that have has_space set.
        phrase = phrase.strip()

        if len(phrase) == 0:
            return []

        tokens = self.regex.findall(phrase)

        # collapse runs of whitespace into a single space
        space = u" "
        for i, token in enumerate(tokens):
            if token[0] == " " and len(token) > 1:
                tokens[i] = space

        return tokens

    def join(self, words):
        return u"".join(words)
