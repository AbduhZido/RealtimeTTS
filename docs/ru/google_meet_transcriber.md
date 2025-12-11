# Архитектура Google Meet Transcriber

[EN](../en/google_meet_transcriber.md) | [FR](../fr/google_meet_transcriber.md) | [ES](../es/google_meet_transcriber.md) | [DE](../de/google_meet_transcriber.md) | [IT](../it/google_meet_transcriber.md) | [ZH](../zh/google_meet_transcriber.md) | [JA](../ja/google_meet_transcriber.md) | [HI](../hi/google_meet_transcriber.md) | [KO](../ko/google_meet_transcriber.md) | [RU](../ru/google_meet_transcriber.md)

*Документация архитектуры для конвейера преобразования речи в текст Google Meet в реальном времени*

Эта страница содержит описание архитектуры, используемой для преобразования речи в текст Google Meet в реальном времени. Полную подробную документацию см. в [английской версии](../en/google_meet_transcriber.md).

## Краткий обзор

Полная система включает:

1. **Расширение браузера** - захватывает звук из Google Meet и отправляет его через WebSocket
2. **Сервер FastAPI** - размещает RealtimeSTT для преобразования речи в текст на стороне сервера
3. **Webhooks N8N** - обрабатывает и сохраняет транскрипции на Google Drive
4. **Google Drive** - безопасное хранилище файлов транскрипций

## Ключевые проектные решения

- **Преобразование речи в текст на стороне сервера** : Выполнение в сервисе FastAPI, а не в расширении
- **Потоковая передача WebSocket + PCM** : Протокол двоичного звука с низкой задержкой
- **Контракт Webhook** : Структурированные полезные данные JSON для интеграции N8N

## Контракты данных

Полную документацию по следующим вопросам см.:
- Сообщения рукопожатия (start/audio/stop)
- Структуры полезных данных webhook
- Соображения безопасности
- Устранение проблем

См. [полную английскую версию](../en/google_meet_transcriber.md).

## Безопасность

- Все WebSocket должны использовать WSS (WebSocket Secure)
- Все webhook должны использовать HTTPS
- Ключи API должны храниться безопасно
- Подписи HMAC-SHA256 рекомендуются для webhook

Дополнительные сведения о безопасности см. в [английской версии](../en/google_meet_transcriber.md).

