# -*- coding: utf-8 -*-
import re
import io

# 1. DICIONÁRIO ESPECÍFICO 1572 (Baseado no seu snippet)
entidades_1572 = {
    # Lugares
    "Occidental": ("placeName", "real", "ocidente"),
    "Lusitana": ("placeName", "real", "portugal"),
    "Taprobana": ("placeName", "real", "taprobana"),
    "Reino": ("placeName", "real", "portugal"),
    "Africa": ("placeName", "real", "africa"),
    "Asia": ("placeName", "real", "asia"),
    "Hypocrene": ("placeName", "myth", "hipocrene"),
    "Christandade": ("placeName", "real", "cristandade"),
    "Occidente": ("placeName", "real", "ocidente"),
    "Hemispherio": ("placeName", "real", "hemisferio"),
    "Rio": ("placeName", "real", "rio_ganges"), # Contextual no estrofe 8

    # Mitologia
    "Neptuno": ("persName", "myth", "neptuno"),
    "Marte": ("persName", "myth", "marte"),
    "Musa": ("persName", "myth", "musas"),
    "Tagides": ("persName", "myth", "tagides"),
    "Phebo": ("persName", "myth", "febo"),
    "Troyano": ("persName", "myth", "eneias"),
    "Grego": ("persName", "myth", "ulisses"),

    # Históricos
    "Alexandro": ("persName", "hist", "alexandre_magno"),
    "Trajano": ("persName", "hist", "trajano"),
    "Lusitano": ("persName", "hist", "portugueses"),
    "Deos": ("persName", "hist", "deus"),
    "Christo": ("persName", "hist", "cristo"),
    "Rei": ("persName", "hist", "d_sebastiao"), # Contextual na dedicatória

    # Coletivos
    "Maura": ("rs", "person", "mouros"),
    "Ismaelita": ("rs", "person", "mouros"),
    "Turco": ("rs", "person", "turcos"),
    "Gentio": ("rs", "person", "gentios"),
}

def marcar_1572(texto_bloco):
    # Ordenar por tamanho para não quebrar nomes compostos
    for termo in sorted(entidades_1572.keys(), key=len, reverse=True):
        tag, tipo, ref = entidades_1572[termo]
        
        # --- LÓGICA PARA QUEBRA DE LINHA ---
        # Criamos um padrão que permite que a tag <lb ... /> apareça em QUALQUER lugar da palavra
        # Ex: se o termo é "Lusitana", ele busca por L<lb/>u<lb/>s... etc.
        letras = [re.escape(l) for l in termo]
        # Padrão que permite a tag de quebra entre as letras
        padrao_regex = r"(<lb[^>]+/>)?".join(letras)
        
        # Busca garantindo fronteira de palavra poética
        regex_final = rf"\b{padrao_regex}\b"
        
        # Substituição
        # Nota: usamos \g<0> para manter o conteúdo original (incluindo as tags <lb/> se existirem)
        subst = f'<{tag} type="{tipo}" ref="#{ref}">\g<0></{tag}>'
        
        # Aplicamos a substituição apenas se não estiver já marcado
        if not re.search(rf'<{tag}[^>]*>\s*{padrao_regex}\s*</{tag}>', texto_bloco):
             texto_bloco = re.sub(regex_final, subst, texto_bloco, flags=re.IGNORECASE)

    return texto_bloco

def processar_canto_original():
    ARQUIVO_ENTRADA = 'LusiadasDireita.xml' # Nome do seu arquivo
    ARQUIVO_SAIDA = 'Lusiadas1572_Marcado.xml'

    try:
        with io.open(ARQUIVO_ENTRADA, 'r', encoding='utf-8') as f:
            conteudo = f.read()

        # Separar tags de texto
        # Adicionei <fw> e <pb> na lista de tags preservadas
        partes = re.split(r'(<[^>]+>)', conteudo)
        resultado = []

        print("Iniciando marcação na versão de 1572...")
        
        for p in partes:
            if p.startswith('<'):
                resultado.append(p)
            else:
                # Marcar o texto plano
                resultado.append(marcar_1572(p))

        with io.open(ARQUIVO_SAIDA, 'w', encoding='utf-8') as f:
            f.write("".join(resultado))

        print(f"Sucesso! Arquivo gerado: {ARQUIVO_SAIDA}")

    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    processar_canto_original()