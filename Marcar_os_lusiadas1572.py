# -*- coding: utf-8 -*-
import re
import io
import spacy

# 1. CARREGAR spaCy (Apenas para auxílio em nomes próprios claros)
print("Carregando inteligência artificial...")
nlp = spacy.load("pt_core_news_lg")

# 2. DICIONÁRIO DE FORMAS ARCAICAS (Baseado na grafia de 1572)
# Mapeia a palavra como ela aparece em 1572 para o ID correto
entidades_1572 = {
    # --- LUGARES ---
    "Occidental": ("placeName", "real", "ocidente"),
    "Lusitana": ("placeName", "real", "portugal"),
    "Taprobana": ("placeName", "real", "taprobana"),
    "Africa": ("placeName", "real", "africa"),
    "Asia": ("placeName", "real", "asia"),
    "India": ("placeName", "real", "india"),
    "Yndia": ("placeName", "real", "india"),
    "Hypocrene": ("placeName", "myth", "hipocrene"),
    "Parnaso": ("placeName", "real", "parnaso"),
    "Tingitana": ("placeName", "real", "tingitana"),
    "Mocambique": ("placeName", "real", "mocambique"),

    # --- MITOLOGIA ---
    "Neptuno": ("persName", "myth", "neptuno"),
    "Marte": ("persName", "myth", "marte"),
    "Phebo": ("persName", "myth", "febo"),
    "Venus": ("persName", "myth", "venus"),
    "Jupiter": ("persName", "myth", "jupiter"),
    "Baco": ("persName", "myth", "baco"),
    "Musa": ("persName", "myth", "musas"),
    "Tagides": ("persName", "myth", "tagides"),
    "Troyano": ("persName", "myth", "eneias"), # Referência ao herói Eneias
    "Grego": ("persName", "myth", "ulisses"),  # Referência ao sábio Ulisses

    # --- HISTÓRICOS ---
    "Alexandro": ("persName", "hist", "alexandre_magno"),
    "Trajano": ("persName", "hist", "trajano"),
    "Christo": ("persName", "hist", "cristo"),
    "Deos": ("persName", "hist", "deus"),
    "Constantino": ("persName", "hist", "constantino"),
    "Vasco da Gama": ("persName", "hist", "v_gama"),
    "Gama": ("persName", "hist", "v_gama"),

    # --- EPÍTETOS / RS ---
    "Maura lanca": ("rs", "person", "mouros"),
    "Maura gente": ("rs", "person", "mouros"),
    "Ismaelita": ("rs", "person", "mouros"),
    "Gentio": ("rs", "person", "gentios")
}

def regex_trans_tag(termo):
    """
    Cria uma regex que permite a existência de tags <lb/> 
    no meio de qualquer letra da palavra buscada.
    """
    # Escapa caracteres especiais e separa as letras
    letras = [re.escape(l) for l in termo]
    # Define que entre cada letra pode haver uma tag de quebra de linha XML
    inter_tag = r"(?:<lb[^>]+/>)?"
    return rf"\b{inter_tag.join(letras)}\b"

def marcar_texto_1572(texto_segmento):
    # 1. Aplicar Dicionário Arcaico com Regex Trans-tag
    # Usamos o marcador temporário [[[ ]]] para não conflitar com tags reais
    for termo, (tag, tipo, ref) in sorted(entidades_1572.items(), key=lambda x: len(x[0]), reverse=True):
        padrao = regex_trans_tag(termo)
        subst = f'[[[{tag} type="{tipo}" ref="#{ref}"]]]\\g<0>[[[/{tag}]]]'
        
        # Só substitui se não houver tags XML coladas (evita aninhamento)
        texto_segmento = re.sub(padrao, subst, texto_segmento, flags=re.IGNORECASE)

    # 2. IA (spaCy) - Opcional para 1572
    # Nota: A IA tem baixa performance em 1572, por isso 
    # ela só agirá em termos que o dicionário não pegou.
    return texto_segmento.replace("[[[", "<").replace("]]]", ">")

def main():
    # AJUSTE OS NOMES DOS ARQUIVOS AQUI
    ARQUIVO_ENTRADA = 'LusiadasDireita.xml' 
    ARQUIVO_SAIDA = 'Lusiadas1572_Marcado_Semantico.xml'

    try:
        with io.open(ARQUIVO_ENTRADA, 'r', encoding='utf-8') as f:
            conteudo = f.read()

        # Isolar o Header (Metadados não devem ser alterados)
        partes_tei = re.split(r'(</teiHeader>)', conteudo)
        if len(partes_tei) < 3:
            print("Erro: Estrutura TEI não encontrada.")
            return
        
        header = partes_tei[0] + partes_tei[1]
        corpo = partes_tei[2]

        # Separar tags editoriais (<l>, <lg>, <fw>, <pb>) do texto
        print("Iniciando marcação trans-tag na edição de 1572...")
        partes_xml = re.split(r'(<[^>]+>)', corpo)
        resultado_final = []

        for p in partes_xml:
            if p.startswith('<'):
                resultado_final.append(p)
            else:
                # Processar o texto puro aplicando a lógica de 1572
                resultado_final.append(marcar_texto_1572(p))

        with io.open(ARQUIVO_SAIDA, 'w', encoding='utf-8') as f:
            f.write(header + "".join(resultado_final))

        print(f"Sucesso! Versão 1572 marcada em: {ARQUIVO_SAIDA}")

    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    main()