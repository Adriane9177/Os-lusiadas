import xml.etree.ElementTree as ET
import json
import re

# Nomes dos arquivos de entrada
ARQUIVO_POEMA = 'Lusiadas_Canto1_marcado.xml'
ARQUIVO_AUTORIDADES = 'autoridade_lusiadas.xml'
ARQUIVO_SAIDA = 'index.html'

# Namespace TEI
ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

def normalizar_id_interno(txt):
    """Remove a hashtag e espaços para garantir que o ID bata com o dicionário."""
    if not txt: return ""
    return txt.replace('#', '').strip()

def carregar_autoridades():
    """Lê o XML de autoridades e cria um dicionário para o JavaScript."""
    try:
        tree = ET.parse(ARQUIVO_AUTORIDADES)
        root = tree.getroot()
        dados = {}

        # Busca todos os elementos que podem ser entidades
        for ent in root.findall('.//{*}person') + root.findall('.//{*}personGrp') + root.findall('.//{*}place'):
            xml_id = ent.get('{http://www.w3.org/XML/1998/namespace}id')
            if not xml_id: continue
            
            # Identifica o tipo
            tag_pura = ent.tag.split('}')[-1]
            tipo = "lugar" if tag_pura == 'place' else "pessoa"
            
            # Pega o nome (persName ou placeName)
            nome_elem = ent.find('{*}persName') if tipo == "pessoa" else ent.find('{*}placeName')
            nome = nome_elem.text if nome_elem is not None else xml_id
            
            # Pega a nota (Afrânio Peixoto)
            nota_elem = ent.find('{*}note')
            nota = nota_elem.text if nota_elem is not None else "Sem descrição disponível."
            
            wiki = ent.get('ref') or "#"
            
            # Pega a imagem
            img_elem = ent.find('{*}graphic')
            img = img_elem.get('url') if img_elem is not None else ""
            
            # Coordenadas (apenas para lugares)
            lat, lon = None, None
            if tipo == "lugar":
                geo = ent.find('.//{*}geo')
                if geo is not None and geo.text:
                    parts = geo.text.replace(',', ' ').split()
                    if len(parts) >= 2:
                        try:
                            lat, lon = float(parts[0]), float(parts[1])
                        except: pass

            dados[xml_id] = {
                "nome": nome, "desc": nota, "wiki": wiki, "img": img, 
                "tipo": tipo, "lat": lat, "lon": lon
            }
        
        return dados
    except Exception as e:
        print(f"Erro ao carregar autoridades: {e}")
        return {}

def tei_para_html(element):
    """Converte elementos TEI para HTML com IDs normalizados."""
    if element is None: return ""
    html = ""
    if element.text: html += element.text

    for child in element:
        tag_name = child.tag.split('}')[-1]
        
        if tag_name in ['persName', 'placeName', 'rs']:
            raw_ref = child.get('ref') or ""
            # Limpa o ID para o JavaScript (remove # e espaços)
            ref_limpo = normalizar_id_interno(raw_ref)
            tipo = child.get('type') or "geral"
            
            html += f'<span class="entidade {tipo}" onclick="mostrarEntidade(\'{ref_limpo}\')">'
            html += tei_para_html(child)
            html += '</span>'
        elif tag_name == 'lg':
            n = child.get('n', '')
            html += f'<div class="estrofe"><span class="num-estrofe">{n}</span>'
            html += tei_para_html(child)
            html += '</div>'
        elif tag_name == 'l':
            html += f'<span class="verso">{tei_para_html(child)}</span>'
        elif tag_name == 'head':
            html += f'<h3 class="titulo-canto">{tei_para_html(child)}</h3>'
        else:
            html += tei_para_html(child)

        if child.tail: html += child.tail
    return html

