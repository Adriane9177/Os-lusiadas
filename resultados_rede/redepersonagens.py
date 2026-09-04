# -*- coding: utf-8 -*-

"""
Rede de personagens no Canto I d'Os Lusíadas

Personagens focais:
- Júpiter
- Vénus
- Baco
- Marte
- Vasco da Gama

A rede inclui também os vizinhos diretos, isto é,
personagens que aparecem na mesma estrofe que pelo
menos um dos cinco personagens focais.

Dependências:
    pip install networkx matplotlib

Uso:
    python rede_personagens.py
"""

from pathlib import Path
from itertools import combinations
import xml.etree.ElementTree as ET

import networkx as nx
import matplotlib.pyplot as plt


# ============================================================
# CONFIGURAÇÕES
# ============================================================

ARQUIVO_CORPUS = "Lusiadas_Canto1_marcado.xml"

PASTA_SAIDA = Path("resultados_rede_personagens")
PASTA_SAIDA.mkdir(exist_ok=True)

# Identificadores usados no seu XML
PERSONAGENS_FOCAIS = {
    "jupiter",
    "venus",
    "baco",
    "marte",
    "v_gama"
}


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def local_name(tag):
    """
    Remove o namespace TEI.

    Ex.:
    {http://www.tei-c.org/ns/1.0}persName
    ->
    persName
    """
    return tag.split("}")[-1]


def limpar_ref(ref):
    """
    Remove o # do atributo @ref.

    #jupiter -> jupiter
    """
    if not ref:
        return None

    ref = ref.strip()

    if ref.startswith("#"):
        ref = ref[1:]

    return ref


def texto_elemento(elemento):
    """
    Recupera todo o texto contido dentro do elemento,
    inclusive quando existem elementos internos.
    """
    texto = "".join(elemento.itertext())

    return " ".join(texto.split()).strip()


# ============================================================
# 1. EXTRAIR PERSONAGENS POR ESTROFE
# ============================================================

def extrair_personagens(caminho_xml):
    """
    Retorna um dicionário no formato:

    estrofe -> {
        entity_id: formas textuais encontradas
    }

    São considerados apenas:
    - <persName>
    - <rs type="person">
    """

    tree = ET.parse(caminho_xml)
    root = tree.getroot()

    estrofes = {}

    for lg in root.iter():

        if local_name(lg.tag) != "lg":
            continue

        if lg.attrib.get("type") != "estrofe":
            continue

        numero_estrofe = lg.attrib.get("n", "")

        personagens = {}

        for elem in lg.iter():

            tag = local_name(elem.tag)

            # -----------------------------
            # <persName>
            # -----------------------------

            if tag == "persName":

                ref = limpar_ref(
                    elem.attrib.get("ref")
                )

                if not ref:
                    continue

                forma = texto_elemento(elem)

            # -----------------------------
            # <rs type="person">
            # -----------------------------

            elif (
                tag == "rs"
                and elem.attrib.get("type") == "person"
            ):

                ref = limpar_ref(
                    elem.attrib.get("ref")
                )

                if not ref:
                    continue

                forma = texto_elemento(elem)

            else:
                continue

            if not forma:
                continue

            personagens.setdefault(
                ref,
                set()
            ).add(forma)

        if personagens:
            estrofes[numero_estrofe] = personagens

    return estrofes


# ============================================================
# 2. CRIAR REDE COMPLETA DE PERSONAGENS
# ============================================================

