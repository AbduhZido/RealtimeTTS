# Google Meet トランスクライバー アーキテクチャ

[EN](../en/google_meet_transcriber.md) | [FR](../fr/google_meet_transcriber.md) | [ES](../es/google_meet_transcriber.md) | [DE](../de/google_meet_transcriber.md) | [IT](../it/google_meet_transcriber.md) | [ZH](../zh/google_meet_transcriber.md) | [JA](../ja/google_meet_transcriber.md) | [HI](../hi/google_meet_transcriber.md) | [KO](../ko/google_meet_transcriber.md) | [RU](../ru/google_meet_transcriber.md)

*Google Meet リアルタイム文字起こしパイプラインのアーキテクチャドキュメント*

このページは、Google Meetのリアルタイム文字起こしに使用されるアーキテクチャの概要を提供します。完全な詳細なドキュメントについては、[英語版](../en/google_meet_transcriber.md)を参照してください。

## クイック概要

完全なシステムには以下が含まれます：

1. **ブラウザ拡張機能** - Google Meetからオーディオをキャプチャし、WebSocket経由で送信
2. **FastAPIサーバー** - サーバー側の文字起こしのためにRealtimeSTTをホスト
3. **N8N Webhook** - Google Driveで文字起こしを処理・保存
4. **Google Drive** - 文字起こしファイルの安全な保存

## 主要な設計上の決定

- **サーバー側の文字起こし** : 拡張機能ではなくFastAPIサービスで実行
- **WebSocket + PCMストリーミング** : 低遅延バイナリオーディオプロトコル
- **Webhookコントラクト** : N8N統合のための構造化されたJSONペイロード

## データコントラクト

以下に関する完全なドキュメント：
- ハンドシェイクメッセージ (start/audio/stop)
- Webhookペイロード構造
- セキュリティに関する考慮事項
- トラブルシューティング

[完全な英語版](../en/google_meet_transcriber.md)を参照してください。

## セキュリティ

- すべてのWebSocketはWSS（WebSocket Secure）を使用する必要があります
- すべてのWebhookはHTTPSを使用する必要があります
- APIキーは安全に保存する必要があります
- Webhookに対してはHMAC-SHA256署名が推奨されます

セキュリティに関する詳細は、[英語版](../en/google_meet_transcriber.md)を参照してください。

