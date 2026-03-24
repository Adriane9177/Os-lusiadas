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

# 2. DICIONÁRIO EXPANDIDO (CANTOS I a X)
# Formato: "Termo": ("tag", "tipo", "id")
entidades_fixas = {
    # --- PRIORIDADES: EPÍTETOS E PERÍFRASES ---
    "ocidental praia Lusitana": ("rs", "place", "portugal"),
    "Reino de Lusitânia": ("rs", "place", "portugal"),
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
    "Ilha dos Amores": ("placeName", "myth", "ilha_amores"),
    "Cabo Tormentoso": ("placeName", "real", "cabo_boa_esperanca"),

    # --- MITOLOGIA ---
    "Adamastor": ("persName", "myth", "adamastor"),
    "Marte": ("persName", "myth", "marte"),
    "Neptuno": ("persName", "myth", "neptuno"),
    "Júpiter": ("persName", "myth", "jupiter"),
    "Baco": ("persName", "myth", "baco"),
    "Vénus": ("persName", "myth", "venus"),
    "Venus": ("persName", "myth", "venus"),
    "Citereia": ("persName", "myth", "venus"),
    "Tétis": ("persName", "myth", "tetis"),
    "Mercúrio": ("persName", "myth", "mercurio"),
    "Cupido": ("persName", "myth", "cupido"),
    "Nereidas": ("persName", "myth", "nereidas"),
    "Austro": ("persName", "myth", "austro"), # No contexto de divindade do vento
    "Noto": ("persName", "myth", "noto"),

    # --- HISTÓRICOS ---
    "Vasco da Gama": ("persName", "hist", "v_gama"),
    "Inês de Castro": ("persName", "hist", "ines_castro"),
    "Inês": ("persName", "hist", "ines_castro"),
    "Afonso Henriques": ("persName", "hist", "afonso_henriques"),
    "D. Manuel": ("persName", "hist", "d_manuel_i"),
    "Gama": ("persName", "hist", "v_gama"),

    # --- LUGARES ---
    "Portugal": ("placeName", "real", "portugal"),
    "Lisboa": ("placeName", "real", "lisboa"),
    "Índia": ("placeName", "real", "india"),
    "India": ("placeName", "real", "india"),
    "África": ("placeName", "real", "africa"),
    "Tejo": ("placeName", "real", "tejo"),
    "Calecut": ("placeName", "real", "calecut"),
    "Pado": ("placeName", "real", "rio_po"),
    "Lampetusa": ("placeName", "myth", "lampetusa")
}

# Substantivos que a IA costuma confundir n'Os Lusíadas (Blacklist)
BLACKLIST_IA = {
    "Fé", "Lei", "Rei", "Império", "Mundo", "Fama", "Guerra", 
    "Paz", "Obras", "Braços", "Canto", "Amor", "Vida", "Morte",
    "Barões", "Gente", "Terra", "Mar", "Senhor", "Deos"
}

def normalizar_id(texto):
    """Remove acentos para gerar IDs XML seguros."""
    mapa = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ç": "c", "ã": "a", "õ": "o"}
    texto = texto.lower().replace(" ", "_")
    for k, v in mapa.items():
        texto = texto.replace(k, v)
    return re.sub(r'[^a-z0-9_]', '', texto)

def marcar_segmento_texto(texto):
    """Processa apenas o texto puro entre tags XML."""
    if len(texto.strip()) < 3:
        return texto

    # Passo 1: Marcar Dicionário Fixo (do maior para o menor)
    for termo in sorted(entidades_fixas.keys(), key=len, reverse=True):
        if termo in texto:
            tag, tipo, ref = entidades_fixas[termo]
            # O padrão regex garante fronteira de palavras
            padrao = rf"\b{re.escape(termo)}\b"
            # Usamos o disfarce [[[ ]]] para proteger a marcação do spaCy
            subst = f'[[[{tag} type="{tipo}" ref="#{ref}"]]]' + termo + f'[[[/{tag}]]]'
            texto = re.sub(padrao, subst, texto)

    # Passo 2: IA (spaCy) no que sobrou (ignora o que está mascarado)
    texto_para_ia = texto.replace("[[[", "___").replace("]]]", "___")
    doc = nlp(texto_para_ia)
    
    # Processar entidades da IA de trás para frente para não quebrar índices
    for ent in reversed(doc.ents):
        if ent.label_ in ["PER", "LOC", "GPE"] and ent.text not in BLACKLIST_IA:
            # Verifica se essa parte do texto já não contém as máscaras do dicionário
            if "___" not in texto[ent.start_char:ent.end_char]:
                tag = "persName" if ent.label_ == "PER" else "placeName"
                tipo = "hist" if ent.label_ == "PER" else "real"
                ref_id = normalizar_id(ent.text)
                
                abrir = f'[[[{tag} type="{tipo}" ref="#{ref_id}"]]]'
                fechar = f'[[[/{tag}]]]'
                texto = texto[:ent.start_char] + abrir + ent.text + fechar + texto[ent.end_char:]

    # Passo 3: Restaurar Tags Reais
    texto = texto.replace("[[[", "<").replace("]]]", ">")
    return texto

def main():
    ARQUIVO_ENTRADA = 'LusiadasModernizado.xml'
    ARQUIVO_SAIDA = 'Lusiadas_ObraCompleta_Marcado.xml'

    try:
        with io.open(ARQUIVO_ENTRADA, 'r', encoding='utf-8') as f:
            conteudo = f.read()

        # Isolar Header (para não marcar nomes de autores/editores)
        partes_tei = re.split(r'(</teiHeader>)', conteudo)
        if len(partes_tei) < 3:
            print("Erro: Estrutura TEI inválida.")
            return
        
        header = partes_tei[0] + partes_tei[1]
        corpo = partes_tei[2]

        # Dividir corpo em blocos de Tags e blocos de Texto
        print("Iniciando processamento da obra completa...")
        partes_xml = re.split(r'(<[^>]+>)', corpo)
        resultado = []

        for p in partes_xml:
            if p.startswith('<'):
                resultado.append(p) # Mantém a tag original (ex: <l>, <lg>)
            else:
                # Aplica a marcação inteligente no conteúdo textual
                resultado.append(marcar_segmento_texto(p))

        with io.open(ARQUIVO_SAIDA, 'w', encoding='utf-8') as f:
            f.write(header + "".join(resultado))

        print(f"Sucesso! Obra marcada em: {ARQUIVO_SAIDA}")

    except Exception as e:
        print(f"Erro fatal: {e}")

if __name__ == "__main__":
    main()