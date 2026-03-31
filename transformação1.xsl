<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet 
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:tei="http://www.tei-c.org/ns/1.0"
  version="1.0">
  
  <xsl:output method="html" encoding="UTF-8" indent="yes"/>
  
  <xsl:variable name="autoridades" select="document('autoridade_lusiadas.xml')"/>
  
  <xsl:template match="/">
    
    <html>
      <head>
        <meta charset="UTF-8"/>
        <title>Os Lusíadas</title>
        
        <style>
          body {
          background-color: #f4ecd8;
          font-family: Georgia, serif;
          margin: 40px;
          }
          
          .estrofe { margin-bottom: 20px; }
          .verso { display: block; margin-left: 20px; }
          
          .pessoa { color: #3b5b6b; cursor: pointer; }
          .mito { color: #6b4c5a; cursor: pointer; }
          .lugar { color: #4f6b4a; cursor: pointer; }
          
          #overlay {
          display:none;
          position:fixed;
          width:100%;
          height:100%;
          background:rgba(0,0,0,0.4);
          top:0;
          left:0;
          }
          
          #painel {
          display:none;
          position:fixed;
          top:50%;
          left:50%;
          transform:translate(-50%,-50%);
          width:400px;
          background:#fdf6e3;
          padding:20px;
          }
          
        </style>
        
        <script>
          <![CDATA[
function mostrarInfo(nome, descricao, link, imagem) {
  document.getElementById("overlay").style.display = "block";
  document.getElementById("painel").style.display = "block";

  document.getElementById("titulo").innerText = nome;
  document.getElementById("descricao").innerText = descricao;

  document.getElementById("link").href = link;
  document.getElementById("imagem").src = imagem;
}

function fecharPainel() {
  document.getElementById("overlay").style.display = "none";
  document.getElementById("painel").style.display = "none";
}
]]>
        </script>
        
      </head>
      
      <body>
        
        <h1>Os Lusíadas</h1>
        
        <xsl:apply-templates/>
        
        <div id="overlay" onclick="fecharPainel()"></div>
        
        <div id="painel">
          <button onclick="fecharPainel()">X</button>
          <h2 id="titulo"></h2>
          <p id="descricao"></p>
          <img id="imagem" style="max-width:100%"/>
          <br/>
          <a id="link" target="_blank">Wikidata</a>
        </div>
        
      </body>
    </html>
    
  </xsl:template>
  
  <!-- versos -->
  <xsl:template match="tei:l">
    <div class="verso">
      <xsl:apply-templates/>
    </div>
  </xsl:template>
  
  <!-- entidades -->
  <xsl:template match="tei:persName | tei:placeName | tei:rs">
    
    <xsl:variable name="id" select="substring-after(@ref,'#')"/>
    <xsl:variable name="entry" select="$autoridades//*[@xml:id=$id]"/>
    
    <span>
      <xsl:attribute name="class">
        <xsl:choose>
          <xsl:when test="@type='myth'">mito</xsl:when>
          <xsl:when test="self::tei:placeName or @type='place'">lugar</xsl:when>
          <xsl:otherwise>pessoa</xsl:otherwise>
        </xsl:choose>
      </xsl:attribute>
      
      <xsl:attribute name="onclick">
        <xsl:text>mostrarInfo('</xsl:text>
        <xsl:value-of select="."/>
        <xsl:text>','</xsl:text>
        <xsl:value-of select="$entry/*[local-name()='note']"/>
        <xsl:text>','</xsl:text>
        <xsl:value-of select="$entry/@ref"/>
        <xsl:text>','</xsl:text>
        <xsl:value-of select="$entry/*[local-name()='graphic']/@url"/>
        <xsl:text>')</xsl:text>
      </xsl:attribute>
      
      <xsl:apply-templates/>
    </span>
    
  </xsl:template>
  
</xsl:stylesheet>