# -*- coding: utf-8 -*-
"""Extrai onomástica, referenciação e aninhamentos TEI; gera CSV, XLSX, redes GraphML e PNG.
Uso: python scriptonomastica_adaptado.py --corpus arquivo.xml --autoridades autoridades.xml --saida resultados
Dependências: pip install networkx matplotlib artifact-tool
"""
import argparse
import csv
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
import xml.etree.ElementTree as ET
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

XML_ID = '{http://www.w3.org/XML/1998/namespace}id'
TAGS = {'persName', 'placeName', 'rs'}

def nome(tag): return tag.rsplit('}', 1)[-1]
def texto(el): return ' '.join(''.join(el.itertext()).split())
def ref_id(raw): return raw.strip()[1:] if raw and raw.strip().startswith('#') else (raw.strip() if raw else '')
def salvar_csv(path, rows, cols):
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore'); w.writeheader(); w.writerows(rows)

def autoridades_xml(path):
    root = ET.parse(path).getroot(); result = {}; repetidos=[]
    for el in root.iter():
        eid=el.get(XML_ID)
        if not eid: continue
        if eid in result: repetidos.append(eid)
        label=next((texto(c) for c in el if nome(c.tag) in {'persName','placeName','orgName','name'} and texto(c)),eid)
        result[eid]={'nome':label,'categoria':nome(el.tag),'wikidata':el.get('ref','')}
    return result,repetidos

def extrair(path, authorities):
    root=ET.parse(path).getroot(); rows=[]; nests=[]; seq=0
    for canto in root.iter():
        if nome(canto.tag)!='lg' or canto.get('type')!='estrofe': continue
        est=canto.get('n','')
        for linha_idx,linha in enumerate([x for x in canto if nome(x.tag)=='l'],1):
            def visita(el, parents):
                nonlocal seq
                tag=nome(el.tag); novos=parents
                if tag in TAGS:
                    seq+=1; mid=f'M{seq:04d}'; raw=el.get('ref',''); eid=ref_id(raw)
                    auth=authorities.get(eid,{})
                    categoria=auth.get('categoria','não encontrada' if eid else 'sem referência')
                    tipo=el.get('type','')
                    natureza= ('nome próprio/topônimo' if tag in {'persName','placeName'} else
                               'referência coletiva' if tipo=='group' else
                               'referência indireta a pessoa' if tipo=='person' else
                               'referência indireta a lugar' if tipo=='place' else 'referência indireta')
                    rows.append(dict(mention_id=mid,entity_id=eid,entity_name=auth.get('nome',''),entity_category=categoria,
                        textual_form=texto(el),tei_element=tag,tei_type=tipo,reference_type=natureza,
                        stanza=est,line=linha_idx,line_text=texto(linha),raw_ref=raw,
                        ref_status=('sem @ref' if not eid else 'sem # inicial' if not raw.startswith('#') else 'ID inexistente' if eid not in authorities else 'válida'),
                        parent_mention_id=parents[-1]['id'] if parents else '',nesting_level=len(parents),
                        authority_url=auth.get('wikidata','')))
                    for p in parents:
                        nests.append(dict(parent_mention_id=p['id'],child_mention_id=mid,parent_form=p['form'],child_form=texto(el),
                            parent_entity_id=p['eid'],child_entity_id=eid,parent_element=p['tag'],child_element=tag,
                            stanza=est,line=linha_idx,relation='aninhamento estrutural (não implica interação)'))
                    novos=parents+[{'id':mid,'form':texto(el),'eid':eid,'tag':tag}]
                for child in el: visita(child,novos)
            visita(linha,[])
    return rows,nests

def variantes(rows):
    groups=defaultdict(list)
    for r in rows:
        if not r['entity_id']: continue
        key=tuple(r[k] for k in ('entity_id','entity_name','entity_category','textual_form','tei_element','tei_type','reference_type'))
        groups[key].append(r)
    out=[]
    for k,rs in groups.items():
        est=sorted({x['stanza'] for x in rs},key=lambda x:int(x) if x.isdigit() else 9999)
        out.append(dict(zip(('entity_id','entity_name','entity_category','textual_form','tei_element','tei_type','reference_type'),k),occurrences=len(rs),stanzas=', '.join(est)))
    return sorted(out,key=lambda x:(x['entity_name'].casefold(),-x['occurrences'],x['textual_form']))

def resumo_entidades(rows):
    d=defaultdict(list)
    for r in rows:
        if r['entity_id']: d[r['entity_id']].append(r)
    return sorted([dict(entity_id=eid,entity_name=rs[0]['entity_name'],category=rs[0]['entity_category'],
        occurrences=len(rs),forms=len({x['textual_form'] for x in rs}),stanzas=len({x['stanza'] for x in rs}),
        direct_names=sum(x['tei_element']!='rs' for x in rs),indirect_refs=sum(x['tei_element']=='rs' for x in rs))
        for eid,rs in d.items()],key=lambda x:(-x['occurrences'],x['entity_name']))

def bipartida(var):
    G=nx.Graph()
    for r in var:
        eid='ENT::'+r['entity_id']; form='FORM::'+r['entity_id']+'::'+r['textual_form']
        G.add_node(eid,label=r['entity_name'],kind='entidade',category=r['entity_category'])
        G.add_node(form,label=r['textual_form'],kind='forma',category=r['reference_type'])
        if G.has_edge(eid,form): G[eid][form]['weight']+=r['occurrences']
        else: G.add_edge(eid,form,weight=r['occurrences'])
    return G

