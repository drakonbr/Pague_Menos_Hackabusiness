# 16 — Prompt da rodada: medicamentos na busca e interface mais fiel ao app

Branch: `feat/medicamentos-e-ui` · Aberto em 21/10/2026 · Status: **implementado e treinado em 21/10** (checklist na seção 7, medições na seção 9). Nada commitado ainda.

Este documento é o prompt de trabalho da rodada. Ele serve para conferir, no fim, se o que foi entregue segue o pedido. Cada item da seção 7 vira uma linha de "feito / não feito" com a prova (comando, teste ou tela).

## 1. Pedido original (resumo fiel)

1. Nova branch. Interface mais próxima e real do app da rede; fluxo de navegação consolidado, pensando em UX/UI.
2. Tirar a mensagem "procure um farmacêutico/médico" quando se pesquisa medicação. Ela atrapalha a lógica de uma farmácia: buscar "dor de cabeça" tem que trazer remédio para dor de cabeça, e o mesmo vale para qualquer medicação.
3. Se o banco não tem remédio para as áreas mais comuns, **adicionar**. Pelo menos **6 remédios por área**, entre os mais comprados. Áreas citadas: dor de cabeça, dor no corpo, dor muscular, dor de barriga; "todos os tipos principais".
4. Busca de medicação **e kits**. Exemplo: "remédio de dor de cabeça" mostra um kit com dipirona + paracetamol. **Revogado em 23/10 (#40, seção 15): remédio nunca entra em kit.**
5. **Nunca** mostrar "busque um farmacêutico/médico". No máximo, quando não houver remédio para o pedido: "Não está no banco de dados ainda."
6. **Não pode ser mockup.** Precisa ser treinado e implementado no GraphRAG.
7. Escrever este prompt antes de começar e mantê-lo na documentação. **Não inventar: na dúvida, perguntar.**

## 2. O que esta rodada revoga (registrar no doc 09)

| Antes | Agora |
| --- | --- |
| D-02: escopo só cosméticos e autocuidado | Medicamentos entram na busca e nos kits *(Desde 23/10, #40: remédio só na busca, nunca em kit.)* |
| D-22: medicamento só em reposição; o motor nunca nomeia nem sugere | O motor busca e nomeia medicamento; desde 23/10 (#40) não monta kit de remédio |
| doc 07: zona "bloqueado" para medicamento e sintoma, com encaminhamento | Sem bloqueio por medicamento ou sintoma; sem texto de encaminhamento |
| `safety.py`: `BLOCK_RULES` de medicamento e sintoma; `REFERRAL` | Removidos. O que sobrar de regra tem que ser decidido na seção 8 |
| Contrato: `reply`, `suggestions`, `notes` sem termos de saúde nem nome de medicamento | Nome de medicamento e de sintoma passam a aparecer nas respostas de busca |
| Testes T7, T8 e `test_privacy` (bloqueio e ausência de termos de saúde) | Reescritos para o comportamento novo |

Continua valendo: `persona.json` (o que a Renata **usa**) fica no aparelho e o motor não lê. Buscar "dor de cabeça" é uma frase que a pessoa digitou, não o histórico dela.

## 3. Catálogo (`catalog/`)

- Novo gerador de medicamentos (ex.: `catalog/medicines.py`), determinístico como os outros, rodando dentro de `generate_catalog.py`.
- **≥ 6 produtos por área**, com princípios ativos e apresentações reais e comuns no Brasil (ex.: dipirona 500 mg, 10 comprimidos). Marcas fictícias, como no resto do catálogo (D-11), salvo resposta diferente na seção 8.
- Campos novos ou reaproveitados em cada medicamento: princípio ativo, concentração, forma, quantidade, classe (analgésico, antiespasmódico...), áreas/sintomas que atende, exigência de receita, advertências da embalagem. Preço e estoque no `inventory.json`, estoque por loja no `store_stock.json`.
- Áreas propostas (confirmar na seção 8): dor de cabeça e febre; dor no corpo; dor muscular e contusão; dor de barriga e cólica; azia e má digestão; gripe e resfriado; tosse; dor de garganta; nariz entupido; alergia; diarreia; prisão de ventre; enjoo; cólica menstrual.
- Itens de reposição da Renata (tensivalol, lipostanol) continuam como estão.
- `validate_catalog.py` ganha checagens: ≥ 6 por área; princípio ativo e concentração preenchidos; preço e estoque positivos; nenhum medicamento sem área.

## 4. GraphRAG (`graphrag/`), treinado de verdade

- **Ontologia**: `domain = medicamento` deixa de exigir `rx` + `equivalence`. *Como ficou:* em vez de criar nós novos (`active`, `symptom`), princípio ativo virou **ingrediente** (família "princípio ativo") e sintoma virou **preocupação**; usam as arestas `CONTAINS` e `ADDRESSES`, que já existiam. Assim grafo, vetores, escopo e compositor tratam medicamento pelo mesmo caminho dos outros produtos, sem tipo novo na ontologia. As etapas de kit são papéis: `analgesico_dipirona`, `analgesico_paracetamol`, `antiinflamatorio`, `relaxante_muscular`, `dor_topico`, `antiespasmodico`, `antigases`, `antiacido`, `protetor_gastrico`, `antigripal`, `descongestionante_nasal`, `imunidade`, `expectorante`, `antitussigeno`, `pastilha_garganta`, `spray_garganta`, `antialergico`, `antidiarreico`, `probiotico`, `reidratacao`, `laxante`, `fibra`, `antiemetico`.
- **Objetivos** em `goals.json` por área (ex.: `dor_de_cabeca`: etapas obrigatórias e opcionais, sinônimos).
- **Léxico e conceitos** (`lexicon.py`, `concepts.py`, `scope.py`): o jeito de falar ("dor de cabeça", "enxaqueca", "dor de barriga", "intestino preso") aponta para a queixa; princípio ativo e **nome popular** também ("dorflex" → orfenadrina, "buscopan" → escopolamina). Os nomes populares só servem para entender a busca: nenhuma marca real aparece em produto. A prateleira de cada queixa é gerada do catálogo (`ScopeResolver.health_concepts`): produto novo de uma área já entra sem editar conceito. Remédio que não existe (diabetes, antibiótico, anticoncepcional, colírio...) é um conceito `absent` com resposta fixa.
- **Ato de fala** (`nlu_corpus.py`): frases de busca de medicamento entram no treino do Naive Bayes, com frases de teste separadas.
- **Segurança** (`safety.py`): sai o bloqueio por medicamento e por sintoma. Se nada no catálogo atende ao pedido, a resposta é só "Não está no banco de dados ainda." Sem farmacêutico, sem médico.
- **Compositor**: medicamento passa a entrar em kits. Regras de composição: ver pergunta 3 da seção 8. *(Desde 23/10, #40: remédio só na busca, nunca em kit.)*
- **Vetores**: medicamentos entram no corpus do PPMI+SVD (hoje são pulados em `embed.py`).
- **Treino**: `python3 -m graphrag.train` e `python3 graphrag/eval/calibrate.py` gerando artefatos novos; contagens de nós e arestas registradas no doc 08.
- **Avaliação**: conjunto de busca de medicamentos em `graphrag/eval/search_set.py` (frases de ajuste e frases cegas, separadas); medir antes e depois.

## 5. App (`app/`)

- Busca de medicamento abre a tela de resultados como qualquer busca: kits em cima, lista embaixo. (Desde 23/10, #40: só a lista, sem kit.)
- A categoria "Medicamentos e saúde" passa a abrir, com subcategorias por área.
- A página do produto de medicamento mostra princípio ativo, concentração, quantidade, selo "exige receita" quando for o caso e as advertências da embalagem.
- Nenhuma tela mostra "procure um farmacêutico/médico". A tela de bloqueio de saúde sai do fluxo de busca.
- Interface mais fiel ao app e fluxo consolidado: depende da pergunta 4 da seção 8. Sem referência visual nova, a base é o doc 13.
- `tools/export_app_mock.py` exporta os medicamentos; o simulador de reserva também os entende (sem ele, o app quebraria com o servidor fora do ar).

## 6. O que não se pode fazer

- Resolver no app algo que deveria estar no motor (seria mockup).
- Inventar princípio ativo, concentração ou apresentação que não exista no Brasil.
- Recomendar dose ou posologia na resposta.
- Mexer nos dados de saúde da persona ou fazer o motor lê-los.

## 7. Checklist de aceite (preencher no fim)

| # | Critério | Prova | Estado |
| --- | --- | --- | --- |
| A1 | Branch `feat/medicamentos-e-ui` com todo o trabalho | `git status` | feito (sem commit; aguarda aprovação) |
| A2 | ≥ 6 medicamentos por área aprovada | `validate_catalog.py` ("pelo menos 6 por área") | feito: 79 medicamentos em 12 áreas, de 6 a 8 cada; 76/76 checagens |
| A3 | "remédio de dor de cabeça" devolve dipirona e paracetamol (desde 23/10, #40: avulsos, sem kit) | `test_T7_dor_de_cabeca_traz_remedios_avulsos_sem_kit` | feito |
| A4 | "dor no corpo", "dor muscular", "dor de barriga" devolvem os itens da área (desde 23/10, #40: sem kit) | `test_T8_areas_de_saude_listam_sem_kit` (12 áreas) | feito |
| A5 | Nenhuma resposta contém "farmacêutico" ou "médico" como encaminhamento | invariante M2 em toda resposta testada; checagem de texto no catálogo; teste do app (T8) | feito; tela "Falar com um farmacêutico" removida |
| A6 | Pedido sem remédio no catálogo responde "Não está no banco de dados ainda." | `test_sem_remedio_no_catalogo_diz_so_que_nao_esta`; regra `missing` da avaliação (8/8) | feito; visto no app |
| A7 | Medicamentos no grafo, nos vetores e no classificador; artefatos retreinados | seção 9 | feito: grafo 599 nós / 3261 arestas; vocabulário 1361; ato de fala 63/65 |
| A8 | App mostra os kits e os produtos de medicamento vindos do motor real | percurso no Chromium (375 px) com o servidor em :8787 | feito: busca → kits → kit → troca; Categorias → Medicamentos; produto com receita; "remédio para diabetes" *(Desde 23/10, #40: remédio só na busca, nunca em kit.)* |
| A9 | Interface e navegação revistas conforme a seção 8 | percurso no navegador | feito em parte; ver seção 10 |
| A10 | Todos os testes passam (catálogo, GraphRAG, app) | comandos do doc 08 | feito: 76/76 · 95/95 · 46/46; build ok |
| A11 | Docs 07, 09, 14 e o contrato atualizados com o que mudou | diff | feito (e 05, 06, 08, READMEs) |

## 8. Perguntas para a Julia (não inventar)

### Respostas (21/10)

| # | Pergunta | Resposta | Como fica |
| --- | --- | --- | --- |
| 1 | Medicamentos com receita | **Todos, igual** | Com e sem receita entram na busca e nos kits do mesmo jeito. A tarja aparece só como dado do produto (selo "exige receita"), sem mensagem. Antibióticos e controlados (retenção de receita) não estão entre os "mais comprados" das áreas pedidas e não foram criados nesta rodada; se quiser, é só pedir *(Desde 23/10, #40: remédio só na busca, nunca em kit.)* |
| 2 | Frase "Se persistirem os sintomas..." | **Some de vez** | Nenhuma tela mostra a frase |
| 3 | Regra dos kits | **Aceita** | Nunca o mesmo princípio ativo duas vezes no kit; nunca dois anti-inflamatórios juntos. As duas regras entram como interações `evitar` (mesma regra K4 dos cosméticos) |
| 4 | Referência visual | **Doc 13 + site público** | Sem prints novos |

Perguntas feitas:

1. **Medicamentos com receita** (tarja vermelha, antibiótico, controlados): entram na busca e nos kits como os isentos de prescrição, ou só os isentos? *(Desde 23/10, #40: remédio só na busca, nunca em kit.)*
2. **Frase legal**: a propaganda de medicamento isento de prescrição no Brasil (RDC 96/2008) costuma levar "SE PERSISTIREM OS SINTOMAS, O MÉDICO DEVERÁ SER CONSULTADO". Ela some de vez, ou fica só como letra pequena na página do produto (fora da busca e dos kits)?
3. **Regra dos kits de medicamento** (revogada em 23/10 pelo #40: não há kit de remédio; as regras de princípio ativo seguem no checador M1): no exemplo, dipirona + paracetamol no mesmo kit. Regra proposta: cada kit traz princípios ativos diferentes para o mesmo sintoma (nunca o mesmo ativo duas vezes) e nunca dois anti-inflamatórios do mesmo grupo juntos (ex.: ibuprofeno + naproxeno). Aceita?
4. **Referência visual**: os prints do app não estão no repositório (doc 13, D-19). Dá para mandar prints de novo (sem dados pessoais) das telas que devem ficar mais fiéis, ou sigo só com o doc 13 e o site público?

## 9. Medições (21/10)

| O quê | Antes (commit 012129c) | Depois |
| --- | --- | --- |
| Testes do GraphRAG | 90/90 | 95/95 (14 reescritos para o comportamento novo, 5 novos) |
| Testes do app | 46/46 | 46/46 (T7, T7b, T8 e 4 da persona reescritos) |
| Checagens do catálogo | 69/69 | 76/76 |
| Grafo | 329 nós, 2197 arestas | 599 nós, 3261 arestas |
| Vocabulário dos vetores | 488 | 1361 |
| Ato de fala, frases fora do treino | 59/60 | 63/65 (os 2 erros são "gostei desse" e "melhor deixar", que já erravam) |
| Ranking (nDCG@10 no teste, 14 frases) | 1,0 | 1,0; pesos bm25 0,00 · emb 0,57 · grafo 0,43 |
| Listas limpas, conjuntos antigos (treino/teste/cego 1–4) | — | 47/47 · 32/32 · 33/33 · 27/28 · 27/27 · 30/30 |
| Listas limpas, medicamentos (ajuste) | — | 12/12; "não está no banco" 4/4 |
| Listas limpas, medicamentos (**cego**, escrito antes de medir) | — | 17/20; "não está no banco" 4/4 |
| Latência busca nova (p95, em processo) | 118 ms | 187 ms |

Falhas do conjunto cego de medicamentos, deixadas sem ajuste: "minha cabeça está latejando" e "travei as costas" (não encontra nada) e "acordei com o corpo todo dolorido" (mistura itens de banho e corpo).

As dependências do GraphRAG foram instaladas num ambiente virtual isolado (`python3 -m venv --without-pip` + get-pip oficial), sem mexer no Python do sistema.

## 10. Interface e navegação: o que mudou

- **Busca**: a barra diz "Busque remédio, sintoma ou produto"; exemplos com remédio. Busca de remédio abre a mesma tela de resultados (kits em cima, lista embaixo; desde 23/10, #40, só a lista).
- **Resultados**: o painel "Quanto quer gastar" deixou de abrir sozinho e empurrar os kits para baixo; agora é uma folha que abre pelo chip de valor. O chip e a pergunta de tipo de pele só aparecem em objetivo de pele. Os filtros ganharam "Só sem receita", e "Tipo de pele" só aparece quando a lista tem dermocosmético.
- **Cartão do kit**: remédio mostra o nome com a dose ("Dipirona 500 mg — 10 comprimidos"), não o tipo. *(Desde 23/10, #40: remédio só na busca, nunca em kit.)*
- **Kit de remédio**: sem a opção de assinatura (assinatura é para rotina, não para sintoma). *(Desde 23/10, #40: remédio só na busca, nunca em kit.)*
- **Produto**: princípio ativo, selo "Venda sob prescrição" ou "Sem receita", seções do site adaptadas para remédio; selo "Exige receita" no cartão da lista.
- **Categorias**: "Medicamentos e saúde", "Vida saudável" e "Higiene pessoal" abrem; Medicamentos tem as 12 áreas e a reposição.
- **Removido**: tela de bloqueio de saúde, botão e tela "Falar com um farmacêutico", confirmação de troca "com o farmacêutico" na reposição, todo texto de encaminhamento.
- **Não feito**: comparação visual lado a lado com o app real (sem prints novos, pergunta 4); fotos reais continuam pendentes.

## 11. Tabela para conferência (tarja e apresentação)

A tarja segue o que é usual no varejo, a partir de conhecimento geral, **sem consulta à base da Anvisa**. Os itens a conferir com mais atenção são os antialérgicos com receita (desloratadina, cetirizina, fexofenadina, dexclorfeniramina), racecadotrila e levodropropizina. Onde não havia certeza da concentração, ela ficou fora do nome (antiácido em suspensão, alginato, macrogol, leite de magnésia, guaco).

**Dor de cabeça e febre** (8)

| Id | Produto | Princípio ativo | Tarja | Preço |
| --- | --- | --- | --- | --- |
| p139 | Dipirona 500 mg — 10 comprimidos | Dipirona monoidratada | sem receita | R$ 7,90 |
| p140 | Dipirona 1 g (genérico) — 10 comprimidos | Dipirona monoidratada | sem receita | R$ 11,90 |
| p141 | Dipirona Gotas 500 mg/mL — 20 mL | Dipirona monoidratada | sem receita | R$ 9,90 |
| p142 | Paracetamol 750 mg — 20 comprimidos | Paracetamol | sem receita | R$ 12,90 |
| p143 | Paracetamol 500 mg + Cafeína 65 mg — 20 comprimidos | Paracetamol + Cafeína anidra | sem receita | R$ 19,90 |
| p144 | Paracetamol Gotas 200 mg/mL — 15 mL | Paracetamol | sem receita | R$ 10,90 |
| p145 | Dipirona 300 mg + Isometepteno 30 mg + Cafeína 30 mg — 20 comprimidos | Dipirona monoidratada + Mucato de isometepteno + Cafeína anidra | sem receita | R$ 24,90 |
| p146 | Ácido Acetilsalicílico 500 mg (genérico) — 20 comprimidos | Ácido acetilsalicílico | sem receita | R$ 8,90 |

**Dor no corpo** (7)

| Id | Produto | Princípio ativo | Tarja | Preço |
| --- | --- | --- | --- | --- |
| p147 | Ibuprofeno 400 mg — 10 cápsulas | Ibuprofeno | sem receita | R$ 14,90 |
| p148 | Ibuprofeno 600 mg (genérico) — 20 comprimidos | Ibuprofeno | vermelha (receita) | R$ 18,90 |
| p149 | Ibuprofeno Gotas 50 mg/mL — 30 mL | Ibuprofeno | sem receita | R$ 16,90 |
| p150 | Naproxeno Sódico 275 mg — 10 comprimidos | Naproxeno sódico | sem receita | R$ 17,90 |
| p151 | Naproxeno Sódico 550 mg (genérico) — 10 comprimidos | Naproxeno sódico | vermelha (receita) | R$ 22,90 |
| p152 | Diclofenaco Potássico 50 mg — 20 comprimidos | Diclofenaco potássico | vermelha (receita) | R$ 21,90 |
| p153 | Nimesulida 100 mg — 12 comprimidos | Nimesulida | vermelha (receita) | R$ 12,90 |

**Dor muscular** (7)

| Id | Produto | Princípio ativo | Tarja | Preço |
| --- | --- | --- | --- | --- |
| p154 | Dipirona 300 mg + Orfenadrina 35 mg + Cafeína 50 mg — 10 comprimidos | Dipirona monoidratada + Citrato de orfenadrina + Cafeína anidra | sem receita | R$ 9,90 |
| p155 | Dipirona 300 mg + Orfenadrina 35 mg + Cafeína 50 mg — 36 comprimidos | Dipirona monoidratada + Citrato de orfenadrina + Cafeína anidra | sem receita | R$ 27,90 |
| p156 | Ciclobenzaprina 5 mg (genérico) — 30 comprimidos | Cloridrato de ciclobenzaprina | vermelha (receita) | R$ 24,90 |
| p157 | Ciclobenzaprina 10 mg — 30 comprimidos | Cloridrato de ciclobenzaprina | vermelha (receita) | R$ 32,90 |
| p158 | Diclofenaco Sódico 50 mg + Carisoprodol 125 mg + Paracetamol 300 mg + Cafeína 30 mg — 15 comprimidos | Diclofenaco sódico + Carisoprodol + Paracetamol + Cafeína anidra | vermelha (receita) | R$ 29,90 |
| p159 | Diclofenaco Dietilamônio Gel 11,6 mg/g — 60 g | Diclofenaco dietilamônio | sem receita | R$ 26,90 |
| p160 | Pomada de Salicilato de Metila, Mentol e Cânfora — 30 g | Salicilato de metila + Mentol + Cânfora | sem receita | R$ 14,90 |

**Dor de barriga e cólica** (6)

| Id | Produto | Princípio ativo | Tarja | Preço |
| --- | --- | --- | --- | --- |
| p161 | Butilbrometo de Escopolamina 10 mg — 20 drágeas | Butilbrometo de escopolamina | sem receita | R$ 16,90 |
| p162 | Butilbrometo de Escopolamina Gotas 10 mg/mL — 20 mL | Butilbrometo de escopolamina | sem receita | R$ 18,90 |
| p163 | Escopolamina 10 mg + Dipirona 250 mg — 20 comprimidos | Butilbrometo de escopolamina + Dipirona monoidratada | sem receita | R$ 22,90 |
| p164 | Simeticona 40 mg (genérico) — 20 comprimidos | Simeticona | sem receita | R$ 8,90 |
| p165 | Simeticona Gotas 75 mg/mL — 15 mL | Simeticona | sem receita | R$ 12,90 |
| p166 | Simeticona 125 mg — 10 cápsulas | Simeticona | sem receita | R$ 14,90 |

**Azia e má digestão** (6)

| Id | Produto | Princípio ativo | Tarja | Preço |
| --- | --- | --- | --- | --- |
| p167 | Hidróxido de Alumínio + Hidróxido de Magnésio + Simeticona — suspensão 240 mL | Hidróxido de alumínio + Hidróxido de magnésio + Simeticona | sem receita | R$ 24,90 |
| p168 | Sal de Frutas (Bicarbonato de Sódio + Carbonato de Sódio + Ácido Cítrico) — 2 envelopes de 5 g | Bicarbonato de sódio + Carbonato de sódio + Ácido cítrico | sem receita | R$ 4,90 |
| p169 | Alginato de Sódio + Bicarbonato de Sódio — 12 sachês de suspensão | Alginato de sódio + Bicarbonato de sódio | sem receita | R$ 29,90 |
| p170 | Omeprazol 20 mg (genérico) — 28 cápsulas | Omeprazol | vermelha (receita) | R$ 15,90 |
| p171 | Pantoprazol 40 mg — 28 comprimidos | Pantoprazol | vermelha (receita) | R$ 39,90 |
| p172 | Esomeprazol 40 mg — 28 comprimidos | Esomeprazol | vermelha (receita) | R$ 54,90 |

**Gripe e resfriado** (6)

| Id | Produto | Princípio ativo | Tarja | Preço |
| --- | --- | --- | --- | --- |
| p173 | Antigripal Paracetamol 400 mg + Fenilefrina 4 mg + Clorfeniramina 4 mg — 20 comprimidos | Paracetamol + Cloridrato de fenilefrina + Maleato de clorfeniramina | sem receita | R$ 17,90 |
| p174 | Antigripal Dipirona 500 mg + Clorfeniramina 2 mg + Cafeína 30 mg — 20 cápsulas | Dipirona monoidratada + Maleato de clorfeniramina + Cafeína anidra | sem receita | R$ 15,90 |
| p175 | Vitamina C 1 g Efervescente — 10 comprimidos | Ácido ascórbico (vitamina C) | sem receita | R$ 13,90 |
| p176 | Soro Fisiológico Nasal 0,9% — 30 mL | Cloreto de sódio 0,9% | sem receita | R$ 6,90 |
| p177 | Nafazolina 0,5 mg/mL Solução Nasal — 30 mL | Cloridrato de nafazolina | sem receita | R$ 7,90 |
| p178 | Oximetazolina 0,5 mg/mL Spray Nasal — 20 mL | Cloridrato de oximetazolina | sem receita | R$ 24,90 |

**Tosse com catarro** (7)

| Id | Produto | Princípio ativo | Tarja | Preço |
| --- | --- | --- | --- | --- |
| p179 | Ambroxol Xarope Adulto 30 mg/5 mL — 120 mL | Cloridrato de ambroxol | sem receita | R$ 16,90 |
| p180 | Acetilcisteína 600 mg — 16 envelopes | Acetilcisteína | sem receita | R$ 44,90 |
| p181 | Bromexina Xarope Adulto 8 mg/5 mL — 120 mL | Cloridrato de bromexina | sem receita | R$ 18,90 |
| p182 | Carbocisteína Xarope Adulto 50 mg/mL (genérico) — 100 mL | Carbocisteína | sem receita | R$ 14,90 |
| p183 | Xarope de Guaco — 120 mL | Guaco (Mikania glomerata) | sem receita | R$ 12,90 |
| p184 | Dropropizina Xarope Adulto 3 mg/mL — 120 mL | Dropropizina | sem receita | R$ 17,90 |
| p185 | Levodropropizina Xarope 6 mg/mL — 120 mL | Levodropropizina | vermelha (receita) | R$ 38,90 |

**Dor de garganta** (6)

| Id | Produto | Princípio ativo | Tarja | Preço |
| --- | --- | --- | --- | --- |
| p186 | Pastilhas Amilmetacresol + Álcool Diclorobenzílico Mel e Limão — 8 pastilhas | Amilmetacresol + álcool diclorobenzílico | sem receita | R$ 13,90 |
| p187 | Pastilhas Amilmetacresol + Álcool Diclorobenzílico Menta — 8 pastilhas | Amilmetacresol + álcool diclorobenzílico | sem receita | R$ 12,90 |
| p188 | Flurbiprofeno 8,75 mg — 16 pastilhas | Flurbiprofeno | sem receita | R$ 29,90 |
| p189 | Benzidamina 3 mg — 12 pastilhas | Cloridrato de benzidamina | sem receita | R$ 19,90 |
| p190 | Benzidamina Spray 1,5 mg/mL — 30 mL | Cloridrato de benzidamina | sem receita | R$ 24,90 |
| p191 | Benzidamina Colutório 1,5 mg/mL (genérico) — 250 mL | Cloridrato de benzidamina | sem receita | R$ 21,90 |

**Alergia e rinite** (6)

| Id | Produto | Princípio ativo | Tarja | Preço |
| --- | --- | --- | --- | --- |
| p192 | Loratadina 10 mg — 12 comprimidos | Loratadina | sem receita | R$ 9,90 |
| p193 | Loratadina Xarope 1 mg/mL — 100 mL | Loratadina | sem receita | R$ 14,90 |
| p194 | Desloratadina 5 mg — 10 comprimidos | Desloratadina | vermelha (receita) | R$ 27,90 |
| p195 | Cetirizina 10 mg (genérico) — 10 comprimidos | Dicloridrato de cetirizina | vermelha (receita) | R$ 12,90 |
| p196 | Fexofenadina 180 mg — 10 comprimidos | Cloridrato de fexofenadina | vermelha (receita) | R$ 34,90 |
| p197 | Dexclorfeniramina 2 mg — 20 comprimidos | Maleato de dexclorfeniramina | vermelha (receita) | R$ 11,90 |

**Diarreia** (7)

| Id | Produto | Princípio ativo | Tarja | Preço |
| --- | --- | --- | --- | --- |
| p198 | Loperamida 2 mg — 12 comprimidos | Cloridrato de loperamida | sem receita | R$ 11,90 |
| p199 | Racecadotrila 100 mg — 9 cápsulas | Racecadotrila | vermelha (receita) | R$ 39,90 |
| p200 | Nitazoxanida 500 mg — 6 comprimidos | Nitazoxanida | vermelha (receita) | R$ 42,90 |
| p201 | Saccharomyces boulardii 200 mg — 12 cápsulas | Saccharomyces boulardii | sem receita | R$ 34,90 |
| p202 | Bacillus clausii 2 bilhões — 5 flaconetes de 5 mL | Bacillus clausii | sem receita | R$ 39,90 |
| p203 | Sais para Reidratação Oral — envelope 27,9 g | Sais para reidratação oral | sem receita | R$ 3,90 |
| p204 | Soro de Reidratação Oral Pronto Sabor Coco — 500 mL | Sais para reidratação oral | sem receita | R$ 9,90 |

**Prisão de ventre** (7)

| Id | Produto | Princípio ativo | Tarja | Preço |
| --- | --- | --- | --- | --- |
| p205 | Bisacodil 5 mg — 20 drágeas | Bisacodil | sem receita | R$ 12,90 |
| p206 | Picossulfato de Sódio Gotas 7,5 mg/mL — 20 mL | Picossulfato de sódio | sem receita | R$ 19,90 |
| p207 | Lactulose Xarope 667 mg/mL (genérico) — 120 mL | Lactulose | sem receita | R$ 21,90 |
| p208 | Leite de Magnésia (Hidróxido de Magnésio) — suspensão 120 mL | Hidróxido de magnésio | sem receita | R$ 13,90 |
| p209 | Macrogol 3350 Pó para Solução Oral — 10 sachês | Macrogol 3350 | sem receita | R$ 34,90 |
| p210 | Psyllium (Plantago ovata) Pó — 10 sachês | Psyllium (Plantago ovata) | sem receita | R$ 29,90 |
| p211 | Psyllium (Plantago ovata) Pó — 30 sachês | Psyllium (Plantago ovata) | sem receita | R$ 69,90 |

**Enjoo e náusea** (6)

| Id | Produto | Princípio ativo | Tarja | Preço |
| --- | --- | --- | --- | --- |
| p212 | Dimenidrinato 100 mg — 10 comprimidos | Dimenidrinato | sem receita | R$ 14,90 |
| p213 | Dimenidrinato 50 mg + Piridoxina 10 mg — 10 comprimidos | Dimenidrinato + Piridoxina (vitamina B6) | sem receita | R$ 16,90 |
| p214 | Dimenidrinato Gotas 25 mg/mL — 20 mL | Dimenidrinato | sem receita | R$ 15,90 |
| p215 | Ondansetrona 4 mg (genérico) — 10 comprimidos orodispersíveis | Ondansetrona | vermelha (receita) | R$ 24,90 |
| p216 | Metoclopramida 10 mg — 20 comprimidos | Cloridrato de metoclopramida | vermelha (receita) | R$ 8,90 |
| p217 | Domperidona 10 mg — 30 comprimidos | Domperidona | vermelha (receita) | R$ 19,90 |

## 12. Desconto dos kits (#30, 23/10)

- Todo kit com 2 itens ou mais tem desconto progressivo: 10% (2 itens), 12% (3), 15% (4 ou 5). O kit sempre sai mais barato que comprar os itens avulsos, sem exagero.
- Vale também para os kits de medicamento (**revogado em 23/10 pelo #40: não há mais kit de remédio**). Decisão da Julia na época: o exemplo pedido foi o kit de dor de cabeça. Ressalva registrada: em produção, promoção de medicamento segue a RDC 96/2008 da Anvisa e precisa de revisão jurídica antes de ir ao ar. No protótipo, o desconto aparece como preço do kit, sem frase de apelo ao consumo.
- O cashback é calculado sobre o que a pessoa paga: o cashback dos itens reduzido na mesma proporção do desconto.
- Arredondamento: meio centavo para cima, em aritmética inteira, igual no motor e no app.

## 13. Faixas dos kits (#31, 23/10)

- **Completo** substitui o Alternativo. A ordem de preço é sempre Econômico < Essencial < Completo (invariante M4, no motor e no app).
- O Completo tem mais itens que o Essencial (nem que seja 1), ou a mesma quantidade com itens de maior relevância, ou a mesma cesta em versão superior (mesmo tipo, preço maior e dose maior lida do nome, ou FPS estritamente maior; sabor, embalagem maior ou marca de referência não contam). O texto do kit diz qual dos três casos é, comparando com o Essencial. Exemplo, dor de cabeça: Econômico R$ 16,92, Essencial R$ 18,72 (dipirona 500 mg + paracetamol 750 mg), Completo R$ 22,32 (dipirona 1 g + paracetamol 750 mg).
- Varredura de 110 frases: as 30 respostas com kit têm os 3 kits; Completos: 6 com itens a mais, 3 em versão superior (todos dipirona 500 mg → 1 g), 21 com maior relevância. Com orçamento apertado (dor de cabeça até R$ 19 ou R$ 20) saem Econômico e Essencial.
- Limite conhecido: o simulador do app (reserva quando o motor está fora) usa a mesma regra de faixas, mas não tem a mesma NLU e relevância do motor; em cerca de 7 de 24 frases ele escolhe kits diferentes (já acontecia antes do #31).
- Limite conhecido: o catálogo não tem nota de cliente. "Mais bem avaliado" é a relevância do motor (preocupações, tipo de pele, recuperação BM25 + vetores + grafo). Com notas reais, elas entram nesse critério.
- Na conversa, "o completo", "o kit completo" e "o terceiro" escolhem esta faixa; "mais completo" continua sendo pedir para gastar mais.
- **Nota de 23/10 (#40):** os exemplos de dor de cabeça e gripe desta seção são histórico; remédio não entra mais em kit (seção 15).

## 14. RAG com DeepSeek (#33 a #38, 23/10)

- **Quando entra:** só quando o grafo não entende. O grafo sempre roda primeiro; se achou, a resposta dele vale e a DeepSeek nem é chamada. Sinais: busca sem nada reconhecido ("Não encontrei esse item"), só a palavra "remédio" sem o quê (lista genérica de medicamentos) e, na conversa, ajuste que o grafo não leu (negação, pergunta sem produto ou refinamento que não mudou nada). Item que o grafo reconhece e o catálogo não tem continua com "Não está no banco de dados ainda." sem chamar a DeepSeek.
- **O que ela faz:** traduz a frase para ids do catálogo (prompt em `graphrag/llm.py`, o mesmo do documento de auditoria). Id que não existe é descartado; com o que sobra montamos uma frase só com rótulos do catálogo e o grafo busca de novo. A tela não mostra "Entendi como": a pessoa vê direto o resultado; a frase entendida vai só para o registro do servidor.
- **Medido** (`graphrag/eval/report_rag.md`): 28 frases que o grafo não entendia (buscas e ajustes); grafo sozinho acerta 1, grafo + DeepSeek acerta 27 (erra "nada que arda", em que a DeepSeek devolveu tudo vazio), cerca de 1,4 s por chamada. No conjunto de busca do motor (101 frases) a DeepSeek é chamada 0 vezes.
- **Limites:** o grafo às vezes entende errado em vez de não entender (ex.: "quero ficar com a pele de bebê" vira "linha infantil"; "tô fanho e entupido" vira banho e corpo); nesses casos a DeepSeek não entra, pela regra de não invalidar o grafo. Conjunto de avaliação pequeno (28 frases).

## 15. Remédio nunca entra em kit (#40, 23/10)

- **Pedido da Julia:** sugerir combinação de medicamentos ("estou com dor de cabeça" → dipirona + paracetamol) é um problema com a Anvisa. Remédio aparece só avulso, na lista; kits continuam para pele, suplementos (vitamina C, colágeno...) e higiene. Revoga o item 4 da seção 1, a regra dos kits de medicamento (seção 8, resposta 3) e o desconto em kit de remédio (seção 12).
- **Regra K13** (motor e simulador): nenhum produto do domínio `medicamento` entra em kit nem na troca de item. Objetivo em que alguma etapa obrigatória só tem remédio (os 13 objetivos de saúde) não monta kit: a resposta é a lista dos itens daquela queixa, sem texto de kit e sem mandar procurar médico ou farmacêutico. Invariante nova **M5** no motor e no app.
- **O que conta como remédio (decisão da Julia):** Vitamina C 1 g efervescente e Psyllium passaram para `suplemento` (ganharam o aviso dos suplementos). Decisão da Julia: as etapas deles, "imunidade" e "fibra", são opcionais no kit de suplementos, ao lado de "vitaminas". Para caber no limite de 5 itens (K9), o compositor passou a testar toda combinação de opcionais que cabe, das maiores para as menores (antes: todas, só a primeira ou nenhuma). Ex.: "kit de suplementos" leva a vitamina C efervescente no Essencial e o psyllium no Completo. e continuam aparecendo na busca do sintoma (gripe, prisão de ventre). Soro fisiológico nasal, sais e soro de reidratação continuam remédio.
- **RAG:** a DeepSeek não reativa kit de remédio; a regra fica no compositor, depois dela.
- Limite: a regra de dose maior do #31 ("versão superior", ex.: dipirona 500 mg → 1 g) continua no código, mas hoje não tem exemplo vivo, porque só remédio tinha esse caso.

## 16. Críticos do teste de usabilidade e RAG melhorado (#41, #42, #60 a #62, 23/10)

- **#41 (RDC 96/2008):** remédio de prescrição não tem preço de tabela maior que o preço (nunca "de/por" nem "Super oferta"), no catálogo, no motor, na ingestão e nos dados do app, e sai da vitrine "Mais vendidos em Medicamentos". A Reposição mostra o preço realmente cobrado. Remédios sem receita e o desconto/frete da reposição automática seguem em discussão no #45.
- **#42 (LGPD):** Privacidade e dados informa o envio da frase à DeepSeek e tem a chave "Entender frases difíceis com um serviço externo" (guardada no aparelho; desligada, nada sai). Os textos admitem que tirar dados pessoais não é perfeito. Decisão pendente da Julia: em produção, o consentimento para dado de saúde deve ser ativo?
- **#61 (conferência):** a DeepSeek também confere quando o grafo respondeu mas viu palavra desconhecida; só troca a resposta se explicar a palavra com algo que o grafo não cobria, nunca com palavra negada, e nunca vira lista de remédios sem pedido de dor, remédio ou sintoma.
- **#62:** `canon_state` reescreve "parte do corpo + até 2 palavras + estado" (não se há "não", "sem" ou "nem" no meio) para apelidos já conhecidos, sem acrescentar palavras soltas ao vocabulário. O corretor só aceita correção de 2 erros se a 1ª letra bate.
- **Limites conhecidos:** "tá tapado meu nariz" (estado antes da parte) e 3ª pessoa com 3+ palavras não casam; duas queixas na mesma frase e negação coordenada ficam sem tratamento; "pele melada depois da praia" vai para oleosidade (antes, proteção solar), o que é discutível.

## 17. Achados curtos do teste de usabilidade (#47, #49, #55 a #59, 24/10)

- **#47 (RDC 243/2018):** suplemento não mostra queixa de saúde na descrição nem na página (BENEFÍCIOS vira "Composição"; PARA QUE SERVE não fala de tipo de pele). A busca por sintoma continua achando esses suplementos pelos conceitos do catálogo, que não são exibidos.
- **#49:** o atalho da página do produto só promete kit onde o motor monta kit (suplementos, higiene, pele; desmaquilagem, textura e olheiras caem em "kit de skin care"); remédio mostra "Veja outros itens avulsos" e remédio de reposição não mostra atalho.
- **#55 a #59:** aviso dura 10 s (8 s sem ação), tem botão Fechar e pausa com mouse ou foco; botões repetidos levam o nome do item; aba Locker com nome acessível; três textos atualizados; "1 item" no singular; "Lojas próximas"; ingredientes sem perder sigla ("ômega 3 (EPA e DHA)", "vitamina E") no motor e no simulador.
- **Limites:** os testes do app conferem o texto do código-fonte, não renderizam; "psyllium (plantago ovata)" sai com o gênero em minúscula; a lista de conceitos de pele sem kit está fixa no app; o #54 não foi reproduzido.

## 18. Achados altos do teste de usabilidade (#43, #44, #45, #48, 24/10)

- **#48:** cesta, receitas anexadas (simuladas), pedidos, carteira pendente, loja e modo de entrega ficam no aparelho (`localStorage`, chave `pm.session.v1`) e voltam ao recarregar; produto que saiu do catálogo é descartado e a quantidade de remédio com receita volta limitada. Privacidade e dados ganhou "Apagar a cesta e os pedidos deste aparelho". Conversa, favoritos e buscas recentes continuam só da sessão.
- **#45 (RDC 96/2008):** nenhum remédio, com ou sem receita, tem preço riscado nem "Super oferta" (catálogo, motor e app); remédio não conta para o frete grátis (cesta, entrega e pagamento) e a Reposição automática não promete mais frete grátis nem desconto (o de 5% segue como premissa que não vale). O desconto progressivo dos kits não se aplica a remédio, que não entra em kit.
- **#44:** na busca por sintoma, remédio de venda livre vem antes dos de receita; quem digita o nome do remédio de receita o vê primeiro. Efeito medido: `AMPLO teste` do grafo foi de 13 para 12 de 15 ("treino pesado e fico todo dolorido" perdeu os de receita que puxavam a lista para dor muscular) e a precisão do conjunto `medcego` de 0,879 para 0,869.
- **#43 (RDC 44/2009):** a receita simulada vale por 2 caixas por item (o "+" para e avisa; a cesta guardada volta com o limite); o pedido com remédio de receita nasce "Aguardando avaliação da receita pelo farmacêutico (simulado)" e a tela de receitas e a de pagamento explicam isso; remédio com tarja diferente de `receita_simples` (controlado) é recusado na cesta, embora o catálogo não tenha nenhum.
- **Decisões que são da Julia:** o limite de 2 caixas é premissa; "se o farmacêutico não aprovar, os itens com receita saem do pedido" é só texto, não há fluxo de aprovação; se kits com desconto devem continuar existindo para itens de higiene com remédio no mesmo pedido.

## 19. Risco de vida, sintoma vago e limite de uso (#63, #64, #65, 24/10)

- **#63 (exceção estreita à regra "nenhuma resposta manda procurar atendimento"):** frases de risco de vida ("quero me matar", "não quero mais viver"...) e sinais de alerta (dor no peito, falta de ar, sangue nas fezes ou na tosse, língua inchada, rigidez no pescoço, boca torta, "pior dor de cabeça da vida", criança que engoliu veneno...) recebem resposta fixa: CVV 188 e SAMU 192 no primeiro caso, SAMU 192 no segundo; sem lista de produtos, sem sugestões e sem nunca ir à DeepSeek. `graphrag/safety.py` (`urgency`) e `app/src/services/urgency.ts` têm as mesmas frases e os dois lados têm teste. Decisão da Julia a confirmar: o texto das mensagens e a lista de sinais; a regra erra para o lado da cautela ("falta de ar depois de correr" também dispara). Não substitui avaliação clínica. A lista NÃO é exaustiva: erros de digitação que o corretor não conserta ("qro morre", abreviações), crise dita sem as palavras previstas e sinais que só aparecem em fala anterior da conversa (o replay do histórico não checa) escapam; só a fala atual é checada. Dor no ombro ou braço esquerdo "irradiando" dispara, mas dor no ombro sozinha não (vai para dor muscular).
- **#65:** "pernas/pés inchados", varizes, retenção de líquido e formigamento viram "Não está no banco de dados ainda" (antes listavam antigases e antiespasmódicos); dor no joelho, coluna, ombro, perna e juntas vai para dor muscular; dor no estômago vai para azia.
- **#64:** a DeepSeek tem teto por pessoa (`RAG_PER_CLIENT_HOUR`, padrão 20 por hora) e por dia (`RAG_DAILY_CAP`, padrão 1500); o servidor identifica a pessoa por hash do IP (cabeçalho `x-real-ip`/`x-forwarded-for`, que quem chama fora da Vercel pode forjar para ganhar um cliente novo a cada pedido: o teto que sobra, nesse caso, é o do dia) e descarta qualquer `_client` que venha no corpo; passou do teto, a busca segue só com o grafo (`ragCalls.limite`); frase com mais de 500 caracteres é recusada. Limite honesto: o contador vive na memória de cada instância (na Vercel há várias e a partida a frio zera); o teto de verdade pede armazenamento compartilhado ou login.

## 20. Reposição, cartão de kit e texto do ajuste (#46, #50 a #54, 24/10)

- **#46:** o equivalente de remédio de receita na Reposição vem como sugestão "sujeita à confirmação do farmacêutico" (Lei 9.787/1999): o motor marca `needsPharmacistConfirmation`, a lista mostra só quem tem mesmo princípio ativo e mesma dose, e o cartão do item trocado repete o aviso. Não há fluxo de aprovação de verdade; o pedido já nasce "aguardando avaliação" (#43).
- **#50:** item de reposição que a loja escolhida não tem fica fora do total e do "Retirar na loja" até a pessoa escolher um equivalente em estoque; a barra diz o que ficou fora da conta.
- **#51:** o cartão do kit mostra o nome do produto de cada etapa (antes, o tipo), então o Essencial e o Completo deixam de parecer iguais.
- **#52:** a resposta de um ajuste no chat diz o que foi aplicado ("Apliquei: sem fragrância") e como cada kit andou ("Preços: Econômico de R$ 44,62 para R$ 105,34"), com a frase "Subiu porque os itens que atendem esse pedido custam mais" quando o aumento passa de 15%. "Tira tudo que tem cheiro" e "não quero ácido" no meio da conversa agora viram ajuste (antes, o primeiro era lido como pergunta sobre produto e o segundo como "não"). O simulador do app não tem esse texto.
- **#53:** "pele que vive melada" vai para oleosidade com a DeepSeek (resolvido pela conferência do #61); só o grafo ainda monta a rotina básica.
- **#54:** não reproduzi (o motor devolve a lista inteira, de 11 a 24 itens, em 60 combinações de objetivo, orçamento e loja); ficou um teste de guarda para a lista não encolher pelo orçamento.
- **Custo:** o classificador de atos de fala foi de 63 para 61 de 65 frases de teste ao longo do dia (exemplos de ajuste de preço e de cheiro).
