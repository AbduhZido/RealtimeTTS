# Arquitectura de Google Meet Transcriber

[EN](../en/google_meet_transcriber.md) | [FR](../fr/google_meet_transcriber.md) | [ES](../es/google_meet_transcriber.md) | [DE](../de/google_meet_transcriber.md) | [IT](../it/google_meet_transcriber.md) | [ZH](../zh/google_meet_transcriber.md) | [JA](../ja/google_meet_transcriber.md) | [HI](../hi/google_meet_transcriber.md) | [KO](../ko/google_meet_transcriber.md) | [RU](../ru/google_meet_transcriber.md)

*Documentación de arquitectura para el pipeline de transcripción en tiempo real de Google Meet*

Esta página proporciona una descripción general de la arquitectura utilizada para la transcripción en tiempo real de Google Meet. Para la documentación completa detallada en español, consulte la [versión en inglés](../en/google_meet_transcriber.md).

## Descripción general rápida

El sistema completo incluye:

1. **Extensión del navegador** - Captura audio de Google Meet y lo envía vía WebSocket
2. **Servidor FastAPI** - Aloja RealtimeSTT para transcripción del lado del servidor
3. **Webhooks de N8N** - Procesa y almacena transcripciones en Google Drive
4. **Google Drive** - Almacenamiento seguro de archivos de transcripción

## Decisiones clave

- **Transcripción del lado del servidor** : Ejecución en un servicio FastAPI, no en la extensión
- **Streaming WebSocket + PCM** : Protocolo de audio binario de baja latencia
- **Contrato de webhook** : Cargas útiles JSON estructuradas para integración N8N

## Contratos de datos

Para documentación completa sobre:
- Mensajes de protocolo de enlace (start/audio/stop)
- Estructuras de carga útil de webhook
- Consideraciones de seguridad
- Solución de problemas

Consulte la [versión completa en inglés](../en/google_meet_transcriber.md).

## Seguridad

- Todos los WebSockets deben usar WSS (WebSocket Secure)
- Todos los webhooks deben usar HTTPS
- Las claves API deben almacenarse de forma segura
- Se recomiendan firmas HMAC-SHA256 para webhooks

Para más información sobre seguridad, consulte la [versión en inglés](../en/google_meet_transcriber.md).

