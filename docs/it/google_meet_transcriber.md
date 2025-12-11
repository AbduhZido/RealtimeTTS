# Architettura di Google Meet Transcriber

[EN](../en/google_meet_transcriber.md) | [FR](../fr/google_meet_transcriber.md) | [ES](../es/google_meet_transcriber.md) | [DE](../de/google_meet_transcriber.md) | [IT](../it/google_meet_transcriber.md) | [ZH](../zh/google_meet_transcriber.md) | [JA](../ja/google_meet_transcriber.md) | [HI](../hi/google_meet_transcriber.md) | [KO](../ko/google_meet_transcriber.md) | [RU](../ru/google_meet_transcriber.md)

*Documentazione architetturale per la pipeline di trascrizione in tempo reale di Google Meet*

Questa pagina fornisce una panoramica dell'architettura utilizzata per la trascrizione in tempo reale di Google Meet. Per la documentazione completa dettagliata in italiano, consultare la [versione in inglese](../en/google_meet_transcriber.md).

## Panoramica rapida

Il sistema completo include:

1. **Estensione del browser** - Cattura l'audio da Google Meet e lo invia via WebSocket
2. **Server FastAPI** - Ospita RealtimeSTT per la trascrizione lato server
3. **Webhook N8N** - Elabora e archivia i trascritti in Google Drive
4. **Google Drive** - Archiviazione sicura dei file di trascrizione

## Decisioni di progettazione chiave

- **Trascrizione lato server** : Esecuzione in un servizio FastAPI, non nell'estensione
- **Streaming WebSocket + PCM** : Protocollo audio binario a bassa latenza
- **Contratto webhook** : Payload JSON strutturati per l'integrazione N8N

## Contratti dati

Per documentazione completa su:
- Messaggi di handshake (start/audio/stop)
- Strutture di payload webhook
- Considerazioni sulla sicurezza
- Risoluzione dei problemi

Consultare la [versione completa in inglese](../en/google_meet_transcriber.md).

## Sicurezza

- Tutti i WebSocket devono utilizzare WSS (WebSocket Secure)
- Tutti i webhook devono utilizzare HTTPS
- Le chiavi API devono essere archiviate in modo sicuro
- Le firme HMAC-SHA256 sono consigliate per i webhook

Per ulteriori informazioni sulla sicurezza, consultare la [versione in inglese](../en/google_meet_transcriber.md).

