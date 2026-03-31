from lxml import etree

# Arquivos
xml_file = "Lusiadas_Canto1_marcado.xml"
xsl_file = "transformação1.xsl"
output_file = "saidateste4.html"

# Carregar XML
xml = etree.parse(xml_file)

# Carregar XSLT
xsl = etree.parse(xsl_file)

# Criar transformação
transform = etree.XSLT(xsl)

# Aplicar transformação
resultado = transform(xml)

# Salvar HTML
with open(output_file, "w", encoding="utf-8") as f:
    f.write(str(resultado))

print("HTML gerado com sucesso!")