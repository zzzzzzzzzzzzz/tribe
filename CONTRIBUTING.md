# Development and contributions

This repository is currently maintained as a small deployment-focused fork of [Tribe](https://github.com/StreetLamb/tribe).

- Read [README.md](./README.md) for the local Docker Compose setup.
- Keep application secrets out of commits; use `.env` locally.
- Run checks using `docker compose -f docker-compose.yml exec -T backend bash /app/tests-start.sh` after starting the stack.
- Production releases are built by GitHub Actions and delivered through GHCR; see [the deployment guide](./deploy/FST-KZ-README.md).

For changes that alter LangChain, FastEmbed, or database dependencies, update the lock files and test both images before deployment.
