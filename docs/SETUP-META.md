# Meta API setup — one-time, ~15 minutes

You need three values as GitHub secrets: `META_TOKEN`, `IG_USER_ID`, `FB_PAGE_ID`.

## 0. Prerequisites

Posts go to Instagram **@pettererik** and the Facebook Page (id `61577232899917`).

- **@pettererik must be a Professional account** (Creator or Business). If it's
  a personal account, the API cannot post to it. Convert in the Instagram app:
  Settings → Account type and tools → Switch to professional account.
  Followers, content and handle are unchanged; this only unlocks tools.
- **@pettererik must be linked to the Facebook Page** `61577232899917`.
  Check: Meta Business Suite → Settings → Linked accounts (or Instagram app →
  Edit profile → Page). Nothing below works without this link.

## 1. Create a Meta app

1. Go to <https://developers.facebook.com/apps> → **Create app**.
2. Use case: **Other** → type: **Business**. Name it `wildr-social`.
3. Connect it to the Wildr business portfolio when asked.

## 2. Get a long-lived Page token

1. Open the **Graph API Explorer**: <https://developers.facebook.com/tools/explorer>
2. Top right: select the `wildr-social` app.
3. Under **Permissions**, add:
   `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`,
   `instagram_basic`, `instagram_content_publish`, `business_management`
4. Click **Generate Access Token** → log in → choose the Wildr Page + Instagram account.
5. Copy the token, then make it long-lived: open (paste your values)

   ```
   https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token&client_id=APP_ID&client_secret=APP_SECRET&fb_exchange_token=SHORT_TOKEN
   ```

   (`APP_ID` and `APP_SECRET` are under App settings → Basic.)
6. With the long-lived token, get the **Page token** (this one doesn't expire):

   ```
   https://graph.facebook.com/v21.0/me/accounts?access_token=LONG_LIVED_TOKEN
   ```

   In the JSON, find the Wildr page → copy its `access_token` → this is `META_TOKEN`.
   The `id` field there is `FB_PAGE_ID` (should be 61577232899917).

## 3. Get the Instagram user id

Open:

```
https://graph.facebook.com/v21.0/61577232899917?fields=instagram_business_account&access_token=META_TOKEN
```

The `instagram_business_account.id` value is `IG_USER_ID`.

## 4. Add the secrets to GitHub

Repo → **Settings → Secrets and variables → Actions → New repository secret**,
or from the terminal:

```bash
gh secret set META_TOKEN --repo pettererik/wildr-social
gh secret set IG_USER_ID --repo pettererik/wildr-social
gh secret set FB_PAGE_ID --repo pettererik/wildr-social
```

## 5. Test

Actions → *Publish next social post* → **Run workflow** with *dry run* checked.
Green run = everything wired. Then run once without dry run to publish for real.

## Notes

- The app can stay in **Development mode** — publishing to a Page/IG account you
  admin works fine there; no App Review needed.
- If posting ever fails with an auth error, regenerate the token (steps 2–3)
  and update the `META_TOKEN` secret.
