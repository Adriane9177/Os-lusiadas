# -*- coding: utf-8 -*-

"""
Análise de entidades anotadas em TEI/XML - Os Lusíadas

Gera:
1. tabela_variantes.csv
2. tabela_variantes.xlsx
3. rede_bipartida.png
4. rede_bipartida.graphml
5. rede_coocorrencia.png
6. rede_coocorrencia.graphml

Dependências:
    pip install pandas networkx matplotlib openpyxl

Uso:
    python analise_entidades.py
"""

from pathlib import Path
from collections import defaultdict, Counter
from itertools import combinations
import xml.etree.ElementTree as ET

import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt


# ============================================================
# CONFIGURAÇÃO
# ============================================================

ARQUIVO_CORPUS = "Lusiadas_Canto1_marcado.xml"
ARQUIVO_AUTORIDADES = "autoridade_lusiadas.xml"

PASTA_SAIDA = Path("resultados_rede")
PASTA_SAIDA.mkdir(exist_ok=True)

# Para a rede de coocorrência:
# 1 = mostra qualquer coocorrência;
# 2 = mostra apenas pares que aparecem juntos em pelo menos 2 estrofes etc.
PESO_MINIMO_COO = 1

# Para a rede bipartida:
# True = inclui formas que aparecem apenas uma vez
# False = mostra apenas formas com mais de uma ocorrência
INCLUIR_HAPAX = True


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

XML_ID = "{http://www.w3.org/XML/1998/namespace}id"


def local_name(tag):
    """
    Remove namespace de uma tag XML.

    Ex.:
    {http://www.tei-c.org/ns/1.0}persName -> persName
    """
    return tag.split("}")[-1]


def limpar_ref(ref):
    """
    Normaliza o @ref interno.

    #v_gama -> v_gama
    """
    if not ref:
        return None

    ref = ref.strip()

    if ref.startswith("#"):
        ref = ref[1:]

    return ref


def texto_elemento(elemento):
    """
    Recupera todo o texto contido no elemento,
    inclusive quando existem tags aninhadas.

    Ex.:
    <rs>Os Doze de <placeName>Inglaterra</placeName></rs>

    retorna:
    Os Doze de Inglaterra
    """
    texto = "".join(elemento.itertext())

    # remove espaços duplicados
    texto = " ".join(texto.split())

    return texto.strip()


# ============================================================
# 1. CARREGAR BASE DE AUTORIDADES
# ============================================================

def carregar_autoridades(caminho):
    """
    Cria dicionário:

    xml:id -> {
        nome: ...
        categoria: ...
    }

    Funciona com person, personGrp, place etc.,
    desde que o elemento possua xml:id.
    """

    tree = ET.parse(caminho)
    root = tree.getroot()

    autoridades = {}

    for elem in root.iter():

        entity_id = elem.attrib.get(XML_ID)

        if not entity_id:
            continue

        categoria_elemento = local_name(elem.tag)

        nome = None

        # procura o primeiro elemento que possa funcionar
        # como nome normalizado da autoridade
        for filho in elem.iter():

            tag = local_name(filho.tag)

            if tag in {
                "persName",
                "placeName",
                "orgName",
                "name"
            }:
                candidato = texto_elemento(filho)

                if candidato:
                    nome = candidato
                    break

        if not nome:
            nome = entity_id

        autoridades[entity_id] = {
            "nome": nome,
            "categoria": categoria_elemento
        }

    return autoridades


# ============================================================
# 2. EXTRAIR TODAS AS MENÇÕES DO CORPUS
# ============================================================

