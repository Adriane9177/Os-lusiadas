# -*- coding: utf-8 -*-
import spacy
import re
import io

# 1. CARREGAR spaCy
print("Carregando inteligência artificial...")
try:
    nlp = spacy.load("pt_core_news_lg")
except:
    print("Erro: Instale o modelo com: python -m spacy download pt_core_news_lg")
    exit()

# 2. DICIONÁRIO DE AUTORIDADES (Prioridade Máxima)
entidades_fixas = {
    "ocidental praia Lusitana": ("rs", "place", "portugal"),
    "O forte Capitão": ("rs", "person", "v_gama"),
    "O ilustre Gama": ("rs", "person", "v_gama"),
    "Sublime Rei": ("rs", "person", "d_sebastiao"),
    "filho de Maia": ("rs", "myth", "mercurio"),
    "clara Deia": ("rs", "myth", "venus"),
    "bela Deusa": ("rs", "myth", "venus"),
    "grão Tebano": ("rs", "myth", "baco"),
    "Marte": ("persName", "myth", "marte"),
    "Neptuno": ("persName", "myth", "neptuno"),
    "Júpiter": ("persName", "myth", "jupiter"),
    "Baco": ("persName", "myth", "baco"),
    "Vénus": ("persName", "myth", "venus"),
    "Venus": ("persName", "myth", "venus"),
    "Citereia": ("persName", "myth", "venus"),
    "Vasco da Gama": ("persName", "hist", "v_gama"),
    "Gama": ("persName", "hist", "v_gama"),
    "Afonso Henriques": ("persName", "hist", "afonso_henriques"),
    "D. Manuel": ("persName", "hist", "d_manuel_i"),
    "Portugal": ("placeName", "real", "portugal"),
    "Tejo": ("placeName", "real", "tejo"),
    "África": ("placeName", "real", "africa"),
    "Ásia": ("placeName", "real", "asia"),
    "Índia": ("placeName", "real", "india"),
    "Taprobana": ("placeName", "real", "taprobana")
}

# Palavras que a IA NUNCA deve marcar (Blacklist)
BLACKLIST_IA = {"Fé", "Lei", "Rei", "Império", "Mundo", "Fama", "Guerra", "Paz", "Obras", "Canto", "Amor", "Morte", "Terra", "Mar"}

def marcar_texto_puro(texto):
    """Aplica marcação apenas em blocos que não são tags XML."""
    if len(texto.strip()) < 2:
        return texto

    # Passo 1: Aplicar Dicionário Fixo (do maior para o menor)
    # Usamos placeholders temporários para evitar que a IA mexa no que já foi marcado
    mapa_placeholders = {}
    
    for i, termo in enumerate(sorted(entidades_fixas.keys(), key=len, reverse=True)):
        if termo in texto:
            tag, tipo, ref = entidades_fixas[termo]
            placeholder = f"[[ENTIDADE{i}]]"
            # Marcação TEI real
            tag_real = f'<{tag} type="{tipo}" ref="#{ref}">{termo}</{tag}>'
            mapa_placeholders[placeholder] = tag_real
            # Substitui o termo pelo placeholder no texto
            texto = re.sub(rf"\b{re.escape(termo)}\b", placeholder, texto)

    # Passo 2: IA (spaCy) no que sobrou (ignora os placeholders)
    doc = nlp(texto)
    # Processar de trás para frente para não quebrar os índices
    for ent in reversed(doc.ents):
        # Filtros: categoria certa, não está na blacklist, não é um placeholder
        if ent.label_ in ["PER", "LOC", "GPE"] and ent.text not in BLACKLIST_IA and "[[" not in ent.text:
            tag = "persName" if ent.label_ == "PER" else "placeName"
            tipo = "hist" if ent.label_ == "PER" else "real"
            ref_id = ent.text.lower().replace(" ", "_").replace("á", "a").replace("ó", "o")
            
            nova_tag = f'<{tag} type="{tipo}" ref="#{ref_id}">{ent.text}</{tag}>'
            texto = texto[:ent.start_char] + nova_tag + texto[ent.end_char:]

    # Passo 3: Devolver as tags do dicionário que estavam escondidas nos placeholders
    for placeholder, tag_real in mapa_placeholders.items():
        texto = texto.replace(placeholder, tag_real)

    return texto

def main():
    ARQUIVO_ENTRADA = 'LusiadasModernizado.xml'
    ARQUIVO_SAIDA = 'Lusiadas_Canto1_marcado.xml'

    try:
        with io.open(ARQUIVO_ENTRADA, 'r', encoding='utf-8') as f:
            conteudo = f.read()

        # Isolar o Canto 1
        m1 = re.search(r'(<div[^>]+n=["\']1["\'][^>]*>)', conteudo)
        m2 = re.search(r'(<div[^>]+n=["\']2["\'][^>]*>)', conteudo)
        
        if not m1:
            print("Canto 1 não encontrado.")
            return

        pre = conteudo[:m1.start()]
        canto1 = conteudo[m1.start():(m2.start() if m2 else len(conteudo))]
        pos = conteudo[(m2.start() if m2 else len(conteudo)):]

        # Dividir Canto 1 em Tags vs Texto Puro
        # Isso impede que o script altere o que está dentro de < >
        partes = re.split(r'(<[^>]+>)', canto1)
        resultado_final = []

        print("Iniciando marcação segura...")
        for p in partes:
            if p.startswith('<'):
                resultado_final.append(p) # Mantém a tag original (ex: <l>, <lg>)
            else:
                # Processa apenas o conteúdo textual
                resultado_final.append(marcar_texto_puro(p))

        with io.open(ARQUIVO_SAIDA, 'w', encoding='utf-8') as f:
            f.write(pre + "".join(resultado_final) + pos)

        print(f"Sucesso! Arquivo corrigido: {ARQUIVO_SAIDA}")

    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    main()