def criar_rede_completa(estrofes):
    """
    Liga dois personagens quando aparecem na mesma estrofe.

    weight = número de estrofes compartilhadas
    stanzas = lista de estrofes compartilhadas
    """

    G = nx.Graph()

    formas_por_entidade = {}

    for numero_estrofe, personagens in estrofes.items():

        ids = sorted(personagens.keys())

        # registrar formas textuais
        for entity_id, formas in personagens.items():

            formas_por_entidade.setdefault(
                entity_id,
                set()
            ).update(formas)

            if not G.has_node(entity_id):

                G.add_node(
                    entity_id,
                    formas=" | ".join(
                        sorted(formas)
                    )
                )

        # criar pares
        for a, b in combinations(ids, 2):

            if G.has_edge(a, b):

                G[a][b]["weight"] += 1
                G[a][b]["stanzas"].append(
                    numero_estrofe
                )

            else:

                G.add_edge(
                    a,
                    b,
                    weight=1,
                    stanzas=[numero_estrofe]
                )

    # atualizar formas dos nós
    for entity_id, formas in formas_por_entidade.items():

        G.nodes[entity_id]["formas"] = (
            " | ".join(sorted(formas))
        )

    return G


# ============================================================
# 3. SELECIONAR FOCAIS + VIZINHOS
# ============================================================

def selecionar_rede_focal(G):
    """
    Seleciona:
    - os cinco personagens focais
    - todos os vizinhos diretos deles
    """

    selecionados = set()

    for personagem in PERSONAGENS_FOCAIS:

        if personagem not in G:
            print(
                f"AVISO: {personagem} "
                f"não foi encontrado no grafo."
            )
            continue

        selecionados.add(personagem)

        selecionados.update(
            G.neighbors(personagem)
        )

    H = G.subgraph(
        selecionados
    ).copy()

    return H


# ============================================================
# 4. NOMES PARA EXIBIÇÃO
# ============================================================

NOMES_EXIBICAO = {
    "jupiter": "Júpiter",
    "venus": "Vénus",
    "baco": "Baco",
    "marte": "Marte",
    "v_gama": "Vasco da Gama"
}


def nome_do_no(G, no):
    """
    Usa nome conhecido para os focais.
    Para os demais, usa a primeira forma textual encontrada.
    """

    if no in NOMES_EXIBICAO:
        return NOMES_EXIBICAO[no]

    formas = G.nodes[no].get(
        "formas",
        no
    )

    # primeira forma
    return formas.split(" | ")[0]


# ============================================================
# 5. GERAR FIGURA
# ============================================================

