# Аудит зависимостей Tribe — октябрь 2026

Перед первым production-деплоем **не обновляем массово** `poetry.lock`, чтобы не смешивать риск несовместимости пакетов с настройкой B2B. Обновление — отдельным PR после Docker build и тестов.

## Зафиксировано в backend/poetry.lock
- langchain-gigachat 0.3.11, gigachat 0.1.40
- langchain-core 0.3.68, langchain 0.3.26, langchain-openai 0.3.27, langgraph 0.2.28
- fastembed 0.3.6, qdrant-client 1.11.1, httpx 0.27.0

## Запланировать отдельными PR
1. `langchain-gigachat` 0.5.x: migration guide заменил `auto_upload_images` на `auto_upload_attachments`. Обновить `gigachat` и `langchain-core` согласованно.
2. LangChain v1 требует отказа от ограничений `langchain-core<0.4` и миграции imports/graph tools.
3. Проверить OpenAI Responses API и вызовы Files API, GigaChat file uploads и удаление.
4. Пересобрать `poetry.lock` через Poetry, выполнить unit/integration tests и Docker build.
5. Отдельно обновить Docker base images и версии Postgres/Qdrant с планом миграции.
6. TLS: существующая интеграция использует `verify_ssl_certs=False`; в production установить доверенный CA и включить проверку цепочки сертификатов.

Источники:
- https://github.com/ai-forever/langchain-gigachat/blob/master/libs/gigachat/MIGRATION.md
- https://github.com/ai-forever/langchain-gigachat/releases
