from io import StringIO
import pkg_resources as pkg
import unittest
from unittest.mock import patch

from xmpinpdf import XmpPdf, commandline, IOErrorNoTrailer

class TestSuite(unittest.TestCase):

    def test_no_file_trailer_keyword(self):
        """
        Should error out if not file trailer keyword.
        """
        filename = pkg.resource_filename(__name__, 'data/pgf_rcupdate1.pdf')
        with self.assertRaises(IOErrorNoTrailer):
            XmpPdf(filename)

    def test_bad_startxref_value(self):
        """
        Should error out if the startxref offset is wrong.
        """
        filename = pkg.resource_filename(__name__, 'data/QuestionMark.pdf')
        with self.assertRaises(IOError):
            XmpPdf(filename)

    def test_trailer_dictionary_with_periods(self):
        filename = pkg.resource_filename(__name__, 'data/Print.pdf')
        pdf = XmpPdf(filename)
        self.assertEqual(pdf.version, 1.3)

    def test_trailer_dictionary_with_newlines(self):
        filename = pkg.resource_filename(__name__,
                                         'data/SKEEntity_Animation.pdf')
        pdf = XmpPdf(filename)
        self.assertEqual(pdf.version, 1.5)

    def test_1p6(self):
        filename = pkg.resource_filename(__name__, 'data/INSP_CATHDR.pdf')

        pdf = XmpPdf(filename)
        self.assertEqual(pdf.version, 1.6)
        self.assertEqual(pdf.trailer_dictionary['Size'], 24)
        self.assertEqual(pdf.trailer_dictionary['Root'].object_number, 1)
        self.assertEqual(pdf.trailer_dictionary['Root'].generation_number, 0)
        self.assertEqual(pdf.trailer_dictionary['Info'].object_number, 22)
        self.assertEqual(pdf.trailer_dictionary['Info'].generation_number, 0)
        self.assertEqual(pdf.startxref, 9293)

        self.assertEqual(len(pdf.xref_table.keys()), 24)
        self.assertEqual(pdf.xref_table[23].offset, 2338)
        self.assertEqual(pdf.xref_table[23].generation_number, 0)
        self.assertEqual(pdf.xref_table[23].free, False)

        self.assertEqual(pdf.document['Type'], 'Catalog')

    def test_1p3(self):
        filename = pkg.resource_filename(__name__, 'data/Rose94.pdf')

        pdf = XmpPdf(filename)
        self.assertEqual(pdf.version, 1.3)
        self.assertEqual(pdf.trailer_dictionary['Size'], 126)
        self.assertEqual(pdf.trailer_dictionary['Root'].object_number, 1)
        self.assertEqual(pdf.trailer_dictionary['Root'].generation_number, 0)
        self.assertEqual(pdf.trailer_dictionary['Info'].object_number, 2)
        self.assertEqual(pdf.trailer_dictionary['Info'].generation_number, 0)
        self.assertEqual(pdf.startxref, 147839)

        # Just one subsection in the xref table, 126 entries in that section
        self.assertEqual(len(pdf.xref_table.keys()), 126)
        self.assertEqual(pdf.xref_table[125].offset, 132499)
        self.assertEqual(pdf.xref_table[125].generation_number, 0)
        self.assertEqual(pdf.xref_table[125].free, False)

    def test_1p4(self):
        """
        """
        filename = pkg.resource_filename(__name__, 'data/BlueSquare.pdf')

        pdf = XmpPdf(filename)

        self.assertEqual(pdf.version, 1.4)
        self.assertEqual(pdf.trailer_dictionary['Size'], 4)
        self.assertEqual(pdf.startxref, 116)

        # Just one subsection in the xref table, 126 entries in that section
        self.assertEqual(len(pdf.xref_table.keys()), 7)
        self.assertEqual(pdf.xref_table[6].offset, 436)
        self.assertEqual(pdf.xref_table[6].generation_number, 0)
        self.assertEqual(pdf.xref_table[6].free, False)

    def test_trailer_with_newlines(self):
        """
        Must work on trailer sections with embedded newlines.

        Sometimes the trailer section has newlines embedded in the value
        """
        filename = pkg.resource_filename(__name__,
                                         'data/Mailbox_Subscription.pdf')

        pdf = XmpPdf(filename)

        self.assertEqual(pdf.version, 1.3)
        self.assertEqual(pdf.trailer_dictionary['Size'], 12)
        self.assertEqual(pdf.startxref, 1820)

        self.assertEqual(len(pdf.xref_table.keys()), 12)
        self.assertEqual(pdf.xref_table[11].offset, 1597)
        self.assertEqual(pdf.xref_table[11].generation_number, 0)
        self.assertEqual(pdf.xref_table[11].free, False)

    def test_commandline(self):
        filename = pkg.resource_filename(__name__, 'data/BlueSquare.pdf')
        with patch('sys.argv', new=['', '-i', filename]):
            with patch('sys.stdout', new=StringIO()) as fake_stdout:
                commandline.pdfinfo()
                value = fake_stdout.getvalue()
        self.assertTrue('Version:  1.4' in value)
