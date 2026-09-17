# Modality-neutral jobs

GenJobs does not make “video generation” its core abstraction. A job represents
any long-running task, and a handler decides what a task name and payload mean.
The core uses `ContentKind` only to describe assets consistently:

| Kind | Typical inputs or outputs |
| --- | --- |
| `text` | prompt files, transcripts, summaries, generated documents |
| `image` | PNG/JPEG references, image-to-image results, image batches |
| `audio` | source audio, voice synthesis, music, sound effects |
| `video` | source clips, rendered scenes, final videos |
| `file` | model checkpoints, archives, PDFs, arbitrary binary files |
| `structured` | JSON-like metadata, evaluation scores, intermediate results |

## Cross-modal examples

```python
from genjobs_core import ContentKind, InputAsset, JobRequest

# Text-to-image
image_job = JobRequest(
    task="image.generate",
    payload={"prompt": "a lighthouse in mist", "width": 1024, "height": 1024},
)

# Image-and-text-to-video
video_job = JobRequest(
    task="video.animate",
    payload={"prompt": "slow orbiting camera", "seconds": 5},
    inputs=(InputAsset("s3://bucket/reference.png", ContentKind.IMAGE, "image/png"),),
)

# Audio-to-text
transcription_job = JobRequest(
    task="audio.transcribe",
    inputs=(InputAsset("s3://bucket/interview.wav", ContentKind.AUDIO, "audio/wav"),),
)
```

Task names use application-owned namespaces such as `text.generate`,
`image.upscale`, `audio.transcribe`, `video.render`, and `multimodal.caption`.
They are not a central registry, and GenJobs will not require a particular
model, provider, prompt format, or media library.

## What belongs outside core

Keep model-specific validation and conversion in separate packages. For
example, a `genjobs-diffusers` integration could validate image dimensions and
return generated images; a `genjobs-comfyui` integration could translate a
workflow graph; an audio adapter could validate sample rate. A user who only
needs text jobs should not install video codecs, PyTorch, or cloud SDKs.
