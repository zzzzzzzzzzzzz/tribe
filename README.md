# Tribe

**Tribe** is a self-hosted application for building and running teams of LLM agents. Configure each member's role, model, tools, and knowledge base, then run sequential or hierarchical workflows through the web UI or API.

This repository is a deployment-focused fork of [the original Tribe project](https://github.com/StreetLamb/tribe).

## Features

- Visual editor for multi-agent teams and execution flows.
- Sequential and hierarchical orchestration powered by LangGraph.
- Tool calling, reusable skills, human approval, and persistent conversations.
- Knowledge retrieval from uploaded documents using FastEmbed and Qdrant.
- OpenAI and GigaChat integrations. GigaChat is configured for `GIGACHAT_API_B2B` and supports **GigaChat-2-Max only**.
- Team API for external applications.

## Architecture

| Component | Technology |
| --- | --- |
| Web app | React, Vite, Nginx |
| Backend | FastAPI, LangChain, LangGraph |
| Background jobs | Celery, Redis |
| Database | PostgreSQL |
| Vector search | Qdrant, FastEmbed |
| Reverse proxy (production) | Traefik, Let's Encrypt |
| Delivery | GitHub Actions → GHCR → Docker Compose on a VPS |

Production runs **six application services**: PostgreSQL, Redis, Qdrant, backend, Celery, and frontend. Traefik runs separately as the HTTPS proxy. n8n, Adminer, Flower, and self-hosted GitHub runners are not part of this deployment.

## Local development

Install Docker Engine + Docker Compose (or Docker Desktop), then:

```bash
git clone https://github.com/zzzzzzzzzzzzz/tribe.git
cd tribe
cp .env.example .env
docker compose -f docker-compose.yml up --build -d
```

- Frontend: [http://localhost:8080](http://localhost:8080)
- API documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- API: [http://localhost:8000/api/v1](http://localhost:8000/api/v1)

These ports bind to `127.0.0.1`; PostgreSQL, Redis, and Qdrant are reachable only through the internal Compose network. The example `.env` contains **development credentials only** — never use them in production.

Stop containers without deleting databases or uploads:

```bash
docker compose -f docker-compose.yml down
```

Run backend tests after starting the local stack:

```bash
docker compose -f docker-compose.yml exec -T backend bash /app/tests-start.sh
```

## Production deployment

Current target: **FST.KZ VPS**, Ubuntu 24.04/26.04, 3 vCPU / 8 GB RAM, `tribe.zzzzzzzzzzzzz.cc`. The deployment uses only the files under [`deploy/`](./deploy/).

1. Follow the [VPS bootstrap and SSH hardening guide](./deploy/FST-KZ-README.md).
2. Store application secrets in `/opt/tribe/.env` on the VPS, based on [`deploy/env.production.example`](./deploy/env.production.example). Keep it out of Git.
3. Create GitHub Actions secrets `VPS_DEPLOY_SSH_KEY` and `VPS_SSH_KNOWN_HOSTS`; the runner uses the built-in `GITHUB_TOKEN` for GHCR.
4. **First deployment:** Actions → **Deploy Tribe** → **Run workflow**, branch `master`.
5. **After the first successful deployment:** set repository Actions variable `TRIBE_AUTO_DEPLOY` to `true`. Then pushes to `master` **and** published GitHub Releases deploy automatically. When the variable is absent or `false`, automated deployment jobs are skipped; manual deployment remains available.

Jobs run on **GitHub-hosted `ubuntu-latest`**, never on the VPS. Backend and frontend images are tagged with the source SHA, pushed to GHCR, and pulled onto the server over verified SSH. Production configuration is in [`deploy/compose.prod.yml`](./deploy/compose.prod.yml) and [`deploy/compose.proxy.yml`](./deploy/compose.proxy.yml).

**Data and safety:** Only ports 22, 80, and 443 are exposed. PostgreSQL, Redis, and Qdrant are not publicly accessible. Docker volumes persist data across restarts, but you must configure off-server backups for PostgreSQL, Qdrant, and uploads before storing important data. Do not use `docker compose down -v` in production.

## Model configuration

- OpenAI: set `OPENAI_API_KEY` when needed.
- GigaChat: set `GIGACHAT_AUTH_TOKEN` to your B2B authorization key; see [B2B configuration](./docs/gigachat-b2b.md).
- Dense embeddings: `BAAI/bge-small-en-v1.5` (English-focused) by default.
- Sparse embeddings: `prithivida/Splade_PP_en_v1` (English-focused) by default.

Changing an embedding model may require rebuilding the Qdrant index. Multilingual embedding alternatives are under evaluation; no model migration has been made yet. Dependency modernization is tracked in the [dependency audit](./docs/dependency-audit-2026-10.md).

## License

See [LICENSE](./LICENSE).
