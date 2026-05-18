# TTS Provider Comparison For Chinese Video Drafts

Last updated: 2026-05-18

This note compares text-to-speech providers for Swiss Narrative Video Maker. The goal is not to find the most expensive "best voice" but to choose a practical path for Chinese creator workflows:

- cheap or free for draft generation
- good enough Mandarin narration for review
- optional higher-quality final voice
- possible future custom voice based on the creator's own voice
- clear privacy and consent boundaries

## Short Answer

For this project, the best near-term strategy is:

1. Keep `edge-tts` as the free draft voice.
2. Add a provider abstraction so the user can switch TTS engines.
3. Prioritize Volcengine / Doubao TTS research for Chinese final voice quality and price.
4. Keep OpenAI TTS as a high-quality candidate, but not a free one.
5. Treat custom voice cloning as a later, consent-aware feature.

## Current State

The project currently uses two different speech technologies:

| Function | Current Tool | Cost Profile | Notes |
| --- | --- | --- | --- |
| Speech to text | `faster-whisper` local model | Free after installation | Good for large-scale transcription; cost is local compute time. |
| Text to speech | `edge-tts` | Free / unofficial | Useful for drafts, but voice quality and long-term API stability are not final-product grade. |

The user's complaint about "the voice sounds bad" is about TTS, not transcription.

## Provider Comparison

| Provider | Best Use | Cost Impression | Chinese Voice Quality | Custom Voice | Integration Risk | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Edge TTS | Free draft voice | Lowest | Acceptable for draft, not ideal for final | No serious custom voice workflow | Medium | Uses an unofficial package around Microsoft Edge voices. |
| Volcengine / Doubao | Chinese creator narration candidate | Likely competitive; must verify by product type | Strong Chinese ecosystem | Yes, via Doubao voice cloning products | Medium | Most interesting candidate for this project. Pricing varies by ordinary TTS, long text, big-model TTS, voice cloning, and voice licensing. |
| OpenAI TTS | High-quality final voice candidate | Paid, not free | Natural, multilingual | API docs expose custom voice/consent concepts; availability and policy should be verified before relying on it | Low to medium | Good fallback if quality beats domestic providers for a specific voice. |
| Azure AI Speech | Formal Microsoft TTS | Has free monthly character quota, then paid | Mature neural voices | Custom Neural Voice with consent process | Medium | More enterprise-oriented but stable and well documented. |
| Tencent Cloud TTS | Low-cost Chinese cloud TTS candidate | Has free resource package and low character pricing in older official PDF | Chinese provider, likely usable | Needs separate verification | Medium | Worth testing if setup is easier than Volcengine. |
| Alibaba Cloud TTS | General cloud TTS candidate | Trial exists; commercial billing by calls | Chinese provider, likely usable | Needs separate verification | Medium | Pricing model counts billing calls by text length. |
| Local TTS | Privacy-first/offline experimentation | Free after setup | Varies widely | Possible with open-source models | High | Installation and voice quality are the main risks. |

## Cost And Policy Notes From Official Sources

### OpenAI

OpenAI TTS is not free. The official pricing page lists `gpt-4o-mini-tts` with an estimated cost of `$0.015 / minute`, and older TTS models at `$15 / 1M characters` or `$30 / 1M characters` for HD.

Sources:

- https://platform.openai.com/docs/pricing
- https://developers.openai.com/api/docs/models/gpt-4o-mini-tts

Implication for this project:

- OpenAI TTS is acceptable as a paid quality option.
- It should not be described as a free voice solution.
- It may be cheap enough for final drafts, but not ideal as the default for repeated experimentation.

### Volcengine / Doubao

Volcengine has several related speech products:

- speech synthesis
- big-model speech synthesis
- long-text speech synthesis
- voice cloning
- speech recognition
- video subtitle generation

Official product docs describe speech synthesis for audio/video creation, support for high-quality voices, speed, pitch, volume, emotion, SSML, and long-text synthesis. The product overview also describes big-model voice cloning.

Sources:

- https://www.volcengine.com/docs/6561/163032
- https://www.volcengine.com/docs/6561/79817?lang=zh
- https://www.volcengine.com/docs/6561/1359370

Important caveat:

Volcengine pricing is split across different service types. "Cheap" may be true for one route but not another. We need to verify the exact product before implementation:

- ordinary TTS
- big-model TTS
- long-text TTS
- voice cloning
- public voice vs purchased licensed voice
- resource pack vs postpaid

Implication for this project:

- Volcengine / Doubao should be the first paid provider to test for Chinese final narration.
- It may fit the creator's preference better than OpenAI because the project is Chinese narration heavy.
- Do not hard-code it until credentials, service type, voice ID, and pricing are confirmed.

### Azure AI Speech

Azure AI Speech has a documented free tier. The pricing page lists Text to Speech Neural as `0.5 million characters free per month` for the free tier. Azure also has Custom Neural Voice, with explicit consent and responsible AI requirements.

Sources:

- https://azure.microsoft.com/en-gb/pricing/details/speech/
- https://learn.microsoft.com/en-us/azure/ai-services/speech-service/text-to-speech
- https://learn.microsoft.com/en-us/azure/ai-foundry/responsible-ai/speech-service/text-to-speech/disclosure-voice-talent?view=foundry-classic

Implication for this project:

