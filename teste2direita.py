import spacy
import io
import re

nlp = spacy.load("pt_core_news_lg")

def aplicar_marcacao_segura(texto):
    doc = nlp(texto)
    matches = []
    
    for ent in doc.ents:
        print(ent.text, ent.label_)
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
    ARQUIVO_ENTRADA = 'LusiadasDireita.xml'
    ARQUIVO_SAIDA = 'teste2direita.xml'

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