def extrair_mencoes(caminho_corpus, autoridades):
    """
    Localiza:
        <persName>
        <placeName>
        <rs>

    desde que tenham atributo @ref.

    Para cada ocorrência registra:
        - forma textual
        - entidade normalizada
        - elemento TEI
        - @type
        - estrofe
        - tipo de referenciação
    """

    tree = ET.parse(caminho_corpus)
    root = tree.getroot()

    mencoes = []

    # percorre as estrofes
    for lg in root.iter():

        if local_name(lg.tag) != "lg":
            continue

        if lg.attrib.get("type") != "estrofe":
            continue

        estrofe = lg.attrib.get("n", "")

        for elem in lg.iter():

            tag = local_name(elem.tag)

            if tag not in {"persName", "placeName", "rs"}:
                continue

            ref = limpar_ref(elem.attrib.get("ref"))

            # ignora marcações sem ligação a uma entidade
            if not ref:
                continue

            forma = texto_elemento(elem)

            if not forma:
                continue

            tipo = elem.attrib.get("type", "")

            # ------------------------------------------------
            # Classificação da natureza da ocorrência
            # ------------------------------------------------

            if tag == "persName":
                natureza = "nome explícito"

            elif tag == "placeName":
                natureza = "nome explícito"

            elif tag == "rs":
                if tipo == "group":
                    natureza = "referência coletiva"
                elif tipo == "person":
                    natureza = "referência indireta a pessoa"
                elif tipo == "place":
                    natureza = "referência indireta a lugar"
                else:
                    natureza = "referência indireta"

            else:
                natureza = ""

            autoridade = autoridades.get(
                ref,
                {
                    "nome": ref,
                    "categoria": "não encontrada"
                }
            )

            mencoes.append({
                "entity_id": ref,
                "entity_name": autoridade["nome"],
                "entity_category": autoridade["categoria"],
                "textual_form": forma,
                "tei_element": tag,
                "tei_type": tipo,
                "reference_type": natureza,
                "stanza": estrofe
            })

    return pd.DataFrame(mencoes)


# ============================================================
# 3. TABELA DE VARIANTES REFERENCIAIS
# ============================================================

def gerar_tabela_variantes(df):
    """
    Agrupa ocorrências iguais da mesma entidade.

    Exemplo:

    jupiter | Júpiter | Júpiter  | 5
    jupiter | Júpiter | Tonante  | 1
    jupiter | Júpiter | Padre    | 1
    """

    registros = []

    grupos = df.groupby([
        "entity_id",
        "entity_name",
        "entity_category",
        "textual_form",
        "tei_element",
        "tei_type",
        "reference_type"
    ], dropna=False)

    for chave, grupo in grupos:

        (
            entity_id,
            entity_name,
            entity_category,
            textual_form,
            tei_element,
            tei_type,
            reference_type
        ) = chave

        estrofes = sorted(
            set(
                str(x)
                for x in grupo["stanza"].tolist()
                if str(x)
            ),
            key=lambda x: int(x) if x.isdigit() else x
        )

        registros.append({
            "entity_id": entity_id,
            "entity_name": entity_name,
            "entity_category": entity_category,
            "textual_form": textual_form,
            "tei_element": tei_element,
            "tei_type": tei_type,
            "reference_type": reference_type,
            "occurrences": len(grupo),
            "stanzas": ", ".join(estrofes)
        })

    tabela = pd.DataFrame(registros)

    tabela = tabela.sort_values(
        ["entity_name", "occurrences", "textual_form"],
        ascending=[True, False, True]
    )

    caminho_csv = PASTA_SAIDA / "tabela_variantes.csv"
    caminho_xlsx = PASTA_SAIDA / "tabela_variantes.xlsx"

    tabela.to_csv(
        caminho_csv,
        index=False,
        encoding="utf-8-sig"
    )

    tabela.to_excel(
        caminho_xlsx,
        index=False
    )

    return tabela


# ============================================================
# 4. REDE BIPARTIDA
# ============================================================

