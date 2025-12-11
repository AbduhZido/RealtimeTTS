# Google Meet Transcriber Architektur

[EN](../en/google_meet_transcriber.md) | [FR](../fr/google_meet_transcriber.md) | [ES](../es/google_meet_transcriber.md) | [DE](../de/google_meet_transcriber.md) | [IT](../it/google_meet_transcriber.md) | [ZH](../zh/google_meet_transcriber.md) | [JA](../ja/google_meet_transcriber.md) | [HI](../hi/google_meet_transcriber.md) | [KO](../ko/google_meet_transcriber.md) | [RU](../ru/google_meet_transcriber.md)

*Architektur-Dokumentation für die Google Meet-Echtzeit-Transkriptionspipeline*

Diese Seite bietet einen Überblick über die für die Google Meet-Echtzeittranskription verwendete Architektur. Vollständige deutsche Dokumentation finden Sie in der [englischen Version](../en/google_meet_transcriber.md).

## Schnelläberblick

Das komplette System umfasst:

1. **Browser-Erweiterung** - Erfasst Audio aus Google Meet und sendet es via WebSocket
2. **FastAPI-Server** - Hostet RealtimeSTT für serverseitige Transkription
3. **N8N-Webhooks** - Verarbeitet und speichert Transkriptionen in Google Drive
4. **Google Drive** - Sichere Speicherung von Transkriptionsdateien

## Wichtige Entwurfsentscheidungen

- **Serverseitige Transkription** : Ausführung in einem FastAPI-Service, nicht in der Erweiterung
- **WebSocket + PCM-Streaming** : Binäres Audioprotokoll mit niedriger Latenz
- **Webhook-Kontrakt** : Strukturierte JSON-Payloads für N8N-Integration

## Datenverträge

Für vollständige Dokumentation zu:
- Handshake-Meldungen (start/audio/stop)
- Webhook-Payload-Strukturen
- Sicherheitsüberlegungen
- Fehlerbehebung

Siehe [vollständige englische Version](../en/google_meet_transcriber.md).

## Sicherheit

- Alle WebSockets müssen WSS (WebSocket Secure) verwenden
- Alle Webhooks müssen HTTPS verwenden
- API-Schlüssel müssen sicher gespeichert werden
- HMAC-SHA256-Signaturen werden für Webhooks empfohlen

Weitere Informationen zur Sicherheit finden Sie in der [englischen Version](../en/google_meet_transcriber.md).