def gerar_site():
    dados_autoridades = carregar_autoridades()
    tree_poema = ET.parse(ARQUIVO_POEMA)
    root_poema = tree_poema.getroot()
    body = root_poema.find('.//{http://www.tei-c.org/ns/1.0}body')
    corpo_html = tei_para_html(body)

    html_template = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Os Lusíadas - Edição Digital</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { margin: 0; font-family: 'Georgia', serif; background: #f4ecd8; color: #2c2c2c; }
        header { text-align: center; padding: 25px; background: #e8dab2; border-bottom: 2px solid #c2b280; }
        #mapa-container { width: 90%; margin: 20px auto; position: relative; }
        #mapa { height: 450px; width: 100%; border: 3px solid #c2b280; border-radius: 8px; transition: 0.5s; z-index: 1; background: #aad3df; }
        .expandido { position: fixed !important; top:0; left:0; width:100% !important; height:100vh !important; z-index: 9999 !important; border: none !important; border-radius: 0 !important; }
        #btn-mapa { position: absolute; top: 10px; right: 10px; z-index: 10000; padding: 10px 15px; cursor: pointer; background: white; border: 2px solid #c2b280; font-weight: bold; border-radius: 4px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
        #texto-poema { padding: 40px; max-width: 850px; margin: 0 auto; background: #fffcf5; box-shadow: 0 0 30px rgba(0,0,0,0.05); }
        .titulo-canto { text-align: center; color: #8b0000; font-variant: small-caps; font-size: 2em; margin-bottom: 40px; }
        .estrofe { margin-bottom: 35px; padding-left: 60px; position: relative; }
        .num-estrofe { position: absolute; left: 0; color: #c2b280; font-weight: bold; font-size: 1em; }
        .verso { display: block; line-height: 1.7; font-size: 1.2em; }
        .entidade { cursor: pointer; border-bottom: 1.5px solid rgba(0,0,0,0.1); transition: 0.2s; }
        .entidade:hover { background: rgba(194, 178, 128, 0.25); border-bottom-color: #8b0000; }
        .entidade.hist, .entidade.person { color: #3b5b6b; }
        .entidade.myth { color: #8b4c5a; }
        .entidade.real { color: #4f6b4a; }
        #overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.75); z-index: 20000; }
        #painel { display: none; position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 90%; max-width: 480px; background: #fdf6e3; padding: 30px; border: 3px solid #c2b280; z-index: 20001; border-radius: 12px; text-align: center; box-shadow: 0 10px 40px rgba(0,0,0,0.5); }
        #painel img { max-width: 100%; max-height: 320px; border-radius: 6px; margin-bottom: 15px; border: 1px solid #c2b280; display: none; margin-left: auto; margin-right: auto; }
        .fechar { position: absolute; top: 10px; right: 15px; cursor: pointer; font-size: 28px; border: none; background: none; color: #8b0000; font-weight: bold; }
    </style>
</head>
<body>
<header>
    <h1>Os Lusíadas</h1>
    <p>Edição Semântica Interativa - Baseada em Afrânio Peixoto</p>
</header>
<div id="mapa-container">
    <button id="btn-mapa" onclick="toggleMapa()">⤢ Expandir Mapa</button>
    <div id="mapa"></div>
</div>
<div id="texto-poema">
    {{CORPO_HTML}}
</div>
<div id="overlay" onclick="fecharPainel()"></div>
<div id="painel">
    <button class="fechar" onclick="fecharPainel()">×</button>
    <img id="modal-img" src="" alt="Imagem da autoridade">
    <h2 id="modal-titulo"></h2>
    <p id="modal-desc" style="text-align:justify; line-height:1.5;"></p>
    <hr style="border:0; border-top:1px solid #c2b280; margin: 15px 0;">
    <a id="modal-link" href="" target="_blank" style="color:#3b5b6b; font-weight:bold; text-decoration:none;">🔗 Ver no Wikidata</a>
</div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
    const autoridades = {{DADOS_JSON}};
    // Troca do servidor para CartoDB (Evita Erro 403)
    const map = L.map('mapa').setView([15, 20], 2);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        attribution: '© OpenStreetMap © CartoDB'
    }).addTo(map);

    const markers = {};
    Object.keys(autoridades).forEach(id => {
        const d = autoridades[id];
        if (d.lat && d.lon) {
            markers[id] = L.marker([d.lat, d.lon]).addTo(map).bindPopup("<b>"+d.nome+"</b>");
        }
    });

    function mostrarEntidade(id) {
        const d = autoridades[id];
        if (!d) {
            console.error("ID não encontrado na lista de autoridades:", id);
            return;
        }
        document.getElementById('modal-titulo').innerText = d.nome;
        document.getElementById('modal-desc').innerText = d.desc;
        document.getElementById('modal-link').href = d.wiki;
        
        const img = document.getElementById('modal-img');
        if (d.img && d.img.trim() !== "") { 
            img.src = d.img; 
            img.style.display = 'block'; 
        } else { 
            img.style.display = 'none'; 
        }
        
        document.getElementById('overlay').style.display = 'block';
        document.getElementById('painel').style.display = 'block';

        if (d.lat && markers[id]) {
            map.flyTo([d.lat, d.lon], 5);
            markers[id].openPopup();
        }
    }

    function fecharPainel() {
        document.getElementById('overlay').style.display = 'none';
        document.getElementById('painel').style.display = 'none';
    }

    function toggleMapa() {
        const m = document.getElementById('mapa');
        const btn = document.getElementById('btn-mapa');
        m.classList.toggle('expandido');
        btn.innerText = m.classList.contains('expandido') ? "⤡ Minimizar" : "⤢ Expandir Mapa";
        setTimeout(() => map.invalidateSize(), 500);
    }
</script>
</body>
</html>
"""
    final_html = html_template.replace("{{CORPO_HTML}}", corpo_html)
    final_html = final_html.replace("{{DADOS_JSON}}", json.dumps(dados_autoridades, indent=4))

    with open(ARQUIVO_SAIDA, 'w', encoding='utf-8') as f:
        f.write(final_html)
    print(f"Sucesso! Site gerado em: {ARQUIVO_SAIDA}")

if __name__ == "__main__":
    gerar_site()