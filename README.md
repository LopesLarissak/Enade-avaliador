# ENADE Avaliador

Pipeline de ingestão, indexação e busca de questões do ENADE, com perfis de acesso e cache.

## Componentes

- API: Python 3.11, FastAPI, Elasticsearch e Redis.
- Ingestão: PyMuPDF extrai questões de PDFs e Kafka encaminha os registros para indexação.
- Interface: React + Vite.
- Identidade: OpenLDAP para perfis de estudante e professor.
- Execução local: Docker Compose.

## Executar localmente

```bash
cp .env.example .env
# Altere os valores de desenvolvimento no arquivo .env antes de usar fora do computador local.
docker compose up -d --build
```

- Interface: <http://localhost:5173>
- Documentação da API: <http://localhost:8000/docs>
- Saúde dos serviços: <http://localhost:8000/health>

O Compose é uma configuração de laboratório/desenvolvimento. Não é uma implantação de produção. A URL pública de demonstração ainda não foi configurada.

## Fluxo de ingestão

1. Coloque os PDFs em `data/pdfs/`.
2. Execute:

   ```bash
   docker compose exec api python -m app.ingestion.cli --input /app/data/pdfs
   ```

3. O extrator registra texto, página de origem, alternativas identificadas e itens que precisam de revisão de mídia.
4. O produtor envia os registros ao tópico `enade.questions`.
5. O worker indexa os registros no Elasticsearch; falhas definitivas são encaminhadas à DLQ.

Os PDFs de prova não são incluídos neste repositório. As questões extraídas devem ser revisadas antes de serem usadas para avaliação.

## Busca, cache e perfis

`GET /questions` faz busca textual em enunciados e alternativas. Pode-se filtrar mais de uma área com parâmetros repetidos:

```text
GET /questions?q=saúde&area=Saúde&area=Computação
```

Respostas de busca são armazenadas no Redis por 60 segundos. O perfil integra-se ao LDAP: professor pode ver gabaritos e análises; estudante não recebe gabarito e recebe `403` nas rotas de análise restritas. A interface permite informar uma ou várias áreas, curso e ano.

`POST /auth/login` recebe `username` e `password` em JSON. A sessão usa token aleatório armazenado no Redis. Para login funcionar, o LDAP precisa conter os usuários e grupos correspondentes; este repositório não cria contas reais automaticamente.

## Testes e relatório

```bash
python -m pytest -q
```

O relatório técnico em formato SBC, com método, resultados observados e limitações, está em [`reports/relatorio_sbc.pdf`](reports/relatorio_sbc.pdf); o fonte LaTeX e o estilo SBC utilizado acompanham o PDF.

## Limitações conhecidas

- A extração por heurísticas precisa ser comparada com uma amostra rotulada por pessoas; a contagem de candidatos não é uma medida de precisão.
- Figuras, fórmulas e questões com mídia exigem revisão humana.
- Kafka, Elasticsearch, Redis e LDAP precisam de validação de integração em execução; a configuração do Compose, sozinha, não comprova funcionamento ponta a ponta.
- Não foi produzido benchmark de latência/vazão nem validado o limite de cinco minutos.
- Kerberos está apenas provisionado como perfil de laboratório; autenticação SASL/GSSAPI, principals, keytabs e TLS não estão comprovados.
- Configure TLS, segredos, backup, replicação e controles de acesso antes de qualquer uso de produção.

Todas as mudanças devem ser propostas por pull request para `main`; não faça commits diretos nessa branch.

## Projeto-fonte

O código inicial da aplicação foi incorporado de [LopesLarissak/Projeto_enade_avaliador](https://github.com/LopesLarissak/Projeto_enade_avaliador).