# Security

## Reporting a Vulnerability

Если вы нашли уязвимость в этом репозитории — не открывайте публичный issue.
Сообщите через GitHub Security Advisories:

```text
https://github.com/akoffice933-maker/ai-pricing-assistant-1c/security/advisories/new
```

Ответ — в течение разумного срока (проект в стадии MVP/pre-pilot, без формального SLA).
Публичное раскрытие — после того как фикс выпущен и обновлён деплой.

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
