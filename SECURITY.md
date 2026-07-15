# Security

## Secrets

Не коммитьте в репозиторий:

- GitHub tokens;
- API keys;
- `.env`;
- `.netrc`;
- файлы credentials;
- реальные выгрузки баз клиентов;
- персональные данные.

## GitHub token

Если токен был случайно отправлен в чат, issue, commit или лог — немедленно отзовите его в GitHub:

```text
GitHub → Settings → Developer settings → Personal access tokens → Revoke
```

## 1С production принцип

AI не должен проводить документы автоматически. Система создаёт только непроведённый черновик, который проверяет человек.
