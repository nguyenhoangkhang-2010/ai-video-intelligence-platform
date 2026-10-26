# 0006 - Short-lived, resource-scoped media tokens instead of the main access token in URLs

## Status
Accepted (implemented: `app/auth/jwt.py::create_media_token`, `app/auth/dependencies.py::get_current_user_for_media`, `GET /videos/{video_id}/media-token`).

## Context
`<video>`/`<img>` elements can't attach an `Authorization` header, so
video streaming/thumbnail URLs need some other way to authenticate.
The previous approach put the user's main, long-lived (60-minute)
access token directly in the URL as `?token=...` - the same token
used for every other authenticated API call. That token then lives
anywhere the URL does: browser history, `Referer` headers sent to
other origins, server access logs, screen recordings of the page.

## Decision
Mint a separate, purpose-built token (`create_media_token`) carrying
`scope="media"` and the exact `video_id` it's valid for, with a short
default lifetime (`settings.security.media_token_expire_seconds`,
300s) - via a new `GET /videos/{video_id}/media-token` endpoint
(normal `Authorization`-header auth, ownership-checked). The media
endpoints' query-token path (`get_current_user_for_media`) now
requires this token specifically: a token missing `scope="media"`, or
scoped to a different `video_id`, or expired, is rejected (401/403).
The main access token is explicitly rejected on this path (it never
worked here even before this token existed in spirit, but is now
enforced, not just assumed).

## Consequences
- A leaked/logged media URL exposes a credential that's worthless
  after 5 minutes and useless for anything except viewing one
  specific video - never full account access.
- One extra request (fetch a media token before building the
  stream/thumbnail URL) per video shown, instead of reusing an
  already-held token. For a single video page this is negligible; for
  a grid of many thumbnails at once, this is N parallel token
  requests on page load (see `useMediaToken`, `VideoThumbnail.tsx`) -
  acceptable at current video-library sizes, worth revisiting (e.g. a
  batch "tokens for these video ids" endpoint) if a library view ever
  needs to render hundreds of thumbnails at once.
- The `Authorization`-header path for `/stream`/`/thumbnail` is
  unchanged - this only closes the query-parameter fallback, which is
  the one a browser media element actually has to use.