def coocorrencia(rows, only_people=False):
    G=nx.Graph(); by_stanza=defaultdict(set); labels={}
    for r in rows:
        if not r['entity_id']: continue
        if only_people and r['entity_category'] not in {'person','personGrp'}: continue
        eid=r['entity_id']; by_stanza[r['stanza']].add(eid)
        labels[eid]=(r['entity_name'],r['entity_category'])
    for eid,(label,cat) in labels.items(): G.add_node(eid,label=label,category=cat)
    weights=Counter()
    for ids in by_stanza.values():
        for a,b in combinations(sorted(ids),2): weights[(a,b)]+=1
    for (a,b),w in weights.items(): G.add_edge(a,b,weight=w,relation='coocorrência na mesma estrofe')
    return G

def rede_aninhamento(nests, rows):
    G=nx.DiGraph(); index={r['mention_id']:r for r in rows}
    for n in nests:
        p=index[n['parent_mention_id']]; c=index[n['child_mention_id']]
        for r in (p,c):
            G.add_node(r['mention_id'],label=r['textual_form'],entity_id=r['entity_id'],tei_element=r['tei_element'],stanza=r['stanza'])
        G.add_edge(p['mention_id'],c['mention_id'],relation='contém',stanza=n['stanza'])
    return G

def figura(G,path,title,limit=35):
    if not G.number_of_nodes(): return
    # Figura é amostra legível; GraphML sempre contém rede integral.
    ranks=sorted(G.nodes(),key=lambda n:G.degree(n,weight='weight'),reverse=True)
    keep=ranks[:limit]; H=G.subgraph(keep).copy()
    pos=nx.spring_layout(H,seed=42,k=1.6/max(1,len(H))**0.5,iterations=120)
    fig,ax=plt.subplots(figsize=(15,11))
    nx.draw_networkx_edges(H,pos,ax=ax,alpha=.24,width=[.5+min(5,H[u][v].get('weight',1)) for u,v in H.edges()])
    nx.draw_networkx_nodes(H,pos,ax=ax,node_size=[260+40*H.degree(n) for n in H],alpha=.85)
    nx.draw_networkx_labels(H,pos,labels={n:H.nodes[n].get('label',n) for n in H},font_size=8,ax=ax)
    ax.set_title(title+' (recorte visual; rede integral no GraphML)');ax.axis('off')
    fig.tight_layout();fig.savefig(path,dpi=190,bbox_inches='tight');plt.close(fig)

def exportar_xlsx(path,tables):
    try:
        from artifact_tool import Workbook, SpreadsheetFile
    except ImportError:
        print('XLSX não gerado: instale artifact-tool; os CSVs foram gerados.');return
    wb=Workbook.create()
    for sheet_name,(rows,columns) in tables.items():
        sh=wb.worksheets.add(sheet_name)
        matrix=[columns]+[[r.get(c,'') for c in columns] for r in rows]
        sh.get_range_by_indexes(0,0,len(matrix),len(columns)).values=matrix
        sh.get_range_by_indexes(0,0,1,len(columns)).format={'fill':'#17324D','font':{'bold':True,'color':'#FFFFFF'},'row_height':25}
        sh.freeze_panes.freeze_rows(1)
        sh.get_range_by_indexes(0,0,len(matrix),len(columns)).format.column_width=19
    SpreadsheetFile.export_xlsx(wb).save(str(path))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--corpus',default='Lusiadas_Canto1_marcadoVF.xml')
    p.add_argument('--autoridades',default='autoridade_lusiadas.xml')
    p.add_argument('--saida',default='resultados_onomasticavf')
    args=p.parse_args(); out=Path(args.saida);out.mkdir(parents=True,exist_ok=True)
    auth,duplicates=autoridades_xml(args.autoridades); rows,nests=extrair(args.corpus,auth)
    vars=variantes(rows); ents=resumo_entidades(rows)
    issues=[r for r in rows if r['ref_status']!='válida']
    tables={
      'Mencoes':(rows,list(rows[0]) if rows else []),
      'Variantes':(vars,list(vars[0]) if vars else []),
      'Entidades':(ents,list(ents[0]) if ents else []),
      'Aninhamentos':(nests,list(nests[0]) if nests else []),
      'Revisao':(issues,list(rows[0]) if rows else [])}
    for title,(data,cols) in tables.items():
        if cols: salvar_csv(out/(title.lower()+'.csv'),data,cols)
    exportar_xlsx(out/'tabelas_onomastica.xlsx',tables)
    networks={'rede_formas_entidades':bipartida(vars),'rede_coocorrencia_geral':coocorrencia(rows),
              'rede_coocorrencia_personagens':coocorrencia(rows,True),'rede_aninhamentos':rede_aninhamento(nests,rows)}
    for name,G in networks.items():
        nx.write_graphml(G,out/(name+'.graphml'))
        figura(G,out/(name+'.png'),name.replace('_',' ').title())
    total_refs=sum(bool(r['entity_id']) for r in rows)
    summary=[f'Total de marcações: {len(rows)}',f'Marcações com @ref: {total_refs}',
             f'Marcações sem @ref: {len(rows)-total_refs}',f'Entidades distintas referenciadas: {len(ents)}',
             f'Variantes agrupadas: {len(vars)}',f'Relações de aninhamento (ancestral-descendente): {len(nests)}',
             f'IDs repetidos na autoridade: {duplicates}',
             'Aviso: coocorrência na estrofe NÃO equivale a interação entre personagens.',
             'Aviso: marcações aninhadas são contadas individualmente; uma expressão pode conter outra.']
    (out/'resumo.txt').write_text('\n'.join(summary),encoding='utf-8')
    print('\n'.join(summary));print('Saída:',out.resolve())
if __name__=='__main__': main()
