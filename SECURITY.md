# Security

Do not post credentials, tokens, production data, or detailed vulnerability reports in public GitHub issues.

If GitHub private vulnerability reporting is enabled for this repository, use its **Security → Report a vulnerability** flow. Otherwise, contact the repository owner privately before disclosing sensitive findings.

The production deployment restricts published ports to SSH and HTTPS, keeps application credentials in a server-side `.env` file, and does not expose the database, Redis, or Qdrant directly. Follow [the deployment guide](./deploy/README.md) and apply security updates after testing.

This is a self-hosted project. Operators are responsible for host updates, trusted TLS certificates for external model providers, and backups.
