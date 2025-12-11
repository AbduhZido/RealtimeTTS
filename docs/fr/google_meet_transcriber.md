# Architecture de Google Meet Transcriber

[EN](../en/google_meet_transcriber.md) | [FR](../fr/google_meet_transcriber.md) | [ES](../es/google_meet_transcriber.md) | [DE](../de/google_meet_transcriber.md) | [IT](../it/google_meet_transcriber.md) | [ZH](../zh/google_meet_transcriber.md) | [JA](../ja/google_meet_transcriber.md) | [HI](../hi/google_meet_transcriber.md) | [KO](../ko/google_meet_transcriber.md) | [RU](../ru/google_meet_transcriber.md)

*Documentation de l'architecture pour le pipeline de transcription en temps réel de Google Meet*

Cette page contient une vue d'ensemble complète de l'architecture utilisée pour la transcription en temps réel de Google Meet. Pour une documentation détaillée complète en français, veuillez consulter la [version anglaise](../en/google_meet_transcriber.md).

## Vue d'ensemble rapide

Le système complet comprend :

1. **Extension de navigateur** - Capture l'audio de Google Meet et l'envoie via WebSocket
2. **Serveur FastAPI** - Héberge RealtimeSTT pour la transcription côté serveur
3. **Webhooks N8N** - Traite et stocke les transcriptions dans Google Drive
4. **Google Drive** - Stockage sécurisé des fichiers de transcription

## Décisions clés

- **Transcription côté serveur** : Exécution dans un service FastAPI, pas dans l'extension
- **Streaming WebSocket + PCM** : Protocole audio binaire à faible latence
- **Contrat de webhook** : Payloads JSON structurés pour l'intégration N8N

## Contrats de données

Pour une documentation complète sur :
- Les messages de poignée de main (start/audio/stop)
- Les structures de charge utile webhook
- Les considérations de sécurité
- Le dépannage

Veuillez consulter la [version anglaise complète](../en/google_meet_transcriber.md).

## Sécurité

- Tous les WebSockets doivent utiliser WSS (WebSocket Secure)
- Tous les webhooks doivent utiliser HTTPS
- Les clés API doivent être stockées de manière sécurisée
- Les signatures HMAC-SHA256 sont recommandées pour les webhooks

Pour plus d'informations sur la sécurité, veuillez consulter la [version anglaise](../en/google_meet_transcriber.md).

