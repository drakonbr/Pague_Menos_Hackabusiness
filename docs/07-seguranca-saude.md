# 07 — Segurança e saúde

A rede vende medicamentos. O enunciado diz que uma solução que recomenda produtos de saúde sem tratar responsabilidade, contraindicações e limites da IA dificilmente será considerada viável. Este documento define o que a IA **faz**, **não faz** e **encaminha**.

> Status: política e regras desenhadas; versão simulada implementada no app para demonstrar as telas. Regras clínicas reais precisam de validação por profissionais de saúde antes de qualquer uso real.

## Princípio

**Escopo inicial: cosméticos e autocuidado** (skin care, proteção solar, tratamento cosmético). Medicamentos, sintomas e condições de saúde ficam fora das recomendações da IA. Mostrar como uma camada validada trataria esses casos é parte da proposta, mas não é implementado por inventar regras clínicas sem validação.

## Três zonas

| Zona | Exemplos | Comportamento |
| --- | --- | --- |
| **Permitido** | skin care, hidratação, limpeza, protetor solar, tratamento cosmético de acne ou manchas | Gera kits, com avisos por produto |
| **Cautela** | gestação ou amamentação com ativos como retinol; pele muito irritada; "tratamento" de acne intensa | Gera kits sem os ativos de risco, mostra aviso e sugere conversar com dermatologista ou farmacêutico |
| **Bloqueado** | medicamento (nome, dose, "o que tomar"), sintoma (dor, febre), condição de saúde (dermatite, psoríase, infecção, ferida), interações medicamentosas | Sem kit. Explica o limite e encaminha a farmacêutico ou médico |

## Intenções bloqueadas (lista inicial, a expandir e validar)

Categorias de gatilho: nome de classe ou de medicamento (antibiótico, anti-inflamatório, corticoide, isotretinoína, analgésico); pedido de dose ou posologia; sintomas (dor, febre, coceira intensa, sangramento, inchaço); condições (dermatite, psoríase, rosácea, micose, infecção, ferida, alergia grave); "receita", "remédio", "o que tomar", "posso misturar com".

Implementação alvo: regras determinísticas **antes** de qualquer modelo (rápidas, auditáveis), mais um classificador de intenção como segunda camada. Ambiguidade vai para o lado seguro (encaminha).

## O que a IA nunca faz

1. Sugerir medicamento, dose, duração ou combinação terapêutica.
2. Apresentar benefício clínico, diagnóstico ou "cura" de um produto.
3. Montar combinação só porque os itens estão em promoção.
4. Inventar preço, estoque, composição ou contraindicação.
5. Dizer que um produto "é seguro para você": só informa os avisos documentados do produto.

## Proteções dentro dos kits permitidos

| Proteção | Regra |
| --- | --- |
| Interações entre ativos | `evitar` nunca no mesmo kit; `separar` só em períodos diferentes, com alerta (doc 06, K4) |
| Fotossensibilizante | Exige proteção solar no kit ou alerta `sem_protetor_no_kit` (K5) |
| Gestação e amamentação | Ao ser mencionada, produtos com aviso `consultar_se_gestante` saem do kit e aparece o aviso de cautela (K11) |
| Avisos por produto | Visíveis no detalhe do kit antes de adicionar ao carrinho |
| Transparência | Cada item explica por que está no kit; avisos e alternativas visíveis |
| Dados | Sem benefício clínico ou estoque sem fonte; preço e estoque só do inventário |

## Texto de encaminhamento (modelo)

> Esse tipo de pedido envolve saúde. Aqui eu só monto kits de cuidados com a pele. Para medicamentos e sintomas, converse com um farmacêutico ou médico.

Ação principal: "Falar com um farmacêutico" (simulada na demonstração). Ação secundária, quando o pedido citava a pele: "Ver cuidados cosméticos" (kits sem alegação terapêutica e com a ressalva de que cosméticos não substituem avaliação profissional).

## Como uma camada de medicamentos seria tratada (proposta, não implementada)

1. Base de referência validada (ex.: dados públicos da Anvisa: princípio ativo, indicações, contraindicações) e curada por farmacêuticos.
2. Regras de contraindicação e interação medicamentosa mantidas por profissionais, versionadas e auditáveis.
3. A IA só **organiza e explica** o que a base valida; nunca decide clinicamente.
4. Medicamentos com prescrição seguem o fluxo de receita; a IA não os recomenda.
5. Encaminhamento a farmacêutico em qualquer dúvida, com registro da conversa para ele.
6. Revisão e testes clínicos de segurança antes de ativar, com métricas de recusa correta.

## Como conferimos (doc 08)

Casos T7 a T10 cobrem bloqueio, cautela e interações. Meta: 100% dos casos bloqueados sem kit; 0 kits com par `evitar`; 0 kits com retinol quando gestação é declarada.

## Limites desta versão

A lista de gatilhos é simples e em português; não cobre todas as formas de dizer. O sistema real precisaria de classificador treinado, revisão clínica e monitoramento. Os textos de aviso são genéricos e fictícios, sem validação profissional.
