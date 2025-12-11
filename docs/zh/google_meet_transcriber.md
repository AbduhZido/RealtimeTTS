# Google Meet 转录器架构

[EN](../en/google_meet_transcriber.md) | [FR](../fr/google_meet_transcriber.md) | [ES](../es/google_meet_transcriber.md) | [DE](../de/google_meet_transcriber.md) | [IT](../it/google_meet_transcriber.md) | [ZH](../zh/google_meet_transcriber.md) | [JA](../ja/google_meet_transcriber.md) | [HI](../hi/google_meet_transcriber.md) | [KO](../ko/google_meet_transcriber.md) | [RU](../ru/google_meet_transcriber.md)

*Google Meet 实时转录管道的架构文档*

本页面提供了用于 Google Meet 实时转录的架构概述。有关完整的详细中文文档，请参阅[英文版本](../en/google_meet_transcriber.md)。

## 快速概述

完整的系统包括：

1. **浏览器扩展** - 从 Google Meet 捕获音频并通过 WebSocket 发送
2. **FastAPI 服务器** - 托管 RealtimeSTT 以进行服务器端转录
3. **N8N Webhook** - 处理并将转录存储在 Google Drive 中
4. **Google Drive** - 转录文件的安全存储

## 关键设计决策

- **服务器端转录** : 在 FastAPI 服务中执行，而非在扩展中
- **WebSocket + PCM 流** : 低延迟二进制音频协议
- **Webhook 合约** : 为 N8N 集成结构化的 JSON 有效负载

## 数据合约

有关以下内容的完整文档：
- 握手消息 (start/audio/stop)
- Webhook 有效负载结构
- 安全考虑
- 故障排除

请参阅[完整英文版本](../en/google_meet_transcriber.md)。

## 安全性

- 所有 WebSocket 必须使用 WSS（WebSocket 安全）
- 所有 Webhook 必须使用 HTTPS
- API 密钥必须安全存储
- Webhook 推荐使用 HMAC-SHA256 签名

有关安全性的更多信息，请参阅[英文版本](../en/google_meet_transcriber.md)。

