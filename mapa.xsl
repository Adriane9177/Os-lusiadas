<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet 
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  version="1.0">
  
  <xsl:output method="html" encoding="UTF-8" indent="yes"/>
  
  <xsl:variable name="autoridades" select="document('autoridade_lusiadas.xml')"/>
  
  <xsl:template match="/">
    
    <html>
      <head>
        <meta charset="UTF-8"/>
        <title>Mapa dos Lugares</title>
        
        <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"/>
        <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
        
        <style>
          body { margin:0; font-family: Georgia; background:#f4ecd8; }
          #mapa { height: 100vh; }
        </style>
        
      </head>
      
      <body>
        
        <div id="mapa"></div>
        
        <!-- 👇 AQUI O XSLT SÓ GERA DADOS -->
        <div id="dados" style="display:none;">
          
          <xsl:for-each select="$autoridades//*[@xml:id]">
            
            <xsl:variable name="geo"
                          select="string(*[local-name()='location']/*[local-name()='geo'])"/>
            
            <xsl:if test="$geo != '' and contains($geo,' ')">
              
              <div class="ponto">
                <span class="lat">
                  <xsl:value-of select="substring-before($geo,' ')"/>
                </span>
                <span class="lon">
                  <xsl:value-of select="substring-after($geo,' ')"/>
                </span>
                <span class="nome">
                  <xsl:value-of select="normalize-space(string(*[local-name()='placeName'] | *[local-name()='persName']))"/>
                </span>
                <span class="desc">
                  <xsl:value-of select="normalize-space(string(*[local-name()='note']))"/>
                </span>
              </div>
              
            </xsl:if>
            
          </xsl:for-each>
          
        </div>
        
        <script>
          document.addEventListener("DOMContentLoaded", function() {
          
          var map = L.map('mapa').setView([20, 0], 2);
          
          L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          maxZoom: 18
          }).addTo(map);
          
          var pontos = document.querySelectorAll(".ponto");
          
          pontos.forEach(function(p) {
          
          var lat = parseFloat(p.querySelector(".lat").textContent);
          var lon = parseFloat(p.querySelector(".lon").textContent);
          var nome = p.querySelector(".nome").textContent;
          var desc = p.querySelector(".desc").textContent;
          
          L.marker([lat, lon])
          .addTo(map)
          .bindPopup("<b>" + nome + "</b>&lt;br/&gt;" + desc);
            
            });
            
            });
          </script>
          
        </body>
      </html>
      
    </xsl:template>
    
  </xsl:stylesheet>