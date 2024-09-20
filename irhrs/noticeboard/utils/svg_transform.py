from django.core.files.storage import default_storage
from lxml import etree
from svgutils.transform import SVGFigure


class SVGFigureCustom(SVGFigure):
    def save(self, fname):
        out = etree.tostring(self.root, xml_declaration=True,
                             standalone=True,
                             pretty_print=True)
        fid = default_storage.open(fname, 'wb')
        fid.write(out)
        fid.close()


def formfile_custom(fname):
    """
    Patch function for svgutils.transform.fromfile
    Open SVG figure from file.

    Parameters
    ----------
    fname : str
        name of the SVG file

    Returns
    -------
    SVGFigure
        newly created :py:class:`SVGFigure` initialised with the file content
    """
    fig = SVGFigureCustom()
    fid = open(fname)
    svg_file = etree.parse(fid)
    fid.close()

    fig.root = svg_file.getroot()
    return fig
