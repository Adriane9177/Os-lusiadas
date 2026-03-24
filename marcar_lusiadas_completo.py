# -*- coding: utf-8 -*-
import spacy
import re
import io

# 1. CARREGAR spaCy
print("Carregando inteligência artificial (spaCy)...")
try:
    nlp = spacy.load("pt_core_news_lg")
except:
    print("Erro: Instale o modelo: python -m spacy download pt_core_news_lg")
    exit()

# 2. DICIONÁRIO DE AUTORIDADES (Expandido para todos os Cantos)
# Prioridade máxima: termos que a IA costuma errar
entidades_fixas = {
    # --- EPÍTETOS E PERÍFRASES ---
    "ocidental praia Lusitana": ("rs", "place", "portugal"),
    "peito ilustre lusitano": ("rs", "person", "portugueses"),
    "barões assinalados": ("rs", "person", "portugueses"),
    "O forte Capitão": ("rs", "person", "v_gama"),
    "O ilustre Gama": ("rs", "person", "v_gama"),
    "Sublime Rei": ("rs", "person", "d_sebastiao"),
    "grão Tebano": ("rs", "myth", "baco"),
    "filho de Maia": ("rs", "myth", "mercurio"),
    "Ilha dos Amores": ("placeName", "myth", "ilha_amores"),
    "Cabo Tormentoso": ("placeName", "real", "cabo_boa_esperanca"),

    # --- ENTIDADES UNITÁRIAS ---
    "Marte": ("persName", "myth", "marte"),
    "Neptuno": ("persName", "myth", "neptuno"),
    "Júpiter": ("persName", "myth", "jupiter"),
    "Vénus": ("persName", "myth", "venus"),
    "Venus": ("persName", "myth", "venus"),
    "Baco": ("persName", "myth", "baco"),
    "Adamastor": ("persName", "myth", "adamastor"),
    "Tétis": ("persName", "myth", "tetis"),
    "Vasco da Gama": ("persName", "hist", "v_gama"),
    "Inês de Castro": ("persName", "hist", "ines_castro"),
    "Portugal": ("placeName", "real", "portugal"),
    "Índia": ("placeName", "real", "india"),
    "Tejo": ("placeName", "real", "tejo"),
}

# Substantivos poéticos que a IA NÃO deve marcar (Evita erros de Domain Shift)
BLACKLIST_IA = {
    "Fé", "Lei", "Rei", "Império", "Mundo", "Fama", "Guerra", "Paz", 
    "Obras", "Braços", "Canto", "Amor", "Morte", "Terra", "Mar", 
    "Gente", "Barões", "Senhor", "Vida", "Luz", "Céu"
}

def normalizar_id(texto):
    """Gera IDs limpos para o XML."""
    mapa = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ç": "c", "ã": "a", "õ": "o"}
    res = texto.lower().replace(" ", "_")
    for k, v in mapa.items():
        res = res.replace(k, v)
    return re.sub(r'[^a-z0-9_]', '', res)

def marcar_texto_segmentado(texto_segmento):
    """Processa apenas blocos de texto que não contêm tags XML."""
    if len(texto_segmento.strip()) < 3:
        return texto_segmento

    # 1. Aplicar Dicionário Fixo (Placeholder para proteger da IA)
    # Ordenar por tamanho para pegar "Vasco da Gama" antes de "Gama"
    mapa_tags = {}
    for i, termo in enumerate(sorted(entidades_fixas.keys(), key=len, reverse=True)):
        if termo in texto_segmento:
            tag, tipo, ref = entidades_fixas[termo]
            placeholder = f"___ENT{i}___"
            real_tag = f'<{tag} type="{tipo}" ref="#{ref}">{termo}</{tag}>'
            mapa_tags[placeholder] = real_tag
            # Regex \b evita marcar dentro de outras palavras
            texto_segmento = re.sub(rf"\b{re.escape(termo)}\b", placeholder, texto_segmento)

    # 2. IA (spaCy) no que sobrou de texto
    # Substituímos placeholders por espaços temporários para o spaCy não se perder
    texto_para_nlp = texto_segmento
    for ph in mapa_tags.keys():
        texto_para_nlp = texto_para_nlp.replace(ph, " " * len(ph))

    doc = nlp(texto_para_nlp)
    # Processar de trás para frente para manter os offsets
    for ent in reversed(doc.ents):
        if ent.label_ in ["PER", "LOC", "GPE"] and ent.text.strip() not in BLACKLIST_IA:
            # Verifica se o spaCy não está tentando marcar em cima de um placeholder
            if "___" not in texto_segmento[ent.start_char:ent.end_char]:
                tag_ia = "persName" if ent.label_ == "PER" else "placeName"
                tipo_ia = "hist" if ent.label_ == "PER" else "real"
                ref_id = normalizar_id(ent.text)
                
                nova_marca = f'<{tag_ia} type="{tipo_ia}" ref="#{ref_id}">{ent.text}</{tag_ia}>'
                texto_segmento = texto_segmento[:ent.start_char] + nova_marca + texto_segmento[ent.end_char:]

    # 3. Restaurar as tags do dicionário
    for ph, tag_completa in mapa_tags.items():
        texto_segmento = texto_segmento.replace(ph, tag_completa)

    return texto_segmento

def main():
    ARQUIVO_ENTRADA = 'LusiadasModernizado.xml'
    ARQUIVO_SAIDA = 'Lusiadas_Completo_REVISADO.xml'

    try:
        with io.open(ARQUIVO_ENTRADA, 'r', encoding='utf-8') as f:
            conteudo = f.read()

        # Isolar o teiHeader (não mexe nele)
        partes_tei = re.split(r'(</teiHeader>)', conteudo)
        if len(partes_tei) < 3:
            print("Erro: Estrutura TEI não encontrada.")
            return
        
        header = partes_tei[0] + partes_tei[1]
        resto_obra = partes_tei[2]

        # Dividir o resto em Tags e Texto Puro
        # O padrão abaixo separa <tag> de "texto entre tags"
        print("Processando os 10 Cantos d'Os Lusíadas...")
        partes_xml = re.split(r'(<[^>]+>)', resto_obra)
        
        resultado_corpo = []
        for p in partes_xml:
            if p.startswith('<'):
                # É uma tag XML original (ex: <l>, <lg>, <div>), mantém intacta
                resultado_corpo.append(p)
            else:
                # É texto puro, aplicar a marcação inteligente
                resultado_corpo.append(marcar_texto_segmentado(p))

        with io.open(ARQUIVO_SAIDA, 'w', encoding='utf-8') as f:
            f.write(header + "".join(resultado_corpo))

        print(f"Sucesso! Arquivo gerado sem erros de aninhamento: {ARQUIVO_SAIDA}")

    except Exception as e:
        print(f"Erro fatal: {e}")

if __name__ == "__main__":
    main()