def gerar_figura(H):
    """
    Gera PNG da rede focal.
    """

    if H.number_of_nodes() == 0:
        print("Nenhum nó encontrado.")
        return

    # layout
    pos = nx.spring_layout(
        H,
        seed=42,
        k=1.5,
        iterations=200
    )

    plt.figure(
        figsize=(15, 12)
    )

    # -----------------------------
    # separar focais e vizinhos
    # -----------------------------

    focais = [
        n
        for n in H.nodes()
        if n in PERSONAGENS_FOCAIS
    ]

    vizinhos = [
        n
        for n in H.nodes()
        if n not in PERSONAGENS_FOCAIS
    ]

    # -----------------------------
    # tamanho dos focais
    # -----------------------------

    tamanho_focais = []

    for no in focais:

        grau = H.degree(
            no,
            weight="weight"
        )

        tamanho_focais.append(
            1800 + grau * 120
        )

    # -----------------------------
    # tamanho dos vizinhos
    # -----------------------------

    tamanho_vizinhos = []

    for no in vizinhos:

        grau = H.degree(
            no,
            weight="weight"
        )

        tamanho_vizinhos.append(
            500 + grau * 70
        )

    # -----------------------------
    # desenhar nós
    # -----------------------------

    nx.draw_networkx_nodes(
        H,
        pos,
        nodelist=focais,
        node_size=tamanho_focais,
        alpha=0.90
    )

    nx.draw_networkx_nodes(
        H,
        pos,
        nodelist=vizinhos,
        node_size=tamanho_vizinhos,
        alpha=0.60
    )

    # -----------------------------
    # espessura das arestas
    # -----------------------------

    pesos = []

    for u, v in H.edges():

        peso = H[u][v].get(
            "weight",
            1
        )

        pesos.append(
            0.7 + peso * 1.2
        )

    nx.draw_networkx_edges(
        H,
        pos,
        width=pesos,
        alpha=0.35
    )

    # -----------------------------
    # rótulos
    # -----------------------------

    labels = {
        no: nome_do_no(H, no)
        for no in H.nodes()
    }

    nx.draw_networkx_labels(
        H,
        pos,
        labels=labels,
        font_size=9
    )

    plt.title(
        "Rede de coocorrência de personagens selecionados "
        "no Canto I d'Os Lusíadas",
        fontsize=14
    )

    plt.axis("off")

    plt.tight_layout()

    arquivo_png = (
        PASTA_SAIDA /
        "rede_personagens_focais.png"
    )

    plt.savefig(
        arquivo_png,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    print(
        f"Figura salva em: {arquivo_png}"
    )


# ============================================================
# 6. EXPORTAR GRAPHML
# ============================================================

def exportar_graphml(H):
    """
    Exporta rede para Gephi.
    """

    # GraphML não aceita listas diretamente.
    # Converter lista de estrofes para string.

    for u, v in H.edges():

        estrofes = H[u][v].get(
            "stanzas",
            []
        )

        if isinstance(
            estrofes,
            list
        ):

            H[u][v]["stanzas"] = (
                ", ".join(
                    str(x)
                    for x in estrofes
                )
            )

    arquivo_graphml = (
        PASTA_SAIDA /
        "rede_personagens_focais.graphml"
    )

    nx.write_graphml(
        H,
        arquivo_graphml
    )

    print(
        f"GraphML salvo em: {arquivo_graphml}"
    )


# ============================================================
# 7. RELATÓRIO DAS RELAÇÕES
# ============================================================

def mostrar_relacoes(H):
    """
    Mostra no terminal as relações dos cinco focais.
    """

    print(
        "\n"
        + "=" * 60
    )

    print(
        "RELAÇÕES DOS PERSONAGENS FOCAIS"
    )

    print(
        "=" * 60
    )

    for personagem in PERSONAGENS_FOCAIS:

        if personagem not in H:
            continue

        print(
            f"\n{nome_do_no(H, personagem)}"
        )

        print("-" * 40)

        vizinhos = []

        for vizinho in H.neighbors(
            personagem
        ):

            peso = H[
                personagem
            ][vizinho]["weight"]

            estrofes = H[
                personagem
            ][vizinho]["stanzas"]

            vizinhos.append(
                (
                    vizinho,
                    peso,
                    estrofes
                )
            )

        # ordenar por maior peso
        vizinhos.sort(
            key=lambda x: x[1],
            reverse=True
        )

        for vizinho, peso, estrofes in vizinhos:

            print(
                f"  -> {nome_do_no(H, vizinho)}"
                f" | coocorrências: {peso}"
                f" | estrofes: {estrofes}"
            )


# ============================================================
# 8. MAIN
# ============================================================

def main():

    print(
        "Lendo corpus..."
    )

    estrofes = extrair_personagens(
        ARQUIVO_CORPUS
    )

    print(
        f"{len(estrofes)} estrofes "
        f"com personagens anotados."
    )

    print(
        "\nCriando rede completa..."
    )

    G = criar_rede_completa(
        estrofes
    )

    print(
        f"Rede completa:"
        f"\n  Nós: {G.number_of_nodes()}"
        f"\n  Arestas: {G.number_of_edges()}"
    )

    print(
        "\nSelecionando personagens focais "
        "e vizinhos..."
    )

    H = selecionar_rede_focal(
        G
    )

    print(
        f"Rede focal:"
        f"\n  Nós: {H.number_of_nodes()}"
        f"\n  Arestas: {H.number_of_edges()}"
    )

    gerar_figura(H)

    exportar_graphml(H)

    mostrar_relacoes(H)

    print(
        "\nAnálise concluída."
    )


if __name__ == "__main__":
    main()