# -*- coding: utf-8 -*-
import spacy
import re
import io

# 1. CARREGAR spaCy
print("Carregando inteligência artificial...")
nlp = spacy.load("pt_core_news_lg")

# 2. DICIONÁRIO DE AUTORIDADES (Canto I)
entidades_fixas = {
    # Mitológicos
    "Marte": ("persName", "myth", "marte"),
    "Neptuno": ("persName", "myth", "neptuno"),
    "Júpiter": ("persName", "myth", "jupiter"),
    "Baco": ("persName", "myth", "baco"),
    "Vénus": ("persName", "myth", "venus"),
    "Venus": ("persName", "myth", "venus"),
    "Citereia": ("persName", "myth", "venus"),
    "filho de Maia": ("rs", "myth", "mercurio"),
    "clara Deia": ("rs", "myth", "venus"),
    "bela Deusa": ("rs", "myth", "venus"),
    "grão Tebano": ("rs", "myth", "baco"),
    
    # Históricos
    "Vasco da Gama": ("persName", "hist", "v_gama"),
    "Gama": ("persName", "hist", "v_gama"),
    "Afonso Henriques": ("persName", "hist", "afonso_henriques"),
    "D. Manuel": ("persName", "hist", "d_manuel_i"),
    "D. Sebastião": ("persName", "hist", "d_sebastiao"),
    "Sublime Rei": ("rs", "person", "d_sebastiao"),
    "O forte Capitão": ("rs", "person", "v_gama"),
    "O ilustre Gama": ("rs", "person", "v_gama"),
    "barões assinalados": ("rs", "person", "portugueses"),
    "Capitão": ('rs', 'person', 'v_gama'), 
    "Grego":('rs', 'person', 'ulisses'),
    "Troiano":('rs', 'person', 'eneias'),
    
    # Lugares
    "Portugal": ("placeName", "real", "portugal"),
    "Tejo": ("placeName", "real", "tejo"),
    "África": ("placeName", "real", "africa"),
    "Africa": ("placeName", "real", "africa"),
    "Ásia": ("placeName", "real", "asia"),
    "Asia": ("placeName", "real", "asia"),
    "Índia": ("placeName", "real", "india"),
    "India": ("placeName", "real", "india"),
    "Taprobana": ("placeName", "real", "taprobana"),
    "ocidental praia Lusitana": ("rs", "place", "portugal")
}

BLACKLIST_IA = {"Fé", "Lei", "Rei", "Império", "Mundo", "Fama", "Guerra", "Paz", "Obras", "Canto", "Amor", "Morte", "Terra", "Mar", "Barões", "Gente", "Deos"}

def aplicar_marcacao_segura(texto):
    if len(texto.strip()) < 3: return texto

    # 1. Encontrar todas as ocorrências do dicionário (coordenadas: inicio, fim, tag_pronta)
    matches = []
    
    # Ordem decrescente de tamanho para não pegar "Gama" dentro de "Vasco da Gama"
    for termo in sorted(entidades_fixas.keys(), key=len, reverse=True):
        for m in re.finditer(rf"\b{re.escape(termo)}\b", texto):
            # Verifica se essa posição já não foi ocupada por um termo maior
            if not any(m.start() < start < m.end() or start < m.start() < end for start, end, _ in matches):
                tag, tipo, ref = entidades_fixas[termo]
                tag_formatada = f'<{tag} type="{tipo}" ref="#{ref}">{termo}</{tag}>'
                matches.append((m.start(), m.end(), tag_formatada))

    # 2. Encontrar ocorrências via IA (spaCy) no texto que sobrou
    doc = nlp(texto)
    for ent in doc.ents:
        if ent.label_ in ["PER", "LOC"] and ent.text not in BLACKLIST_IA and len(ent.text) > 2:
            # Verifica se o spaCy não está batendo em algo já marcado pelo dicionário
            if not any(ent.start_char < end and ent.end_char > start for start, end, _ in matches):
                tag_ia = "persName" if ent.label_ == "PER" else "placeName"
                tipo_ia = "hist" if ent.label_ == "PER" else "real"
                ref_ia = ent.text.lower().replace(" ", "_").replace("á", "a").replace("í", "i").replace("ó", "o")
                tag_formatada = f'<{tag_ia} type="{tipo_ia}" ref="#{ref_ia}">{ent.text}</{tag_ia}>'
                matches.append((ent.start_char, ent.end_char, tag_formatada))

    # 3. Reconstruir o texto de trás para frente usando as coordenadas
    matches.sort(key=lambda x: x[0], reverse=True)
    resultado = list(texto)
    for start, end, tag_pronta in matches:
        resultado[start:end] = [tag_pronta]
    
    return "".join(resultado)

def main():
    ARQUIVO_ENTRADA = 'LusiadasModernizado.xml'
    ARQUIVO_SAIDA = 'Lusiadas_Canto1_teste2.xml'

    try:
        with io.open(ARQUIVO_ENTRADA, 'r', encoding='utf-8') as f:
            conteudo = f.read()

        # Isolar Canto 1
        m1 = re.search(r'(<div[^>]+n=["\']1["\'][^>]*>)', conteudo)
        m2 = re.search(r'(<div[^>]+n=["\']2["\'][^>]*>)', conteudo)
        if not m1: return

        pre = conteudo[:m1.start()]
        canto1 = conteudo[m1.start():(m2.start() if m2 else len(conteudo))]
        pos = conteudo[(m2.start() if m2 else len(conteudo)):]

        # Separar tags XML de texto para não estragar a estrutura
        partes = re.split(r'(<[^>]+>)', canto1)
        novo_canto = []
        
        for p in partes:
            if p.startswith('<'):
                novo_canto.append(p)
            else:
                novo_canto.append(aplicar_marcacao_segura(p))

        with io.open(ARQUIVO_SAIDA, 'w', encoding='utf-8') as f:
            f.write(pre + "".join(novo_canto) + pos)

        print(f"Sucesso! Arquivo gerado corretamente em: {ARQUIVO_SAIDA}")

    except Exception as e:
        print(f"Erro fatal: {e}")

if __name__ == "__main__":
    main()