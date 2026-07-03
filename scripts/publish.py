#!/usr/bin/env python3
"""Publish the next queued post to Instagram + Facebook via the Meta Graph API.

Reads the lowest-numbered folder in queue/, publishes it, then moves it to
posted/ (the workflow commits the move). Images are served to Meta as raw
GitHub URLs, so the repo must be public.

Required env vars:
    META_TOKEN    long-lived Page access token
    IG_USER_ID    Instagram Business account id
    FB_PAGE_ID    Facebook Page id
    GITHUB_REPOSITORY, GITHUB_SHA   (set automatically by Actions)

Optional:
    DRY_RUN=1     validate and print, publish nothing

post.json format:
    {
      "caption": "text with \n\n line breaks and #hashtags",
      "images": ["assets/LM_06584.jpg", "assets/DSCF3430.jpg"],
      "platforms": ["instagram", "facebook"]
    }
"""
import json
import os
import pathlib
import shutil
import sys
import time
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
GRAPH = "https://graph.facebook.com/v21.0"


def api(path: str, params: dict) -> dict:
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(f"{GRAPH}/{path}", data=data)
    try:
        body = urllib.request.urlopen(req, timeout=120).read()
    except urllib.error.HTTPError as e:
        sys.exit(f"Graph API error on /{path}: {e.read().decode()[:800]}")
    return json.loads(body)


def wait_ready(container_id: str, token: str, attempts: int = 20):
    """Poll a media container until Meta has finished processing it."""
    for _ in range(attempts):
        url = f"{GRAPH}/{container_id}?fields=status_code&access_token={urllib.parse.quote(token)}"
        status = json.loads(urllib.request.urlopen(url, timeout=60).read())
        code = status.get("status_code")
        if code == "FINISHED":
            return
        if code == "ERROR":
            sys.exit(f"Container {container_id} failed processing")
        time.sleep(3)
    sys.exit(f"Container {container_id} never finished processing")


def publish_instagram_reel(ig_id, token, caption, video_url):
    container = api(
        f"{ig_id}/media",
        {
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "share_to_feed": "true",
            "access_token": token,
        },
    )["id"]
    wait_ready(container, token, attempts=60)  # video processing takes a while
    result = api(f"{ig_id}/media_publish", {"creation_id": container, "access_token": token})
    print(f"Instagram: published reel {result['id']}")
    return result["id"]


def publish_facebook_video(page_id, token, caption, video_url):
    result = api(
        f"{page_id}/videos",
        {"file_url": video_url, "description": caption, "access_token": token},
    )
    print(f"Facebook: published video {result['id']}")
    return result["id"]


def publish_instagram(ig_id, token, caption, image_urls):
    if len(image_urls) == 1:
        container = api(
            f"{ig_id}/media",
            {"image_url": image_urls[0], "caption": caption, "access_token": token},
        )["id"]
    else:
        children = []
        for url in image_urls:
            child = api(
                f"{ig_id}/media",
                {"image_url": url, "is_carousel_item": "true", "access_token": token},
            )["id"]
            children.append(child)
        for child in children:
            wait_ready(child, token)
        container = api(
            f"{ig_id}/media",
            {
                "media_type": "CAROUSEL",
                "children": ",".join(children),
                "caption": caption,
                "access_token": token,
            },
        )["id"]
    wait_ready(container, token)
    result = api(f"{ig_id}/media_publish", {"creation_id": container, "access_token": token})
    print(f"Instagram: published media {result['id']}")
    return result["id"]


def publish_facebook(page_id, token, caption, image_urls):
    media = []
    for url in image_urls:
        photo = api(
            f"{page_id}/photos",
            {"url": url, "published": "false", "access_token": token},
        )["id"]
        media.append(photo)
    params = {"message": caption, "access_token": token}
    for i, photo_id in enumerate(media):
        params[f"attached_media[{i}]"] = json.dumps({"media_fbid": photo_id})
    result = api(f"{page_id}/feed", params)
    print(f"Facebook: published post {result['id']}")
    return result["id"]


def main():
    dry = os.environ.get("DRY_RUN") == "1"
    queue = sorted(p for p in (ROOT / "queue").iterdir() if p.is_dir())
    if not queue:
        print("Queue empty — nothing to publish. Refill queue/ !")
        return
    post_dir = queue[0]
    post = json.loads((post_dir / "post.json").read_text())
    caption = post["caption"].strip()
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    sha = os.environ.get("GITHUB_SHA", "main")

    def raw_url(rel):
        return f"https://raw.githubusercontent.com/{repo}/{sha}/{urllib.parse.quote(rel)}"

    video = post.get("video")
    media_rels = [video] if video else post["images"]
    for rel in media_rels:
        if not (ROOT / rel).exists():
            sys.exit(f"Missing media file: {rel}")
    media_urls = [raw_url(rel) for rel in media_rels]

    kind = "video" if video else f"{len(media_urls)} image(s)"
    print(f"Publishing {post_dir.name}: {kind}")
    if dry:
        print("[dry-run] caption:\n" + caption)
        print("[dry-run] urls:\n" + "\n".join(media_urls))
        return

    token = os.environ["META_TOKEN"]
    results = {}
    platforms = post.get("platforms", ["instagram", "facebook"])
    if "instagram" in platforms:
        if video:
            results["instagram"] = publish_instagram_reel(
                os.environ["IG_USER_ID"], token, caption, media_urls[0]
            )
        else:
            results["instagram"] = publish_instagram(
                os.environ["IG_USER_ID"], token, caption, media_urls
            )
    if "facebook" in platforms:
        if video:
            results["facebook"] = publish_facebook_video(
                os.environ["FB_PAGE_ID"], token, caption, media_urls[0]
            )
        else:
            results["facebook"] = publish_facebook(
                os.environ["FB_PAGE_ID"], token, caption, media_urls
            )

    post["published"] = {"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **results}
    (post_dir / "post.json").write_text(json.dumps(post, indent=2, ensure_ascii=False))
    dest = ROOT / "posted" / post_dir.name
    shutil.move(str(post_dir), str(dest))
    print(f"Moved {post_dir.name} -> posted/")


if __name__ == "__main__":
    main()
