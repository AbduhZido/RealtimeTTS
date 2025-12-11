# Google Meet ट्रांसक्राइबर आर्किटेक्चर

[EN](../en/google_meet_transcriber.md) | [FR](../fr/google_meet_transcriber.md) | [ES](../es/google_meet_transcriber.md) | [DE](../de/google_meet_transcriber.md) | [IT](../it/google_meet_transcriber.md) | [ZH](../zh/google_meet_transcriber.md) | [JA](../ja/google_meet_transcriber.md) | [HI](../hi/google_meet_transcriber.md) | [KO](../ko/google_meet_transcriber.md) | [RU](../ru/google_meet_transcriber.md)

*Google Meet रीयल-टाइम ट्रांसक्रिप्शन पाइपलाइन के लिए आर्किटेक्चर दस्तावेज़*

यह पृष्ठ Google Meet के रीयल-टाइम ट्रांसक्रिप्शन के लिए उपयोग की जाने वाली आर्किटेक्चर का अवलोकन प्रदान करता है। संपूर्ण विस्तृत दस्तावेज़ के लिए, कृपया [अंग्रेजी संस्करण](../en/google_meet_transcriber.md) देखें।

## त्वरित अवलोकन

पूर्ण प्रणाली में शामिल हैं:

1. **ब्राउज़र एक्सटेंशन** - Google Meet से ऑडियो कैप्चर करता है और WebSocket के माध्यम से भेजता है
2. **FastAPI सर्वर** - सर्वर-साइड ट्रांसक्रिप्शन के लिए RealtimeSTT होस्ट करता है
3. **N8N Webhooks** - Google Drive में ट्रांसक्रिप्ट को प्रोसेस और स्टोर करता है
4. **Google Drive** - ट्रांसक्रिप्ट फ़ाइलों का सुरक्षित स्टोरेज

## मुख्य डिज़ाइन निर्णय

- **सर्वर-साइड ट्रांसक्रिप्शन** : एक्सटेंशन में नहीं, FastAPI सेवा में निष्पादन
- **WebSocket + PCM स्ट्रीमिंग** : कम विलंबता बाइनरी ऑडियो प्रोटोकॉल
- **Webhook अनुबंध** : N8N इंटीग्रेशन के लिए संरचित JSON पेलोड

## डेटा अनुबंध

निम्नलिखित पर संपूर्ण दस्तावेज़:
- हैंडशेक संदेश (start/audio/stop)
- Webhook पेलोड संरचनाएं
- सुरक्षा संबंधी विचार
- समस्या निवारण

कृपया [संपूर्ण अंग्रेजी संस्करण](../en/google_meet_transcriber.md) देखें।

## सुरक्षा

- सभी WebSocket को WSS (WebSocket Secure) का उपयोग करना चाहिए
- सभी Webhooks को HTTPS का उपयोग करना चाहिए
- API कुंजियों को सुरक्षित रूप से संग्रहीत किया जाना चाहिए
- Webhooks के लिए HMAC-SHA256 हस्ताक्षर की सिफारिश की जाती है

सुरक्षा के बारे में अधिक जानकारी के लिए, कृपया [अंग्रेजी संस्करण](../en/google_meet_transcriber.md) देखें।

