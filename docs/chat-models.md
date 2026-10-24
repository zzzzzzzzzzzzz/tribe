# Allowed chat models

Tribe uses a **closed model list** in the team editor and validates the
model name server-side on member creation, modification, team import and
inference. Any previously saved models outside the list must be updated.

## OpenAI

- `gpt-5.2`
- `gpt-4-turbo`
- `gpt-4`
- `gpt-5-nano`
- `gpt-5.1`
- `gpt-4.1`
- `gpt-4.1-mini`
- `gpt-4.1-nano`
- `gpt-6-luna`
- `gpt-5.6-luna`
- `gpt-5.6-terra`
- `gpt-5.5`
- `gpt-5.4-mini`
- `gpt-5.4-nano`
- `gpt-4o-mini`
- `gpt-4o`
- `gpt-3.5-turbo`

For new agents, the default OpenAI model remains `gpt-4o-mini`.

**Important:** These are explicitly configured identifiers, not a guarantee
that OpenAI offers every name on every account. In particular, specialized
`luna` and `terra` identifiers may require a separate OpenAI-compatible
endpoint configured as `base_url`. A model present in this list might still
return a provider-side `model_not_found` or access error.

## GigaChat

- `GigaChat-2-Max` (B2B scope)

The UI and backend enforce the same policy. Model changes require a new
frontend/backend image deployment; the values are not controlled through
`.env`.

### Strict import error reporting

Team import validates every referenced skill, uploaded document, and provider
model before any database writes. A missing resource returns HTTP 422 with
its exact name and a hint to import the skill or upload the document first.
The UI shows the server's error detail instead of hiding the underlying reason.
No resources are created automatically and no existing skill is modified.

### Reusing earlier chat attachments

Tribe stores per-provider file IDs with the chat thread. On subsequent
messages, the graph includes a short reference to earlier images and documents
in the model input, without uploading the file again.

- OpenAI Responses API: `input_image` / `input_file` with `file_id`.
- GigaChat: an `attachments` array on a user message.
- Images: up to 10 recent images per request, including new ones (GigaChat API
  limit); at most 5 earlier documents are included.
- Provider files are stored for up to 30 days. Expired or deleted provider
  uploads cannot be referenced later; upload again if the API rejects an old ID.
- The app still passes normal text conversation history through its existing
  checkpointed LangGraph state.
