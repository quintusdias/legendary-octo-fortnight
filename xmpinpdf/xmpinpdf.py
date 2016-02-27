import collections
import os
import re

# postman

_IND_REF_REGEX = re.compile('''(?P<object_number>(\d+))\s
                               (?P<generation_number>(\d+))\sR''', re.VERBOSE)

# There may be whitespace after the opening chevron.
# The dictionary string consists of
#   1) a slash
#   2) an indeterminate amount of text that may include whitespace, brackets
#      angle brackets, the dot
#   3) possible whitespace
#   4) 1-3 repeated
_DICTIONARY_PATTERN = '<<\s*(?P<dict_string>((/[\w\s[\]<>.()-]+)+))>>'


IndirectReference = collections.namedtuple('IndirectReference',
                                           ['object_number',
                                            'generation_number'])
XRefTable = collections.namedtuple('XRefTable', ['offset', 'generation_number',
                                                 'free'])


class IOErrorNoTrailer(IOError):
    """
    PDFs without a trailer keyword are not supported
    """
    pass


class XmpPdf(object):
    """
    Attributes
    ----------
    filename : file
        Path to PDF file.
    trailer_offset : int
        Byte offset to the trailer section.
    version : float
        Version claimed by PDF file.
    """

    def __init__(self, filename):
        self.filename = filename
        self.eol_chars = [b'\n', b'\r']

        self._f = open(self.filename, 'rb')

        self.read_header()
        self.read_trailer()
        self.parse_cross_reference_table()

        self.parse_document()

    def __del__(self):
        if hasattr(self, '_f'):
            self._f.close()

    def __str__(self):
        msg = ('Filename:  {filename}\n'
               'Version:  {version}')
        msg = msg.format(version=self.version,
                         filename=self.filename)
        return msg

    def parse_document(self):
        try:
            root_obj_num = self.trailer_dictionary['Root'].object_number
        except KeyError:
            self.document = None
            return

        # How many bytes to read?  Start at the dictionary object, read until
        # the next non-free object.
        #
        # So collect all the non-free objects and sort them.
        lst = []
        for obj in self.xref_table.values():
            if not obj.free:
                lst.append(obj.offset)
        lst = sorted(lst)

        self._f.seek(self.xref_table[root_obj_num].offset)

        # Read the least amount of data possible.
        idx = lst.index(self.xref_table[root_obj_num].offset)
        if idx == len(lst) - 1:
            # Read until the end of the file.
            data = self._f.read().decode('utf-8').rstrip()
        else:
            num_bytes = lst[idx + 1] - lst[idx]
            data = self._f.read(num_bytes).decode('utf-8').rstrip()

        m = re.search(_DICTIONARY_PATTERN, data)
        dictionary_string = m.group('dict_string')

        pattern = '''/(?P<key>\w+)
                     ((\s(?P<obj_num>\d+)\s
                      (?P<gnum>\d+)\sR)|
                      (\s?\/(?P<value>\w+)))'''
        regex = re.compile(pattern, re.VERBOSE)

        document = {}
        for m in regex.finditer(dictionary_string):
            g = m.groupdict()
            key = g['key']
            if g['value'] is None:
                kwargs = {
                    'object_number': int(g['obj_num']),
                    'generation_number': int(g['gnum']),
                }
                document[key] = IndirectReference(**kwargs)
            else:
                document[key] = g['value']

        self.document = document

    def consume_whitespace(self):
        """
        Read until we encounter a non-whitespace character.
        """
        while True:
            pos = self._f.tell()
            b = self._f.read(1)
            if b not in self.eol_chars:
                self._f.seek(pos)
                return

    def parse_cross_reference_table(self):
        """
        Read the cross reference table.
        """
        self._f.seek(self.startxref)

        token = self._f.read(4)
        if token != b'xref':
            message = 'Expected to find xref token, got "{token}" instead.'
            message = message.format(token=token.decode('utf-8'))
            raise IOError(message)
        self.consume_whitespace()
        self.xref_table = {}
        while True:
            try:
                self.read_subsection()
            except IOError:
                break

    def get_line_of_text(self):
        """
        Read line of text from binary file.
        """
        lst = []
        while True:
            char = self._f.read(1)
            if char in self.eol_chars:
                break
            lst.append(char)
        return b''.join(lst).decode('utf-8')

    def read_subsection(self):
        line = self.get_line_of_text()
        regex = re.compile("(?P<obj_num>\d+)\s(?P<num_objs>\d+)")
        m = regex.search(line)
        if m is None:
            raise IOError('Not reading a subsection anymore.')
        g = m.groupdict()
        obj_num = int(g['obj_num'])
        num_objs = int(g['num_objs'])
        regex = re.compile("""(?P<offset>\d+)\s
                              (?P<generation_number>\d+)\s
                              (?P<in_use_keyword>f|n)""", re.VERBOSE)
        for obj_num in range(num_objs):
            xref_line = self._f.read(20).decode('utf-8').rstrip()
            m = regex.search(xref_line)
            try:
                g = m.groupdict()
            except AttributeError:
                message = ('Error encountered reading the cross reference '
                           'table.  The file may not be a valid PDF.')
                raise IOError(message)
            offset = int(g['offset'])
            generation_number = int(g['generation_number'])
            free = True if g['in_use_keyword'] == 'f' else False
            entry = XRefTable(offset=offset,
                              generation_number=generation_number,
                              free=free)
            self.xref_table[obj_num] = entry

    def read_trailer(self):
        """
        Read PDF file trailer.

        Extract the offset of the last cross reference section along with the
        trailer dictionary.
        """
        self.position_to_trailer()

        # Should be able to process the trailer as text.
        data = self._f.read().decode('utf-8')

        # locate the trailer dictionary
        m = re.search(_DICTIONARY_PATTERN, data)
        text = m.group('dict_string')
        items = [item.strip() for item in text.split('/') if item != '']

        d = {}
        for item in items:
            items = item.split()
            key = items[0]
            value = ' '.join(items[1:])
            m = _IND_REF_REGEX.match(value)
            if m is None:
                try:
                    d[key] = int(value)
                except ValueError:
                    d[key] = value
            else:
                g = m.groupdict()
                kwargs = {
                    'object_number': int(g['object_number']),
                    'generation_number': int(g['generation_number']),
                }
                d[key] = IndirectReference(**kwargs)
        self.trailer_dictionary = d

        regex = re.compile("""
                           startxref\s
                           (?P<startxref>\d+)\s
                           %%EOF
                           """, re.VERBOSE)
        m = regex.search(data)
        self.startxref = int(m.group('startxref'))

    def position_to_trailer(self):
        """
        The trailer should be close to the end of the file, we are just not
        sure where.
        """
        end_pos = self._f.seek(0, os.SEEK_END)
        count = 2
        while True:
            pos = max(0, end_pos - 10 ** count)
            self._f.seek(pos)
            data = self._f.read()
            trailer_offset = data.find(b'trailer')
            if trailer_offset == -1:
                # Must go back further.
                count += 1
                if count > 5:
                    message = ('Could not locate the file trailer.  '
                               'PDFs without a file trailer are not '
                               'supported.')
                    raise IOErrorNoTrailer(message)
                continue

            # We found it, maybe?
            self._f.seek(pos + trailer_offset)
            self.trailer_offset = self._f.tell()
            return

    def _read_trailer(self):
        data = self._f.read()
        pos = data.find(b'trailer')
        if pos == -1:
            raise IOError('Did not find the trailer')

    def read_header(self):
        """
        Read PDF file header.

        Extract the PDF version number.
        """
        data = self._f.read(8)
        m = re.search('%PDF-(?P<major>\d)\.(?P<minor>\d)',
                      data.decode('utf-8'))
        if m is None:
            message = 'Bad header line {header}, {filename} is not a PDF.'
            message = message.format(header=data,
                                     filename=self.filename)
            raise IOError(message)

        g = m.groupdict()
        self.version = float(g['major']) + float(g['minor'])/10
