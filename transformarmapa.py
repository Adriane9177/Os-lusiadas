from lxml import etree

xml = etree.parse("Lusiadas_Canto1_marcado.xml")
xsl = etree.parse("mapa.xsl")

transform = etree.XSLT(xsl)
resultado = transform(xml)

with open("mapa.html", "wb") as f:
    f.write(etree.tostring(resultado, pretty_print=True, encoding="UTF-8"))