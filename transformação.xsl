<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet 
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:tei="http://www.tei-c.org/ns/1.0"
  version="1.0">
  
  <xsl:output method="html" encoding="UTF-8" indent="yes"/>
  
  <!-- 🔥 carregar arquivo de autoridades -->
  <xsl:variable name="autoridades" select="document('autoridade_lusiadas.xml')"/>
  
  <!-- TEMPLATE PRINCIPAL -->
  <xsl:template match="/">
    <html>
      <head>
        <meta charset="UTF-8"/>
        <style>
          body { font-family: Georgia; margin: 40px; }
          .estrofe { margin-bottom: 25px; }
          .verso { display: block; margin-left: 20px; }
          
          .pessoa { color: blue; font-weight: bold; cursor: pointer; }
          .lugar { color: green; cursor: pointer; }
          .mito { color: purple; font-style: italic; cursor: pointer; }
          
          .tooltip:hover { text-decoration: underline; }
        </style>
      </head>
      
      <body>
        <h1>Os Lusíadas</h1>
        <xsl:apply-templates/>
      </body>
    </html>
  </xsl:template>
  
  <!-- ESTROFE -->
  <xsl:template match="tei:lg">
    <div class="estrofe">
      <xsl:apply-templates/>
    </div>
  </xsl:template>
  
  <!-- VERSO -->
  <xsl:template match="tei:l">
    <div class="verso">
      <xsl:apply-templates/>
    </div>
  </xsl:template>
  
  <!-- ===== FUNÇÃO DE BUSCA ===== -->
  <!-- pega id sem # -->
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
    
    <!-- buscar no arquivo -->
    <xsl:variable name="entry"
                  select="$autoridades//person[@xml:id=$id]"/>
    
    <span>
      <!-- classe -->
      <xsl:attribute name="class">
        <xsl:text>tooltip </xsl:text>
        <xsl:choose>
          <xsl:when test="@type='myth'">mito</xsl:when>
          <xsl:otherwise>pessoa</xsl:otherwise>
        </xsl:choose>
      </xsl:attribute>
      
      <!-- tooltip -->
      <xsl:if test="$entry/note">
        <xsl:attribute name="title">
          <xsl:value-of select="$entry/note"/>
        </xsl:attribute>
      </xsl:if>
      
      <!-- link -->
      <xsl:if test="$entry/@ref">
        <xsl:attribute name="onclick">
          <xsl:text>window.open('</xsl:text>
          <xsl:value-of select="$entry/@ref"/>
          <xsl:text>')</xsl:text>
        </xsl:attribute>
      </xsl:if>
      
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
    
    <span class="lugar tooltip">
      
      <xsl:if test="$entry/note">
        <xsl:attribute name="title">
          <xsl:value-of select="$entry/note"/>
        </xsl:attribute>
      </xsl:if>
      
      <xsl:if test="$entry/@ref">
        <xsl:attribute name="onclick">
          <xsl:text>window.open('</xsl:text>
          <xsl:value-of select="$entry/@ref"/>
          <xsl:text>')</xsl:text>
        </xsl:attribute>
      </xsl:if>
      
      <xsl:apply-templates/>
    </span>
    
  </xsl:template>
  
  <!-- TEXTO -->
  <xsl:template match="text()">
    <xsl:value-of select="."/>
  </xsl:template>
  
</xsl:stylesheet>