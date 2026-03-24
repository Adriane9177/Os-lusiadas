# -*- coding: utf-8 -*-
import spacy
import re
import io

# 1. CARREGAR spaCy (IA)
print("Carregando inteligência artificial (spaCy)...")
try:
    nlp = spacy.load("pt_core_news_lg")
except:
    print("Erro: Instale o modelo com: python -m spacy download pt_core_news_lg")
    exit()

# 2. DICIONÁRIO DE AUTORIDADES (Canto 1 - Foco em precisão filológica)
entidades_fixas = {
    # --- EPÍTETOS E PERÍFRASES (Prioridade para frases longas) ---
    "ocidental praia Lusitana": ("rs", "place", "portugal"),
    "peito ilustre lusitano": ("rs", "person", "portugueses"),
    "barões assinalados": ("rs", "person", "portugueses"),
    "O forte Capitão": ("rs", "person", "v_gama"),
    "O ilustre Gama": ("rs", "person", "v_gama"),
    "Sublime Rei": ("rs", "person", "d_sebastiao"),
    "filho de Maia": ("rs", "myth", "mercurio"),
    "clara Deia": ("rs", "myth", "venus"),
    "bela Deusa": ("rs", "myth", "venus"),
    "grão Tebano": ("rs", "myth", "baco"),
    "grão Macedónio": ("rs", "person", "alexandre_magno"),
    "Maura lança": ("rs", "person", "mouros"),
    "doze de Inglaterra": ("rs", "person", "doze_inglaterra"),
    "Reinos lá da Aurora": ("rs", "place", "oriente"),

    # --- MITOLOGIA ---
    "Marte": ("persName", "myth", "marte"),
    "Neptuno": ("persName", "myth", "neptuno"),
    "Júpiter": ("persName", "myth", "jupiter"),
    "Tonante": ("persName", "myth", "jupiter"),
    "Baco": ("persName", "myth", "baco"),
    "Vénus": ("persName", "myth", "venus"),
    "Venus": ("persName", "myth", "venus"),
    "Citereia": ("persName", "myth", "venus"),
    "Mercúrio": ("persName", "myth", "mercurio"),
    "Tétis": ("persName", "myth", "tetis"),
    "Tethys": ("persName", "myth", "tetis"),
    "Próteo": ("persName", "myth", "proteo"),
    "Atlante": ("persName", "myth", "atlante"),
    "Anfitrite": ("persName", "myth", "anfitrite"),
    "Tágides": ("persName", "myth", "tagides"),
    "Tagides": ("persName", "myth", "tagides"),

    # --- HISTÓRICOS ---
    "Vasco da Gama": ("persName", "hist", "v_gama"),
    "Gama": ("persName", "hist", "v_gama"),
    "Afonso Henriques": ("persName", "hist", "afonso_henriques"),
    "D. Manuel": ("persName", "hist", "d_manuel_i"),
    "Nuno": ("persName", "hist", "nuno_alvares"),
    "Egas": ("persName", "hist", "egas_moniz"),
    "Magriço": ("persName", "hist", "magrico"),
    "Alexandro": ("persName", "hist", "alexandre_magno"),
    "Trajano": ("persName", "hist", "trajano"),

    # --- LUGARES ---
    "África": ("placeName", "real", "africa"),
    "Ásia": ("placeName", "real", "asia"),
    "Índia": ("placeName", "real", "india"),
    "Taprobana": ("placeName", "real", "taprobana"),
    "Portugal": ("placeName", "real", "portugal"),
    "Tejo": ("placeName", "real", "tejo"),
    "Moçambique": ("placeName", "real", "mocambique"),
    "Mombaça": ("placeName", "real", "mombaca"),
    "Olimpo": ("placeName", "myth", "olimpo"),
    "Aqueronte": ("placeName", "myth", "aqueronte")
}

# Itens que a IA NÃO deve marcar (Blacklist)
BLACKLIST_IA = {
    "Fé", "Lei", "Rei", "Império", "Mundo", "Fama", "Guerra", 
    "Paz", "Obras", "Braços", "Canto", "Amor", "Vida", "Morte", "Terra", "Mar"
}

def normalizar_id(texto):
    mapa = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ç": "c", "ã": "a", "õ": "o"}
    texto = texto.lower().replace(" ", "_")
    for k, v in mapa.items():
        texto = texto.replace(k, v)
    return re.sub(r'[^a-z0-9_]', '', texto)

def marcar_segmento_texto(texto):
    if len(texto.strip()) < 3:
        return texto

    # 1. Aplicar Dicionário Fixo com máscara [[[ ]]]
    for termo in sorted(entidades_fixas.keys(), key=len, reverse=True):
        if termo in texto:
            tag, tipo, ref = entidades_fixas[termo]
            padrao = rf"\b{re.escape(termo)}\b"
            subst = f'[[[{tag} type="{tipo}" ref="#{ref}"]]]' + termo + f'[[[/{tag}]]]'
            texto = re.sub(padrao, subst, texto)

    # 2. Aplicar spaCy no que sobrou
    texto_ia = texto.replace("[[[", "___").replace("]]]", "___")
    doc = nlp(texto_ia)
    for ent in reversed(doc.ents):
        if ent.label_ in ["PER", "LOC", "GPE"] and ent.text not in BLACKLIST_IA:
            if "___" not in texto[ent.start_char:ent.end_char]:
                tag = "persName" if ent.label_ == "PER" else "placeName"
                tipo = "hist" if ent.label_ == "PER" else "real"
                ref_id = normalizar_id(ent.text)
                
                abrir = f'[[[{tag} type="{tipo}" ref="#{ref_id}"]]]'
                fechar = f'[[[/{tag}]]]'
                texto = texto[:ent.start_char] + abrir + ent.text + fechar + texto[ent.end_char:]

    return texto.replace("[[[", "<").replace("]]]", ">")

def main():
    ARQUIVO_ENTRADA = 'LusiadasModernizado.xml'
    ARQUIVO_SAIDA = 'Lusiadas_Canto1_Marcado.xml'

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

        # Processar protegendo as tags XML existentes
        partes_xml = re.split(r'(<[^>]+>)', canto1)
        resultado = []
        for p in partes_xml:
            if p.startswith('<'):
                resultado.append(p)
            else:
                resultado.append(marcar_segmento_texto(p))

        with io.open(ARQUIVO_SAIDA, 'w', encoding='utf-8') as f:
            f.write(pre + "".join(resultado) + pos)

        print(f"Sucesso! Canto 1 marcado em: {ARQUIVO_SAIDA}")

    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    main()