- Azure is a stable formal provider.
- It may be useful if the creator wants Microsoft voices but with official API support rather than `edge-tts`.
- Custom voice is possible, but should be treated as a consent-bound advanced feature.

### Tencent Cloud

Tencent Cloud's official TTS purchase guide PDF says users can receive a free resource package, and lists charging by characters. The PDF states an `800万字符` free package for general speech synthesis, valid for three months after claiming. It also lists postpaid standard and premium voice character pricing in that document.

Source:

- https://main.qcloudimg.com/raw/document/product/pdf/1073_34112_cn.pdf

Important caveat:

The PDF is older. Before implementation, verify the current console price and product availability.

Implication for this project:

- Tencent is worth including in a later provider benchmark.
- It may be inexpensive for standard Mandarin generation.

### Alibaba Cloud

Alibaba Cloud's official pricing page says the trial version is currently free during the trial period, with limits. Commercial usage is postpaid and billed daily. For speech synthesis, billing calls are calculated from text length: text within 100 characters counts as one billing call, and each additional 100 characters adds one call.

Source:

- https://www.alibabacloud.com/help/zh/isi/product-overview/pricing

Implication for this project:

- Alibaba is viable but the billing model is less intuitive for long scripts.
- It should be tested after Volcengine unless the setup is much easier.

## Custom Voice And "My Voice But Better"

The user's desired direction is:

- avoid reading every script manually
- generate narration from final text
- optionally sound like the creator
- reduce strong accent
- remove filler words
- improve rhythm and delivery

This should be split into three layers:

### 1. Script Cleanup

Remove filler words and awkward phrasing before TTS:

- "嗯"
- "啊"
- "就是"
- "然后"
- repeated fragments
- overly long sentences

This is low risk and should happen in the script editing workflow.

### 2. Voice Selection And Direction

Use a high-quality public voice with style settings:

- calm documentary narration
- friendly creator voice
- faster short-video rhythm
- slower explanatory rhythm
- less dramatic, more trustworthy

This is the best next step.

### 3. Custom Voice / Voice Cloning

Use the creator's own voice as a reference, with explicit consent and careful data handling.

This is feasible in principle, but should not be the first implementation because:

- providers vary widely in quality and price
- voice data is biometric/sensitive
- consent and storage policies matter
- output may preserve accent more than desired
- "more like me" and "more standard Mandarin" can conflict

## Recommendation For Product Roadmap

### Task A: TTS Provider Abstraction

Add a provider interface:

```text
edge
volcengine
openai
azure
tencent
aliyun
local
```

Configuration should live in `.env`:

```text
TTS_PROVIDER=edge
TTS_VOICE=zh-CN-XiaoxiaoNeural
```

Provider-specific keys should be optional and only required when that provider is selected.

### Task B: Voice Audition Command

Add a command that generates the same sample sentence with multiple voices:

```powershell
python -m snvm audition-voice --text "瑞士为什么让很多人觉得生活更稳定？"
```

Output:

```text
output/voice_auditions/
  edge_xiaoxiao.mp3
  volc_wanwanxiaohe.mp3
  openai_voice_a.mp3
```

This makes provider choice based on listening, not assumptions.

### Task C: Volcengine First Paid Provider

Implement Volcengine / Doubao before OpenAI if:

- account setup is manageable
- API works from the user's region
- selected voice sounds better than Edge
- pricing is acceptable for repeated drafts

### Task D: Final Voice Policy

The tool should label voice outputs by usage:

- draft voice
- review voice
- final candidate voice
- custom creator voice

This prevents the current draft voice from being mistaken for final quality.

## Public Article Angle

Possible title:

> 做中文视频配音，AI TTS 到底该选谁：免费、便宜、自然和真人音色的取舍

Core argument:

1. Transcription and dubbing are different cost problems.
2. Local Whisper-style transcription is already cheap enough for creators.
3. TTS is where quality and cost start to matter.
4. Free voices are good for drafts but rarely ideal for final publishing.
5. Chinese creators should test domestic TTS providers, especially Volcengine / Doubao, before assuming OpenAI is the best default.
6. Voice cloning is promising, but creator consent, privacy, and "my voice but better" expectations must be handled carefully.

## Sources

- OpenAI API pricing: https://platform.openai.com/docs/pricing
- OpenAI GPT-4o mini TTS model: https://developers.openai.com/api/docs/models/gpt-4o-mini-tts
- Azure AI Speech pricing: https://azure.microsoft.com/en-gb/pricing/details/speech/
- Azure text to speech overview: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/text-to-speech
- Azure voice talent disclosure: https://learn.microsoft.com/en-us/azure/ai-foundry/responsible-ai/speech-service/text-to-speech/disclosure-voice-talent?view=foundry-classic
- Volcengine Doubao Speech product overview: https://www.volcengine.com/docs/6561/163032
- Volcengine speech synthesis product intro: https://www.volcengine.com/docs/6561/79817?lang=zh
- Volcengine Doubao Speech billing: https://www.volcengine.com/docs/6561/1359370
- Tencent Cloud TTS purchase guide PDF: https://main.qcloudimg.com/raw/document/product/pdf/1073_34112_cn.pdf
- Alibaba Cloud Intelligent Speech Interaction pricing: https://www.alibabacloud.com/help/zh/isi/product-overview/pricing
