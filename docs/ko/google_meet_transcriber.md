# Google Meet 트랜스크라이버 아키텍처

[EN](../en/google_meet_transcriber.md) | [FR](../fr/google_meet_transcriber.md) | [ES](../es/google_meet_transcriber.md) | [DE](../de/google_meet_transcriber.md) | [IT](../it/google_meet_transcriber.md) | [ZH](../zh/google_meet_transcriber.md) | [JA](../ja/google_meet_transcriber.md) | [HI](../hi/google_meet_transcriber.md) | [KO](../ko/google_meet_transcriber.md) | [RU](../ru/google_meet_transcriber.md)

*Google Meet 실시간 전사 파이프라인을 위한 아키텍처 문서*

이 페이지는 Google Meet 실시간 전사에 사용되는 아키텍처의 개요를 제공합니다. 완전한 상세 문서는 [영문 버전](../en/google_meet_transcriber.md)을 참조하세요.

## 빠른 개요

완전한 시스템에는 다음이 포함됩니다:

1. **브라우저 확장프로그램** - Google Meet에서 오디오를 캡처하고 WebSocket을 통해 전송
2. **FastAPI 서버** - 서버 측 전사를 위해 RealtimeSTT 호스트
3. **N8N Webhooks** - Google Drive에서 전사본 처리 및 저장
4. **Google Drive** - 전사 파일의 안전한 저장

## 주요 설계 결정

- **서버 측 전사** : 확장프로그램이 아닌 FastAPI 서비스에서 실행
- **WebSocket + PCM 스트리밍** : 저지연 바이너리 오디오 프로토콜
- **Webhook 계약** : N8N 통합을 위한 구조화된 JSON 페이로드

## 데이터 계약

다음에 대한 완전한 문서:
- 핸드셰이크 메시지 (start/audio/stop)
- Webhook 페이로드 구조
- 보안 고려 사항
- 문제 해결

[완전한 영문 버전](../en/google_meet_transcriber.md)을 참조하세요.

## 보안

- 모든 WebSocket은 WSS(WebSocket Secure) 사용 필수
- 모든 Webhooks은 HTTPS 사용 필수
- API 키는 안전하게 저장해야 함
- Webhooks에는 HMAC-SHA256 서명 권장

보안에 대한 자세한 내용은 [영문 버전](../en/google_meet_transcriber.md)을 참조하세요.

