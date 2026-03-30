<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet 
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:tei="http://www.tei-c.org/ns/1.0"
  version="1.0">
  
  <xsl:output method="html" encoding="UTF-8" indent="yes"/>
  
  <!-- carregar autoridades -->
  <xsl:variable name="autoridades" select="document('autoridade_lusiadas.xml')"/>
  
  <xsl:template match="/">
    
    <html>
      <head>
        <meta charset="UTF-8"/>
        
        <title>Os Lusíadas - Edição Digital</title>
        
        <style>
          body {
          font-family: Georgia, serif;
          margin: 0;
          display: flex;
          }
          
          /* TEXTO */
          #conteudo {
          width: 65%;
          padding: 40px;
          }
          
          .estrofe {
          margin-bottom: 25px;
          }
          
          .verso {
          display: block;
          margin-left: 20px;
          }
          
          /* ENTIDADES */
          .pessoa {
          color: #1f77b4;
          font-weight: bold;
          cursor: pointer;
          }
          
          .mito {
          color: #9467bd;
          font-style: italic;
          cursor: pointer;
          }
          
          .lugar {
          color: #2ca02c;
          cursor: pointer;
          }
          
          /* PAINEL LATERAL */
          #painel {
          display: none;
          position: fixed;
          top: 20%;
          left: 50%;
          transform: translate(-50%, -20%);
          width: 400px;
          background: white;
          border: 2px solid #333;
          padding: 20px;
          border-radius: 10px;
          box-shadow: 0 0 10px rgba(0,0,0,0.3);
          z-index: 1000;
          }
          
          #painel h2 {
          margin-top: 0;
          }
          
          #painel a {
          display: inline-block;
          margin-top: 10px;
          color: blue;
          }
        </style>
        
        <script>
          function mostrarInfo(nome, descricao, link) {
          document.getElementById("painel").style.display = "block";
          document.getElementById("titulo").innerText = nome;
          document.getElementById("descricao").innerText = descricao;
          
          let linkEl = document.getElementById("link");
          
          if(link &amp;&amp; link !== "") {
          linkEl.href = link;
          linkEl.style.display = "inline";
          } else {
          linkEl.style.display = "none";
          }
          }
          
          function fecharPainel() {
          document.getElementById("painel").style.display = "none";
          }
        </script>
        
      </head>
      
      <body>
        
        <!-- TEXTO -->
        <div id="conteudo">
          <h1>Os Lusíadas</h1>
          <xsl:apply-templates/>
        </div>
        
        <div id="painel">
          <button onclick="fecharPainel()">X</button>
          <h2 id="titulo"></h2>
          <p id="descricao"></p>
          <a id="link" target="_blank">Abrir no Wikidata</a>
        </div>

        <!-- PAINEL -->
        <div id="painel">
          <h2 id="titulo">Clique em uma entidade</h2>
          <p id="descricao">A informação aparecerá aqui.</p>
          <a id="link" target="_blank">Abrir no Wikidata</a>
        </div>
        
      </body>
    </html>
    
  </xsl:template>
  
  <!-- ESTROFES -->
  <xsl:template match="tei:lg">
    <div class="estrofe">
      <xsl:apply-templates/>
    </div>
  </xsl:template>
  
  <!-- VERSOS -->
  <xsl:template match="tei:l">
    <div class="verso">
      <xsl:apply-templates/>
    </div>
  </xsl:template>
  
  <!-- FUNÇÃO PARA PEGAR ID -->
  <xsl:template name="get-id">
    <xsl:param name="ref"/>
    <xsl:value-of select="substring-after($ref, '#')"/>
  </xsl:template>
  
  <!-- ===== PESSOAS ===== -->
  <xsl:template match="tei:persName | tei:rs[@type='person']">
    
    <xsl:variable name="id">
      <xsl:call-template name="get-id">
        <xsl:with-param name="ref" select="@ref"/>
      </xsl:call-template>
    </xsl:variable>
    
    <xsl:variable name="entry"
                  select="$autoridades//person[@xml:id=$id]"/>
    
    <span>
      
      <!-- classe -->
      <xsl:attribute name="class">
        <xsl:choose>
          <xsl:when test="@type='myth'">mito</xsl:when>
          <xsl:otherwise>pessoa</xsl:otherwise>
        </xsl:choose>
      </xsl:attribute>
      
      <!-- clique -->
      <xsl:attribute name="onclick">
        <xsl:text>mostrarInfo('</xsl:text>
        <xsl:value-of select="normalize-space(.)"/>
        <xsl:text>','</xsl:text>
        <xsl:value-of select="normalize-space($entry/note)"/>
        <xsl:text>','</xsl:text>
        <xsl:value-of select="string($entry/@ref)"/>
        <xsl:text>')</xsl:text>
      </xsl:attribute>
      
      <xsl:apply-templates/>
      
    </span>
    
  </xsl:template>
  
  <!-- ===== LUGARES ===== -->
  <xsl:template match="tei:placeName | tei:rs[@type='place']">
    
    <xsl:variable name="id">
      <xsl:call-template name="get-id">
        <xsl:with-param name="ref" select="@ref"/>
      </xsl:call-template>
    </xsl:variable>
    
    <xsl:variable name="entry"
                  select="$autoridades//place[@xml:id=$id]"/>
    
    <span class="lugar">
      
      <xsl:attribute name="onclick">
        <xsl:text>mostrarInfo('</xsl:text>
        <xsl:value-of select="normalize-space(.)"/>
        <xsl:text>','</xsl:text>
        <xsl:value-of select="normalize-space($entry/note)"/>
        <xsl:text>','</xsl:text>
        <xsl:value-of select="$entry/@ref"/>
        <xsl:text>')</xsl:text>
      </xsl:attribute>
      
      <xsl:apply-templates/>
      
    </span>
    
  </xsl:template>
  
  <!-- TEXTO -->
  <xsl:template match="text()">
    <xsl:value-of select="."/>
  </xsl:template>
  
</xsl:stylesheet>