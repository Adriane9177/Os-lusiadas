import spacy
import re

# =========================
# 1. CARREGAR MODELO
# =========================
nlp = spacy.load("pt_core_news_lg")

# =========================
# 2. DICIONÁRIO EXPANDIDO
# =========================
entidades_fixas = {
    # 👤 HISTÓRICOS
    "Vasco da Gama": ('persName', 'hist', 'v_gama'),
    "Dom Manuel": ('persName', 'hist', 'dom_manuel'),
    "Dom João II": ('persName', 'hist', 'dom_joao_ii'),
    "Dom Sebastião": ('persName', 'hist', 'dom_sebastiao'),
    "Afonso de Albuquerque": ('persName', 'hist', 'afonso_albuquerque'),
    "Constantino": ('persName', 'hist', 'constantino'),
    "Capitão": ('rs', 'person', 'v_gama'), 
    "grego":('rs', 'person', 'ulisses'),
    "troiano":('rs', 'person', 'eneias'),

    # 🧝 MITOLÓGICOS
    "Vênus": ('persName', 'myth', 'venus'),
    "Baco": ('persName', 'myth', 'baco'),
    "Netuno": ('persName', 'myth', 'netuno'),
    "Marte": ('persName', 'myth', 'marte'),
    "Júpiter": ('persName', 'myth', 'jupiter'),
    "Mercúrio": ('persName', 'myth', 'mercurio'),
    "Apolo": ('persName', 'myth', 'apolo'),
    "Minerva": ('persName', 'myth', 'minerva'),
    "Destino": ('rs', 'person', 'fado'),
    "Fado": ('persName', 'myth', 'fado'),
    "Citereia":('persName', 'myth', 'venus'),
    "clara Deia": ('rs', 'person', 'venus'),
    "Padre":('rs', 'person', 'jupiter'),
    "Lieo":('persName', 'myth', 'baco'),
    "grão Tebano":('rs', 'person', 'baco'),
    "Febo":('rs', 'person', 'apolo'),


    # 🌍 LUGARES
    "Portugal": ('placeName', 'real', 'portugal'),
    "Lisboa": ('placeName', 'real', 'lisboa'),
    "Índia": ('placeName', 'real', 'india'),
    "África": ('placeName', 'real', 'africa'),
    "Ásia": ('placeName', 'real', 'asia'),
    "Europa": ('placeName', 'real', 'europa'),
    "Rio Ganges": ('placeName', 'real', 'rio_ganges'),
    "Ganges": ('placeName', 'real', 'rio_ganges'),
    "Mar Cáspio": ('placeName', 'real', 'mar_caspio'),
}

TERMOS_FIXOS_LOWER = {k.lower() for k in entidades_fixas}

# =========================
# 3. FUNÇÃO PRINCIPAL
# =========================
def marcar_entidades(texto):
    mapa = {}
    texto_proc = texto

    # =========================
    # 3.1 Substituir entidades fixas (PRIORIDADE)
    # =========================
    for i, termo in enumerate(sorted(entidades_fixas.keys(), key=len, reverse=True)):
        placeholder = f"__ENT_{i}__"
        if termo in texto_proc:
            texto_proc = texto_proc.replace(termo, placeholder)
            mapa[placeholder] = termo

    # =========================
    # 3.2 Rodar spaCy
    # =========================
    doc = nlp(texto_proc)
    resultado = texto_proc

    # =========================
    # 3.3 Marcação automática
    # =========================
    for ent in doc.ents:
        texto_ent = ent.text

        # ignorar placeholders
        if texto_ent.startswith("__ENT_"):
            continue

        # ignorar termos já controlados
        if texto_ent.lower() in TERMOS_FIXOS_LOWER:
            continue

        # classificar
        if ent.label_ == "PER":
            tag = "persName"
            tipo = "hist"
        elif ent.label_ in ["LOC", "GPE"]:
            tag = "placeName"
            tipo = "real"
        else:
            continue

        marcado = f'<{tag} type="{tipo}" ref="{texto_ent.lower().replace(" ", "_")}">{texto_ent}</{tag}>'

        # substituição segura (evita duplicação)
        resultado = resultado.replace(texto_ent, marcado)

    # =========================
    # 3.4 Restaurar entidades fixas
    # =========================
    for placeholder, termo in mapa.items():
        tag, tipo, ref = entidades_fixas[termo]

        if tag == "rs":
            marcado = f'<rs type="{tipo}" ref="{ref}">{termo}</rs>'
        else:
            marcado = f'<{tag} type="{tipo}" ref="{ref}">{termo}</{tag}>'

        resultado = resultado.replace(placeholder, marcado)

    return resultado


# =========================
# 4. LEITURA DO XML ORIGINAL (NÃO ALTERA)
# =========================
with open("LusiadasModernizado.xml", "r", encoding="utf-8") as f:
    conteudo = f.read()

# =========================
# 5. PROCESSAR
# =========================
conteudo_marcado = marcar_entidades(conteudo)

# =========================
# 6. SALVAR (MESMO NOME QUE VOCÊ USAVA)
# =========================
with open("Lusiadasteste2_marcado.xml", "w", encoding="utf-8") as f:
    f.write(conteudo_marcado)

print("Processamento concluído!")