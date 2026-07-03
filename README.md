# wildr-social

Automated Instagram + Facebook carousel posting for **Wildr Japan / Chase the Powder**.

Posts go out **Monday, Wednesday and Friday at 08:00 UTC** (18:00 AEST) via a
GitHub Action that publishes the next post in `queue/` through the Meta Graph API.

## How it works

```
Google Drive (ski photos)
      │  scripts/fetch_photos.py  (downloads + crops to 1080x1350)
      ▼
assets/  ──►  queue/001-first-tracks/post.json   (caption + image list)
      │       .github/workflows/publish.yml  (cron Mon/Wed/Fri)
      ▼
Instagram carousel + Facebook page post  ──►  posted/
```

- **`assets/`** — Instagram-ready 4:5 JPEGs (1080×1350), committed so Meta can
  fetch them as raw GitHub URLs. This repo must stay **public** for that reason —
  only put photos here you are happy to have public (they're going on Instagram anyway).
- **`queue/`** — pending posts, published in name order (`001-`, `002-`, …).
  Each folder holds one `post.json`.
- **`posted/`** — archive of published posts with Meta media ids and timestamps.

## post.json

```json
{
  "caption": "Some mornings you measure snowfall in metres...\n\nSend us a message if you want in next season.\n\n#japow #hokkaido #backcountryskiing",
  "images": ["assets/LM_06584.jpg", "assets/DSCF3430.jpg", "assets/LM_06426.jpg"],
  "platforms": ["instagram", "facebook"]
}
```

### Video posts (Reels)

A post can be a video instead of a carousel — published as an Instagram Reel
and a Facebook video:

```json
{
  "caption": "…",
  "video": "assets/video/asahi-dake-run.mp4",
  "images": [],
  "platforms": ["instagram", "facebook"]
}
```

Drop finished vertical clips (9:16, MP4, **under 95 MB** — GitHub raw-file limit)
into `assets/video/`. Edit them in CapCut/Canva first if needed; the publisher
takes them as-is.

## Refilling the queue

Content is generated in batches with the `wildr-social` Claude skill
(`~/.claude/skills/wildr-social/`): it picks unused photos from `assets/`,
writes captions in the Wildr voice, creates queue folders and pushes.
Review the batch on GitHub before Monday — that's the approval step.

## Manual controls

- **Test without posting:** Actions → *Publish next social post* → Run workflow → dry run ✔
- **Post right now:** same, with dry run unchecked.
- **Pause everything:** Actions tab → disable the workflow (or empty the queue).

## Secrets (repo → Settings → Secrets and variables → Actions)

| Secret       | What                                            |
| ------------ | ----------------------------------------------- |
| `META_TOKEN` | Long-lived **Page** access token                |
| `IG_USER_ID` | Instagram Business account id                   |
| `FB_PAGE_ID` | Facebook Page id (61577232899917)               |

Setup walkthrough: [docs/SETUP-META.md](docs/SETUP-META.md)
