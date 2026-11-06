Projeto ENADEc
Pipeline de ingestão, mensagens, indexação e busca de questões do ENADE.

Pilha
Python 3.11, FastAPI, PyMuPDF, Pydantic
Kafka (KRaft), Elasticsearch 8, Redis
React + Vite
Docker Compose
OpenLDAP (base de autenticação) e MIT Kerberos (perfil de infraestrutura)
Esta é uma base progressiva para desenvolvimento. LDAP e Kerberos são provisionados como serviços de laboratório, mas a autenticação Kerberos SASL/GSSAPI ponta a ponta exige emissão de principais/keytabs e configuração TLS/JAAS compatível com as imagens escolhidas. Não considere RF22/RF23 concluídos antes dos testes de tecnologia descritos abaixo.

Subir sem Codespaces
Crie um repositório GitHub vazio e abra-o em Codespaces.
Copie os arquivos desta estrutura para a raiz.
Executar:
cp .env.example .env
docker compose up -d --build
Acompanhe: docker compose pse docker compose logs -f api worker.
API: http://localhost:8000/docs
Frontend: http://localhost:5173
Elasticsearch: http://localhost:9200
OpenLDAP: localhost:389 (admin / senha definida no .env).
Ingerir PDFs
Coloque os PDFs em data/pdfs/e execute:

docker compose exec api python -m app.ingestion.cli --input /app/data/pdfs
O produtor publica questões no tópico enade.questions; o índice de trabalho no Elasticsearch. PDFs não são desativados.

Pontos finais principais
GET /health
GET /questions?q=ética&area=...&course=...&year=...&kind=FG
GET /questions/{id}
GET /analytics/courses
GET /analytics/competencies
POST /cart/{session_id}eGET /cart/{session_id}
POST /auth/login(LDAP)
Organização
app/ingestion: remoção, segmentação e produtor Kafka
app/worker: consumidor Kafka, DLQ e Elasticsearch
app/api: rotas, autenticação e cache
frontend: interface React
infra: configurações auxiliares
Limitações deliberadas da primeira entrega
A segmentação automática por heurística precisa ser validada em PDFs reais; o formato das provas varia.
Fórmulas/imagens são preservadas como referência de página e sinalizadas para revisão. A conversão multimodal para LaTeX/Mermaid deve ser adicionada com avaliação humana; não há conversão fictícia.
competenciese knowledge_objectssão metadados que precisam ser enriquecidos a partir das diretrizes/itens oficiais.
Para produção, configure TLS, gerenciador de segredos, backup, replicação, ACLs Kafka/Elasticsearch e Kerberos SASL/GSSAPI real.
A composição é de laboratório/desenvolvimento, não uma implantação de produção.
Testes
docker compose exec api pytest -q
Decisões iniciais de topologia
Para laboratório local: 1 corretora Kafka, 3 partições no tópico principal e 1 no DLQ; Elasticsearch com 1 shard primário e 0 réplicas; Redis autônomo. Em produção, aumente brokers/partições conforme vazão, shards conforme volume e réplicas conforme disponibilidade. Em nó único, as réplicas não aumentam a tolerância à falha.

GitHub
git init
git add .
git commit -m "feat: estrutura inicial do pipeline ENADE"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git
git push -u origin main