def gerar_rede_bipartida(tabela):
    """
    Rede:

           forma textual
                |
             entidade

    Cada forma textual é conectada ao referente
    apontado pelo @ref.

    Peso da aresta = número de ocorrências dessa forma
    para aquela entidade.
    """

    B = nx.Graph()

    for _, row in tabela.iterrows():

        if not INCLUIR_HAPAX and row["occurrences"] == 1:
            continue

        entity_id = f"ENT::{row['entity_id']}"

        # IMPORTANTE:
        # adicionamos o ID da entidade também ao identificador da forma.
        #
        # Assim, se uma mesma expressão textual apontar para entidades
        # diferentes em contextos diferentes, não haverá colisão.
        form_id = (
            f"FORM::{row['entity_id']}::"
            f"{row['textual_form']}"
        )

        # nó entidade
        B.add_node(
            entity_id,
            bipartite="entity",
            label=row["entity_name"],
            entity_id=row["entity_id"],
            category=row["entity_category"]
        )

        # nó forma
        B.add_node(
            form_id,
            bipartite="form",
            label=row["textual_form"],
            reference_type=row["reference_type"],
            tei_element=row["tei_element"],
            tei_type=row["tei_type"]
        )

        # ligação forma -> entidade
        B.add_edge(
            form_id,
            entity_id,
            weight=int(row["occurrences"])
        )

    # exporta para Gephi
    nx.write_graphml(
        B,
        PASTA_SAIDA / "rede_bipartida.graphml"
    )

    # --------------------------------------------------------
    # Visualização
    # --------------------------------------------------------

    entidades = [
        n for n, d in B.nodes(data=True)
        if d.get("bipartite") == "entity"
    ]

    formas = [
        n for n, d in B.nodes(data=True)
        if d.get("bipartite") == "form"
    ]

    if not B.nodes:
        return B

    # layout bipartido
    pos = nx.bipartite_layout(
        B,
        entidades,
        align="vertical",
        scale=2
    )

    plt.figure(figsize=(18, 14))

    # entidades
    nx.draw_networkx_nodes(
        B,
        pos,
        nodelist=entidades,
        node_size=1300,
        alpha=0.85
    )

    # formas
    nx.draw_networkx_nodes(
        B,
        pos,
        nodelist=formas,
        node_size=500,
        alpha=0.65
    )

    # espessura de acordo com frequência
    pesos = [
        max(0.7, B[u][v]["weight"] * 0.8)
        for u, v in B.edges()
    ]

    nx.draw_networkx_edges(
        B,
        pos,
        width=pesos,
        alpha=0.4
    )

    labels = {
        n: d.get("label", n)
        for n, d in B.nodes(data=True)
    }

    nx.draw_networkx_labels(
        B,
        pos,
        labels=labels,
        font_size=7
    )

    plt.title(
        "Rede bipartida entre formas referenciais e entidades "
        "no Canto I d'Os Lusíadas"
    )

    plt.axis("off")
    plt.tight_layout()

    plt.savefig(
        PASTA_SAIDA / "rede_bipartida.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    return B


# ============================================================
# 5. REDE DE COOCORRÊNCIA POR ESTROFE
# ============================================================

def gerar_rede_coocorrencia(df):
    """
    Duas entidades são ligadas quando aparecem
    na mesma estrofe.

    Peso da aresta = número de estrofes em que
    o par aparece conjuntamente.
    """

    G = nx.Graph()

    # --------------------------------------------------------
    # Adicionar nós
    # --------------------------------------------------------

    entidades = (
        df[
            [
                "entity_id",
                "entity_name",
                "entity_category"
            ]
        ]
        .drop_duplicates()
    )

    for _, row in entidades.iterrows():

        G.add_node(
            row["entity_id"],
            label=row["entity_name"],
            category=row["entity_category"]
        )

    # --------------------------------------------------------
    # Contar pares por estrofe
    # --------------------------------------------------------

    pesos = Counter()

    for estrofe, grupo in df.groupby("stanza"):

        ids = sorted(set(grupo["entity_id"]))

        for a, b in combinations(ids, 2):
            pesos[(a, b)] += 1

    # --------------------------------------------------------
    # Inserir somente relações acima do limite
    # --------------------------------------------------------

    for (a, b), peso in pesos.items():

        if peso >= PESO_MINIMO_COO:

            G.add_edge(
                a,
                b,
                weight=peso
            )

    # remover nós isolados
    isolados = list(nx.isolates(G))
    G.remove_nodes_from(isolados)

    nx.write_graphml(
        G,
        PASTA_SAIDA / "rede_coocorrencia.graphml"
    )

    if not G.nodes:
        return G

    # --------------------------------------------------------
    # Layout
    # --------------------------------------------------------

    pos = nx.spring_layout(
        G,
        seed=42,
        k=1.2
    )

    plt.figure(figsize=(16, 14))

    # tamanho segundo grau ponderado
    tamanhos = []

    for no in G.nodes():

        grau_ponderado = G.degree(
            no,
            weight="weight"
        )

        tamanhos.append(
            250 + grau_ponderado * 80
        )

    pesos_arestas = [
        max(0.5, G[u][v]["weight"] * 0.8)
        for u, v in G.edges()
    ]

    nx.draw_networkx_nodes(
        G,
        pos,
        node_size=tamanhos,
        alpha=0.8
    )

    nx.draw_networkx_edges(
        G,
        pos,
        width=pesos_arestas,
        alpha=0.3
    )

    labels = {
        n: G.nodes[n].get("label", n)
        for n in G.nodes()
    }

    nx.draw_networkx_labels(
        G,
        pos,
        labels=labels,
        font_size=7
    )

    plt.title(
        "Rede de coocorrência de entidades por estrofe "
        "no Canto I d'Os Lusíadas"
    )

    plt.axis("off")
    plt.tight_layout()

    plt.savefig(
        PASTA_SAIDA / "rede_coocorrencia.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    return G


# ============================================================
# 6. RELATÓRIO RESUMIDO
# ============================================================

def mostrar_resumo(df, tabela, B, G):

    print("\n" + "=" * 60)
    print("RESUMO DA ANÁLISE")
    print("=" * 60)

    print(
        f"\nOcorrências anotadas com @ref: {len(df)}"
    )

    print(
        f"Entidades distintas: "
        f"{df['entity_id'].nunique()}"
    )

    print(
        f"Formas referenciais distintas: "
        f"{len(tabela)}"
    )

    print(
        f"\nRede bipartida:"
        f"\n  Nós: {B.number_of_nodes()}"
        f"\n  Arestas: {B.number_of_edges()}"
    )

    print(
        f"\nRede de coocorrência:"
        f"\n  Nós: {G.number_of_nodes()}"
        f"\n  Arestas: {G.number_of_edges()}"
    )

    # --------------------------------------------------------
    # entidades com maior variedade de formas
    # --------------------------------------------------------

    diversidade = (
        tabela
        .groupby(
            ["entity_id", "entity_name"]
        )
        ["textual_form"]
        .nunique()
        .sort_values(ascending=False)
    )

    print(
        "\nEntidades com maior diversidade "
        "de formas referenciais:\n"
    )

    print(diversidade.head(15))


# ============================================================
# MAIN
# ============================================================

def main():

    print("Carregando autoridades...")

    autoridades = carregar_autoridades(
        ARQUIVO_AUTORIDADES
    )

    print(
        f"{len(autoridades)} registros "
        "de autoridade encontrados."
    )

    print("\nExtraindo menções do corpus...")

    df = extrair_mencoes(
        ARQUIVO_CORPUS,
        autoridades
    )

    print(
        f"{len(df)} ocorrências anotadas "
        "encontradas."
    )

    # tabela
    tabela = gerar_tabela_variantes(df)

    print(
        "\nTabela de variantes criada."
    )

    # bipartida
    print(
        "Gerando rede bipartida..."
    )

    B = gerar_rede_bipartida(tabela)

    # coocorrência
    print(
        "Gerando rede de coocorrência..."
    )

    G = gerar_rede_coocorrencia(df)

    mostrar_resumo(
        df,
        tabela,
        B,
        G
    )

    print(
        "\nArquivos gerados em:",
        PASTA_SAIDA.resolve()
    )


if __name__ == "__main__":
    main()