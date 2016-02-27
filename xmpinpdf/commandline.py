import argparse

from .xmpinpdf import XmpPdf


def pdfinfo():

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', type=str,
                        help='Input PDF file')
    args = parser.parse_args()

    pdf = XmpPdf(args.input)
    print(pdf)
