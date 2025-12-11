# Arquitetura do Google Meet Transcriber

[EN](../en/google_meet_transcriber.md) | [FR](../fr/google_meet_transcriber.md) | [ES](../es/google_meet_transcriber.md) | [DE](../de/google_meet_transcriber.md) | [IT](../it/google_meet_transcriber.md) | [ZH](../zh/google_meet_transcriber.md) | [JA](../ja/google_meet_transcriber.md) | [HI](../hi/google_meet_transcriber.md) | [KO](../ko/google_meet_transcriber.md) | [RU](../ru/google_meet_transcriber.md)

*Documentação de arquitetura para o pipeline de transcrição em tempo real do Google Meet*

Esta página fornece uma visão geral da arquitetura usada para transcrição em tempo real do Google Meet. Para documentação completa detalhada em português, consulte a [versão em inglês](../en/google_meet_transcriber.md).

## Visão Geral Rápida

O sistema completo inclui:

1. **Extensão do navegador** - Captura áudio do Google Meet e envia via WebSocket
2. **Servidor FastAPI** - Hospeda RealtimeSTT para transcrição do lado do servidor
3. **Webhooks N8N** - Processa e armazena transcrições no Google Drive
4. **Google Drive** - Armazenamento seguro de arquivos de transcrição

## Decisões de Design Principais

- **Transcrição do lado do servidor** : Execução em um serviço FastAPI, não na extensão
- **Streaming WebSocket + PCM** : Protocolo de áudio binário de baixa latência
- **Contrato Webhook** : Payloads JSON estruturadas para integração N8N

## Contratos de Dados

Para documentação completa sobre:
- Mensagens de handshake (start/audio/stop)
- Estruturas de payload webhook
- Considerações de segurança
- Solução de problemas

Consulte a [versão completa em inglês](../en/google_meet_transcriber.md).

## Segurança

- Todos os WebSockets devem usar WSS (WebSocket Secure)
- Todos os webhooks devem usar HTTPS
- As chaves API devem ser armazenadas com segurança
- As assinaturas HMAC-SHA256 são recomendadas para webhooks

Para mais informações sobre segurança, consulte a [versão em inglês](../en/google_meet_transcriber.md).

