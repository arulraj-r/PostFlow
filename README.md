# PostFlow

PostFlow is a Python-based social media automation workflow that selects media from Dropbox, generates captions with Groq AI, publishes the selected content to multiple social platforms, verifies the result, retries temporary failures, and moves failed files into platform-specific Dropbox folders.

The current project supports:

- Facebook
- Instagram
- Threads
- Telegram
- Discord
- Tumblr

It can process:

- Images
- Videos
- Text files (`.txt`)

PostFlow can be run locally with Python or automatically through GitHub Actions.

---

## Table of Contents

1. [What PostFlow Does](#what-postflow-does)
2. [How the Workflow Works](#how-the-workflow-works)
3. [Project Structure](#project-structure)
4. [Requirements](#requirements)
5. [Clone the Repository](#clone-the-repository)
6. [Local Python Setup](#local-python-setup)
7. [Install Dependencies](#install-dependencies)
8. [Environment Variables](#environment-variables)
9. [Dropbox Setup](#dropbox-setup)
10. [Groq AI Setup](#groq-ai-setup)
11. [Facebook Setup](#facebook-setup)
12. [Instagram Setup](#instagram-setup)
13. [Threads Setup](#threads-setup)
14. [Telegram Setup](#telegram-setup)
15. [Discord Setup](#discord-setup)
16. [Tumblr Setup](#tumblr-setup)
17. [Configure `config.json`](#configure-configjson)
18. [Local `.env` Setup](#local-env-setup)
19. [Run PostFlow Locally](#run-postflow-locally)
20. [How Media Selection Works](#how-media-selection-works)
21. [How Captions Are Generated](#how-captions-are-generated)
22. [How Each Platform Receives Media](#how-each-platform-receives-media)
23. [Retry and Error Handling](#retry-and-error-handling)
24. [Failed Files](#failed-files)
25. [GitHub Actions Setup](#github-actions-setup)
26. [GitHub Secrets](#github-secrets)
27. [Running GitHub Actions Manually](#running-github-actions-manually)
28. [Automatic Scheduling](#automatic-scheduling)
29. [Understanding the Logs](#understanding-the-logs)
30. [Changing Posting Frequency](#changing-posting-frequency)
31. [Changing the Image/Video/Text Ratio](#changing-the-imagevideotext-ratio)
32. [Changing Caption Settings](#changing-caption-settings)
33. [Disabling a Platform](#disabling-a-platform)
34. [Troubleshooting](#troubleshooting)
35. [Security](#security)
36. [Important API Notes](#important-api-notes)
37. [Common Questions](#common-questions)
38. [Typical Production Workflow](#typical-production-workflow)
39. [License](#license)

---

# What PostFlow Does

PostFlow is designed around a simple idea:

> Put content into Dropbox, run the workflow, and let PostFlow publish the content to the enabled platforms.

A normal run looks like this:

```text
Dropbox /instagram
        |
        v
Find valid files
        |
        v
Randomly select image/video/text
        |
        v
Download selected file
        |
        +----------------------+
        |                      |
        v                      v
    Text file             Image / Video
        |                      |
        |                      v
        |                Generate AI caption
        |                      |
        +----------+-----------+
                   |
                   v
          Verify media size
                   |
                   v
        Publish to each platform
                   |
                   v
        Retry temporary failures
                   |
          +--------+--------+
          |                 |
       Success            Failure
          |                 |
          v                 v
Delete from Dropbox   /failed/<platform>
          |
          v
     Final summary
```

PostFlow processes **one selected file per execution**.

That means one scheduled GitHub Actions run normally consumes one image, one video, or one text file.

---

# How the Workflow Works

The main workflow is implemented in `main.py`.

## Step 1 — Load configuration

PostFlow reads:

```text
config.json
```

This controls:

- enabled platforms
- caption limits
- Dropbox folders
- retry settings
- posting delay
- Instagram processing settings
- Threads settings
- fixed hashtag

---

## Step 2 — Connect to Dropbox

PostFlow uses:

```text
DROPBOX_APP_KEY
DROPBOX_APP_SECRET
DROPBOX_REFRESH_TOKEN
```

The Dropbox folder configured in `config.json` is scanned.

Default:

```json
"folder": "/instagram"
```

---

## Step 3 — Find supported files

Supported image extensions:

```text
.jpg
.jpeg
.png
.webp
```

Supported video extensions:

```text
.mp4
.mov
.m4v
.avi
.mkv
.webm
```

Supported text extension:

```text
.txt
```

Unsupported files are not posted.

---

## Step 4 — Select one file

PostFlow separates available files into:

```text
Images
Videos
Text files
```

The current selection weights are:

```text
Image = 20
Video = 60
Text  = 20
```

These are weights, not guarantees.

For example, a 60% video weight does not mean exactly six videos will be selected in every ten runs. It means the random selection favors videos.

---

## Step 5 — Download the selected file

The selected Dropbox file is downloaded temporarily to the GitHub Actions runner or local machine.

The temporary file is removed after processing.

---

## Step 6 — Generate a caption

For images and videos, PostFlow sends the filename to Groq.

The current model configured in the code is:

```text
openai/gpt-oss-20b
```

The filename is converted into a human-readable topic.

Example:

```text
sunset_beach_walk.mp4
```

becomes approximately:

```text
sunset beach walk
```

The AI is asked to generate a social media caption and relevant hashtags.

---

## Step 7 — Create a public media URL when required

Instagram and Threads do not receive the local file directly in this implementation.

For image/video posts, PostFlow creates or reuses a Dropbox shared link and converts it into a direct/raw URL.

That public URL is passed to the APIs that require externally accessible media.

This is especially important for Instagram and Threads.

---

## Step 8 — Verify file size

Before publishing media, PostFlow checks the configured platform-specific size limit.

If the file is too large for a platform:

```text
That platform is skipped
```

The workflow does not needlessly send the oversized file to that API.

---

## Step 9 — Publish

The enabled platforms are processed one by one.

A delay is placed between platform attempts.

Default:

```json
"post_delay": 10
```

So PostFlow waits approximately 10 seconds between platform operations.

---

## Step 10 — Retry temporary errors

Temporary errors such as:

```text
429
500
502
503
504
timeouts
connection resets
rate limits
```

can be retried.

Permanent errors are not blindly retried.

---

## Step 11 — Handle the file

### If every enabled platform succeeds

The original Dropbox file is deleted.

### If one or more platforms fail

The original file is copied into:

```text
/failed/<platform>/
```

for each failed platform and then removed from the original inbox.

Example:

```text
/failed/instagram/video.mp4
/failed/threads/video.mp4
```

This makes it possible to identify which platform failed.

---

# Project Structure

```text
PostFlow/
│
├── .github/
│   └── workflows/
│       └── main.yml
│
├── core/
│   ├── error_classifier.py
│   ├── retry_manager.py
│   └── verifier.py
│
├── modules/
│   ├── __init__.py
│   ├── caption_generator.py
│   ├── dropbox_handler.py
│   └── utils.py
│
├── platforms/
│   ├── __init__.py
│   ├── discord.py
│   ├── facebook.py
│   ├── instagram.py
│   ├── telegram.py
│   ├── threads.py
│   └── tumblr.py
│
├── config.json
├── main.py
└── README.md
```

---

# Requirements

You need:

- Python 3.12 recommended
- Git
- A Dropbox developer application
- A Groq API key
- Credentials for every social platform you want to enable
- A GitHub repository if you want scheduled execution through GitHub Actions

You do **not** need FFmpeg for the current repository.

The current code does not perform video/audio transcoding. It uploads or references the original media file.

---

# Clone the Repository

Open a terminal.

```bash
git clone https://github.com/YOUR_USERNAME/PostFlow.git
```

Enter the repository:

```bash
cd PostFlow
```

If your repository has a different name, replace `PostFlow` with your actual repository directory.

---

# Local Python Setup

## Windows

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can use:

```powershell
.venv\Scripts\activate.bat
```

or run the Python executable directly without activating the environment.

---

## macOS / Linux

```bash
python3 -m venv .venv
```

Activate:

```bash
source .venv/bin/activate
```

---

# Install Dependencies

The GitHub Actions workflow currently installs:

```text
python-dotenv
requests
dropbox
groq
pytumblr
urllib3
```

For local use, install them with:

```bash
python -m pip install --upgrade pip
pip install python-dotenv requests dropbox groq pytumblr urllib3
```

You can verify the important packages:

```bash
pip show requests
pip show dropbox
pip show groq
pip show pytumblr
pip show python-dotenv
```

---

# Environment Variables

PostFlow reads credentials from environment variables.

The complete set used by the current GitHub Actions workflow is:

```text
DROPBOX_APP_KEY
DROPBOX_APP_SECRET
DROPBOX_REFRESH_TOKEN

GROQ_API_KEY

FB_PAGE_ID
META_TOKEN

IG_ID

THREADS_USER_ID
THREADS_ACCESS_TOKEN

TELEGRAM_POST_BOT_TOKEN
TELEGRAM_POST_CHAT_ID

TELEGRAM_LOG_BOT_TOKEN
TELEGRAM_LOG_CHAT_ID

DISCORD_BOT_TOKEN
DISCORD_CHANNEL_ID

TUMBLR_BLOG_NAME
TUMBLR_CONSUMER_KEY
TUMBLR_CONSUMER_SECRET
TUMBLR_OAUTH_TOKEN
TUMBLR_OAUTH_TOKEN_SECRET
```

Not every variable is necessarily required for every platform.

For example, if you only enable Facebook and Telegram, you still need to make sure the platform constructors used by your configuration have the credentials they require.

---

# Dropbox Setup

Dropbox is the content source for PostFlow.

## 1. Create a Dropbox App

Go to the Dropbox developer console and create an application.

Choose an appropriate Dropbox API access type.

The application needs permission to:

- list files
- download files
- create/read shared links
- copy files
- delete files
- create folders

The exact Dropbox permission names may change in the Dropbox developer dashboard, so always use the current permission labels shown there.

---

## 2. Generate a refresh token

PostFlow uses:

```text
DROPBOX_REFRESH_TOKEN
```

A refresh token is preferable for unattended automation because the workflow can obtain access without requiring you to manually paste a short-lived access token every time.

Follow Dropbox's current OAuth flow to generate the refresh token.

Store:

```text
DROPBOX_APP_KEY
DROPBOX_APP_SECRET
DROPBOX_REFRESH_TOKEN
```

as secrets.

---

## 3. Create the content folder

The default configuration expects:

```text
/instagram
```

Create that folder in Dropbox.

Put your media inside it.

Example:

```text
/instagram
    beach.mp4
    sunset.jpg
    morning.txt
    city_walk.mp4
```

---

## 4. Failed folder

The default failed folder is:

```text
/failed
```

You do not have to create it manually.

PostFlow can create:

```text
/failed
/failed/facebook
/failed/instagram
/failed/threads
/failed/telegram
/failed/tumblr
/failed/discord
```

when necessary.

---

# Groq AI Setup

PostFlow uses Groq for caption generation.

Create an API key in your Groq account.

Store it as:

```text
GROQ_API_KEY
```

The current caption generator uses:

```text
openai/gpt-oss-20b
```

If that model is unavailable in your Groq account or the provider changes its model availability, update:

```text
modules/caption_generator.py
```

and replace the model name with a currently supported model.

---

# Facebook Setup

PostFlow uses the Facebook Graph API for Facebook publishing.

The current code expects:

```text
FB_PAGE_ID
META_TOKEN
```

`META_TOKEN` is used for Meta API requests.

You need a Facebook Page and a Meta developer application with the permissions required by the current Graph API for the operations you intend to perform.

At minimum, your token must be authorized for the Page and the publishing operations.

The exact Meta permission names and approval requirements can change. Check the current Meta developer documentation before deploying.

---

## Find the Page ID

Use your Meta/Facebook developer setup or Page API tooling to obtain the Page ID.

Store it as:

```text
FB_PAGE_ID
```

---

## Generate the token

Generate a token that has the required Page permissions.

Store it as:

```text
META_TOKEN
```

Do not commit the token to Git.

---

# Instagram Setup

The current implementation uses the Instagram Graph API and expects:

```text
IG_ID
META_TOKEN
```

The Instagram account must be eligible for the API workflow being used by your Meta application.

The current code publishes:

- images as Instagram image posts
- videos as Instagram Reels

The code creates a media container first and then publishes it.

For video publishing:

```text
Create container
      |
      v
Wait for processing
      |
      v
Check status
      |
      v
Publish container
```

This is why Instagram video posting can take longer than an image post.

---

## Important Instagram requirement

Instagram media URLs must be reachable by Instagram's servers.

A local path such as:

```text
C:\videos\test.mp4
```

will not work.

The current PostFlow implementation uses Dropbox shared URLs for this purpose.

---

## Instagram environment variables

Set:

```text
IG_ID
META_TOKEN
```

The Instagram Graph API version is configured in:

```json
"instagram_graph_version": "v18.0"
```

If Meta no longer supports that API version, update the value and the associated endpoint assumptions in `platforms/instagram.py` and `platforms/facebook.py`.

---

# Threads Setup

The current Threads implementation uses:

```text
THREADS_USER_ID
THREADS_ACCESS_TOKEN
```

The API host in the current code is:

```text
https://graph.threads.net/v1.0
```

Threads image/video posts also use publicly accessible media URLs.

The workflow is:

```text
Create Threads container
        |
        v
Wait for processing
        |
        v
Publish container
        |
        v
Verify published thread
```

---

## Threads configuration

Current settings include:

```json
"threads_auto_publish_text": true,
"threads_reply_control": "everyone",
"threads_enable_reply_approvals": false
```

Valid reply controls in the code are:

```text
everyone
accounts_you_follow
mentioned_only
```

---

# Telegram Setup

Create a Telegram bot using BotFather.

Obtain the bot token.

Store it as:

```text
TELEGRAM_POST_BOT_TOKEN
```

Then determine the destination chat/channel/group ID and store:

```text
TELEGRAM_POST_CHAT_ID
```

The bot must have sufficient permissions to post to the target destination.

Telegram publishing methods include:

```text
sendMessage
sendPhoto
sendVideo
```

The current code also has retry handling for common server errors.

---

# Discord Setup

Create a Discord application/bot.

Invite the bot to your server with permission to send messages and upload files in the target channel.

Store:

```text
DISCORD_BOT_TOKEN
DISCORD_CHANNEL_ID
```

Discord publishing uses the channel messages endpoint.

Images and videos are uploaded as message attachments.

The caption is sent as the message content.

---

# Tumblr Setup

Create a Tumblr application and complete the OAuth flow.

PostFlow expects:

```text
TUMBLR_BLOG_NAME
TUMBLR_CONSUMER_KEY
TUMBLR_CONSUMER_SECRET
TUMBLR_OAUTH_TOKEN
TUMBLR_OAUTH_TOKEN_SECRET
```

Tumblr uses the `pytumblr` package.

The Tumblr implementation can publish:

- photos
- videos
- text

For image/video posts, the original local file is passed to the Tumblr client.

---

# Configure `config.json`

The default configuration is:

```json
{
  "platforms": {
    "facebook": {
      "limit": 3000,
      "enable_text_posts": true
    },
    "instagram": {
      "limit": 2200,
      "enable_text_posts": false
    },
    "telegram": {
      "limit": 1024,
      "enable_text_posts": true
    },
    "threads": {
      "limit": 500,
      "enable_text_posts": true
    },
    "tumblr": {
      "limit": 2000,
      "enable_text_posts": true
    },
    "discord": {
      "limit": 2000,
      "enable_text_posts": true
    }
  },
  "dropbox": {
    "folder": "/instagram",
    "failed_folder": "/failed"
  },
  "settings": {
    "post_delay": 10,
    "retry_count": 3,
    "retry_delay": 20,
    "poll_interval": 20,
    "poll_attempts": 3,
    "instagram_graph_version": "v18.0",
    "instagram_processing_wait_seconds": 10,
    "instagram_processing_max_attempts": 30,
    "instagram_publish_delay_seconds": 15,
    "fixed_hashtag": "#arul9x",
    "threads_auto_publish_text": true,
    "threads_reply_control": "everyone",
    "threads_enable_reply_approvals": false
  }
}
```

---

# Understanding Platform Limits

The `limit` value controls caption/text length in `main.py`.

It is not the same thing as the platform's media file-size limit.

For example:

```json
"instagram": {
  "limit": 2200
}
```

means the generated caption is trimmed to 2200 characters.

Media size is handled separately by:

```text
core/verifier.py
```

---

# Local `.env` Setup

For local testing, create:

```text
.env
```

in the repository root.

Example:

```env
DROPBOX_APP_KEY=your_dropbox_app_key
DROPBOX_APP_SECRET=your_dropbox_app_secret
DROPBOX_REFRESH_TOKEN=your_dropbox_refresh_token

GROQ_API_KEY=your_groq_api_key

FB_PAGE_ID=your_facebook_page_id
META_TOKEN=your_meta_access_token

IG_ID=your_instagram_user_id

THREADS_USER_ID=your_threads_user_id
THREADS_ACCESS_TOKEN=your_threads_access_token

TELEGRAM_POST_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_POST_CHAT_ID=your_telegram_chat_id

TELEGRAM_LOG_BOT_TOKEN=your_telegram_log_bot_token
TELEGRAM_LOG_CHAT_ID=your_telegram_log_chat_id

DISCORD_BOT_TOKEN=your_discord_bot_token
DISCORD_CHANNEL_ID=your_discord_channel_id

TUMBLR_BLOG_NAME=your_blog_name
TUMBLR_CONSUMER_KEY=your_consumer_key
TUMBLR_CONSUMER_SECRET=your_consumer_secret
TUMBLR_OAUTH_TOKEN=your_oauth_token
TUMBLR_OAUTH_TOKEN_SECRET=your_oauth_token_secret
```

---

## Important: Load `.env`

The project installs `python-dotenv`, but the current `main.py` does not explicitly call `load_dotenv()`.

If you want `.env` to work automatically for local execution, add this near the beginning of `main.py`:

```python
from dotenv import load_dotenv

load_dotenv()
```

Without this, setting values in `.env` alone may not populate `os.getenv()`.

Alternatively, export the environment variables directly in your shell before running the program.

---

# Never Commit `.env`

Add this to `.gitignore`:

```gitignore
.env
.venv/
__pycache__/
*.pyc
temp_*
```

Never commit:

```text
.env
API keys
OAuth secrets
access tokens
bot tokens
client secrets
refresh tokens
```

---

# Run PostFlow Locally

After installing dependencies and configuring environment variables:

```bash
python main.py
```

On some systems:

```bash
python3 main.py
```

---

## What should happen

A successful run should roughly look like:

```text
UNIVERSAL ROTATING WORKFLOW STARTED
Dropbox client initialized
Selected video: example.mp4
Processing FILE -> example.mp4
INSTAGRAM starting publish
Instagram poll attempt 1/30: IN_PROGRESS
Instagram poll attempt 2/30: FINISHED
INSTAGRAM success
FACEBOOK starting publish
FACEBOOK success
...
Dropbox file deleted (all targets success)
UNIVERSAL WORKFLOW FINAL SUMMARY
```

The exact log output will vary.

---

# Test With One File First

Before enabling all six platforms, test with one simple file.

Recommended first test:

```text
test.jpg
```

Put it in:

```text
/instagram
```

Enable only one platform in `config.json`.

Run:

```bash
python main.py
```

Confirm that:

1. Dropbox can be accessed.
2. The file is selected.
3. The caption is generated.
4. The platform receives the post.
5. The file is deleted after successful processing.

Then add the next platform.

This makes authentication/API problems much easier to identify.

---

# How Media Selection Works

The selection logic is in:

```text
modules/dropbox_handler.py
```

The current weights are:

```python
types = ["image", "video", "text"]
weights = [20, 60, 20]
```

That means:

```text
Image 20%
Video 60%
Text  20%
```

approximately over a sufficiently large number of random selections.

---

## Important fallback behavior

Suppose the random selection chooses:

```text
video
```

but there are no videos in Dropbox.

PostFlow falls back to another available type.

For example:

```text
Images: 10
Videos: 0
Text: 2
```

If video is randomly selected, PostFlow chooses from:

```text
images or text
```

instead.

---

# How Captions Are Generated

Caption generation is handled by:

```text
modules/caption_generator.py
```

For a video, the prompt asks for:

```text
An engaging storytelling caption
Maximum 150 words
4 relevant hashtags
```

For an image:

```text
A short punchy caption
Maximum 100 words
3 relevant hashtags
```

The fixed brand hashtag is configured separately.

Current value:

```text
#arul9x
```

---

# Hashtag Formatting

The generated response is split into:

```text
Caption text
Hashtags
```

Then `main.py` formats the result for each platform.

The platform-specific hashtag limits are defined in `main.py`.

The final caption also receives the configured fixed hashtag.

---

# Text Files

If the selected file is:

```text
something.txt
```

PostFlow reads the text directly.

AI caption generation is not used for the text content.

The contents of the file become the post text.

Each platform can independently enable or disable text posting.

---

# Instagram Text Posts

Instagram does not support a text-only post through this workflow.

The Instagram implementation therefore returns:

```text
SKIPPED
```

for text-only publishing.

That is why the default configuration has:

```json
"enable_text_posts": false
```

for Instagram.

---

# How Each Platform Receives Media

## Facebook

Local file upload.

```text
Dropbox
   |
   v
Local temporary file
   |
   v
Facebook API
```

---

## Instagram

Public URL.

```text
Dropbox
   |
   v
Shared/direct media URL
   |
   v
Instagram media container
   |
   v
Publish
```

Videos require processing-status polling before publishing.

---

## Threads

Public URL.

```text
Dropbox
   |
   v
Shared/direct media URL
   |
   v
Threads container
   |
   v
Wait for processing
   |
   v
Publish
```

---

## Telegram

Local file upload.

```text
Local file
   |
   +--> sendPhoto
   |
   +--> sendVideo
```

---

## Discord

Local attachment upload.

```text
Local file
   |
   v
Discord message attachment
```

---

## Tumblr

Local file upload through `pytumblr`.

---

# Retry and Error Handling

The retry system is implemented in:

```text
core/retry_manager.py
```

and:

```text
core/error_classifier.py
```

---

## Temporary errors

Typical retry conditions include:

```text
429
500
502
503
504
timeout
connection reset
rate limit
try again
```

These may be retried.

---

## Authentication errors

Typical authentication signals:

```text
401
unauthorized
expired
token invalid
```

The workflow does not automatically refresh your social platform credentials.

It stops and logs that the token needs attention.

You should update the relevant secret/token and run the workflow again.

---

## Media errors

Typical media problems include:

```text
413
415
422
payload too large
unsupported media
aspect ratio
invalid format
media download has failed
failed_downloading_video
failed_processing_video
```

These are classified as:

```text
SKIP
```

rather than repeatedly retrying the same invalid media.

---

## Permanent errors

Typical permanent API errors:

```text
400
403
404
405
forbidden
```

These are treated as:

```text
STOP
```

because retrying the same request usually does not fix a configuration or permission problem.

---

# Failed Files

When a platform fails while other platforms succeed, PostFlow preserves the file for that platform.

Example:

```text
/failed/instagram/example.mp4
```

If both Instagram and Threads fail:

```text
/failed/instagram/example.mp4
/failed/threads/example.mp4
```

This is useful because you can troubleshoot each platform independently.

---

# What Happens to the Original File?

## All platforms succeed

Original file:

```text
/instagram/example.mp4
```

is deleted.

---

## One or more platforms fail

The file is copied to each failed platform folder.

Then the original inbox file is deleted.

This prevents the same file from being automatically selected again from the main inbox.

---

# GitHub Actions Setup

The repository already contains:

```text
.github/workflows/main.yml
```

The workflow:

1. Checks out the repository.
2. Installs Python 3.12.
3. Installs dependencies.
4. Loads GitHub Secrets into environment variables.
5. Runs:

```bash
python main.py
```

---

# GitHub Secrets

Go to:

```text
GitHub repository
    >
Settings
    >
Secrets and variables
    >
Actions
```

Create repository secrets with these exact names.

## Dropbox

```text
DROPBOX_APP_KEY
DROPBOX_APP_SECRET
DROPBOX_REFRESH_TOKEN
```

## Groq

```text
GROQ_API_KEY
```

## Meta

```text
FB_PAGE_ID
META_TOKEN
IG_ID
```

## Threads

```text
THREADS_USER_ID
THREADS_ACCESS_TOKEN
```

## Telegram

```text
TELEGRAM_POST_BOT_TOKEN
TELEGRAM_POST_CHAT_ID
TELEGRAM_LOG_BOT_TOKEN
TELEGRAM_LOG_CHAT_ID
```

## Discord

```text
DISCORD_BOT_TOKEN
DISCORD_CHANNEL_ID
```

## Tumblr

```text
TUMBLR_BLOG_NAME
TUMBLR_CONSUMER_KEY
TUMBLR_CONSUMER_SECRET
TUMBLR_OAUTH_TOKEN
TUMBLR_OAUTH_TOKEN_SECRET
```

The names must match the workflow exactly.

A typo such as:

```text
META_ACCESS_TOKEN
```

instead of:

```text
META_TOKEN
```

will cause the application to see a missing token.

---

# GitHub Actions Workflow

The workflow is:

```text
.github/workflows/main.yml
```

It uses:

```yaml
python-version: "3.12"
```

and installs:

```text
python-dotenv
requests
dropbox
groq
pytumblr
urllib3
```

Then it runs:

```bash
python main.py
```

---

# Running GitHub Actions Manually

Go to:

```text
GitHub
    >
Your repository
    >
Actions
    >
Social Auto Runner
```

Click:

```text
Run workflow
```

Then start the workflow.

This is the best way to perform the first production test.

---

# Automatic Scheduling

The current workflow contains multiple cron schedules.

Important:

> GitHub Actions cron schedules use UTC.

The current schedule contains runs at:

```text
00:00 UTC
01:12 UTC
02:24 UTC
03:36 UTC
04:48 UTC
06:00 UTC
07:12 UTC
08:24 UTC
09:36 UTC
10:48 UTC
12:00 UTC
13:12 UTC
14:24 UTC
15:36 UTC
16:48 UTC
18:00 UTC
19:12 UTC
20:24 UTC
21:36 UTC
22:48 UTC
```

For India Standard Time (IST, UTC+5:30), these correspond approximately to:

```text
05:30
06:42
07:54
09:06
10:18
11:30
12:42
13:54
15:06
16:18
17:30
18:42
19:54
21:06
22:18
23:30
00:42
01:54
03:06
04:18
```

The UTC date boundary means some of the later IST times occur on the following calendar day.

GitHub Actions scheduled jobs are not guaranteed to execute at the exact second specified by cron. GitHub may delay scheduled workflow runs, especially during periods of high load.

---

# Important Scheduling Behavior

There are 20 scheduled triggers in the current workflow.

Each execution processes:

```text
ONE FILE
```

Therefore, if you have 100 files in Dropbox, 20 scheduled runs per day can consume roughly 20 files per day, assuming every run succeeds and a valid file is available.

The actual number can be lower because of:

- failed API calls
- skipped files
- invalid media
- missing credentials
- GitHub Actions delays
- no files available
- API rate limits

---

# Changing Posting Frequency

Edit:

```text
.github/workflows/main.yml
```

Find:

```yaml
on:
  schedule:
```

Each line is a cron schedule.

For example:

```yaml
- cron: "0 0 * * *"
```

means:

```text
00:00 UTC every day
```

To run once per day:

```yaml
on:
  schedule:
    - cron: "0 0 * * *"
```

To run every 6 hours:

```yaml
on:
  schedule:
    - cron: "0 */6 * * *"
```

Remember that GitHub Actions uses UTC.

---

# Changing the Image/Video/Text Ratio

Open:

```text
modules/dropbox_handler.py
```

Find:

```python
types = ["image", "video", "text"]
weights = [20, 60, 20]
```

For example, to favor images:

```python
types = ["image", "video", "text"]
weights = [60, 20, 20]
```

For mostly videos:

```python
types = ["image", "video", "text"]
weights = [10, 80, 10]
```

For equal weighting:

```python
types = ["image", "video", "text"]
weights = [1, 1, 1]
```

The numbers do not have to add up to 100.

They are relative weights.

---

# Changing Caption Settings

Open:

```text
modules/caption_generator.py
```

Current hashtag counts:

```python
tag_counts = {
    "video": 4,
    "image": 3
}
```

You can change them.

Example:

```python
tag_counts = {
    "video": 5,
    "image": 4
}
```

---

## Change the fixed hashtag

Open:

```text
config.json
```

Change:

```json
"fixed_hashtag": "#arul9x"
```

For example:

```json
"fixed_hashtag": "#MyBrand"
```

---

# Disabling a Platform

The current configuration treats platforms listed under:

```json
"platforms"
```

as enabled.

If you do not want a platform to run, remove its entry from `config.json`.

For example, to disable Tumblr, remove:

```json
"tumblr": {
  "limit": 2000,
  "enable_text_posts": true
}
```

The mapping in `main.py` determines the supported platform names:

```text
facebook
instagram
threads
telegram
discord
tumblr
```

---

# Caption Length Configuration

Example:

```json
"facebook": {
  "limit": 3000,
  "enable_text_posts": true
}
```

The `limit` controls the final caption/text length used by PostFlow.

Examples:

```text
Facebook: 3000
Instagram: 2200
Telegram: 1024
Threads: 500
Tumblr: 2000
Discord: 2000
```

These are project configuration values and should be reviewed against the current platform API rules if platform limits change.

---

# Posting Delay

In `config.json`:

```json
"post_delay": 10
```

This means PostFlow waits 10 seconds between platform operations.

To use 30 seconds:

```json
"post_delay": 30
```

---

# Retry Settings

Current values:

```json
"retry_count": 3,
"retry_delay": 20
```

This means the retry manager can make up to three attempts for retryable failures.

The default retry delay is 20 seconds.

Some platform classes also have their own polling intervals.

---

# Instagram Processing Settings

The current configuration contains:

```json
"instagram_processing_wait_seconds": 10,
"instagram_processing_max_attempts": 30,
"instagram_publish_delay_seconds": 15
```

Conceptually:

```text
Check Instagram processing status
        |
        v
Wait 10 seconds
        |
        v
Check again
        |
        v
Maximum 30 attempts
```

After the video reports:

```text
FINISHED
```

the workflow waits the configured publish delay before publishing.

---

# Media Verification

Media-size verification is in:

```text
core/verifier.py
```

The project currently contains these configured values:

```text
Discord:
    image 10 MB
    video 10 MB

Facebook:
    image 30 MB
    video 1024 MB

Instagram:
    image 30 MB
    video 1024 MB

Telegram:
    image 10 MB
    video 50 MB

Threads:
    image 8 MB
    video 1024 MB

Tumblr:
    image 10 MB
    video 100 MB
```

These values are project-level conservative checks.

They should not be treated as permanent official API limits. Platform limits can change, and different upload/API products can have different restrictions.

If the API rejects a file despite the verifier allowing it, review the current platform requirements and update `core/verifier.py`.

---

# Troubleshooting

## 1. `Missing Instagram credentials`

Check:

```text
IG_ID
META_TOKEN
```

Make sure the variable names are exact.

---

## 2. `Missing Telegram Credentials`

Check:

```text
TELEGRAM_POST_BOT_TOKEN
TELEGRAM_POST_CHAT_ID
```

---

## 3. `Missing Discord Credentials`

Check:

```text
DISCORD_BOT_TOKEN
DISCORD_CHANNEL_ID
```

---

## 4. Groq caption generation fails

Check:

```text
GROQ_API_KEY
```

Also verify that the model configured in:

```text
modules/caption_generator.py
```

is currently available.

The code has a fallback caption if AI generation fails.

---

## 5. Dropbox says no valid files

Check:

```text
config.json
```

Make sure:

```json
"folder": "/instagram"
```

matches your actual Dropbox folder.

Then check that the folder contains one of the supported extensions.

---

## 6. Instagram says media cannot be fetched

This usually means Instagram cannot download the supplied media URL.

Check:

1. Dropbox shared link exists.
2. The link is publicly accessible.
3. The link points directly to the media.
4. The file has not been deleted.
5. The media format is supported.
6. The URL is not returning an HTML page instead of the media.
7. The media is not too large.
8. The Meta API version and endpoint behavior are still supported.

The relevant code is:

```text
modules/dropbox_handler.py
platforms/instagram.py
```

---

## 7. Instagram video stays in processing

The video may be rejected or may take longer than the configured polling window.

Check:

```text
instagram_processing_wait_seconds
instagram_processing_max_attempts
```

Also inspect the API response and verify the video's codec, dimensions, duration, and file size against the current Instagram requirements.

---

## 8. Threads media fails

Check:

```text
THREADS_ACCESS_TOKEN
THREADS_USER_ID
```

Then check whether the Dropbox media URL can be fetched publicly.

Threads image/video publishing requires the platform to retrieve the media from the URL.

---

## 9. Facebook returns 401

Your Meta token is invalid, expired, revoked, or lacks the required permissions.

Replace:

```text
META_TOKEN
```

with a valid token and run the workflow again.

---

## 10. Facebook returns 403

This is normally a permissions/access problem.

Check:

- Page access
- Meta app permissions
- token permissions
- Page ID
- app mode
- current Graph API requirements

---

## 11. Telegram does not post

Check:

```text
TELEGRAM_POST_BOT_TOKEN
TELEGRAM_POST_CHAT_ID
```

Also verify the bot is allowed to send messages to the destination.

---

## 12. Discord does not post

Check:

```text
DISCORD_BOT_TOKEN
DISCORD_CHANNEL_ID
```

Verify that the bot has permission to:

```text
View Channel
Send Messages
Attach Files
```

where required.

---

## 13. Tumblr authentication fails

Check all five Tumblr credentials:

```text
TUMBLR_CONSUMER_KEY
TUMBLR_CONSUMER_SECRET
TUMBLR_OAUTH_TOKEN
TUMBLR_OAUTH_TOKEN_SECRET
TUMBLR_BLOG_NAME
```

Make sure the blog name matches the Tumblr blog being authenticated.

---

# Reading the Final Summary

At the end of a run, PostFlow prints a summary similar to:

```text
============================================================
UNIVERSAL WORKFLOW FINAL SUMMARY
============================================================
Enabled Platforms : 6
Disabled Platforms: 0
------------------------------------------------------------
Total Success     : 6
Total Failed      : 0
Total Skipped     : 0
============================================================
FACEBOOK   -> S:1 | F:0 | SK:0
INSTAGRAM  -> S:1 | F:0 | SK:0
THREADS    -> S:1 | F:0 | SK:0
TELEGRAM   -> S:1 | F:0 | SK:0
TUMBLR     -> S:1 | F:0 | SK:0
DISCORD    -> S:1 | F:0 | SK:0
============================================================
```

Meaning:

```text
S  = Success
F  = Failed
SK = Skipped
```

---

# Production Checklist

Before turning on scheduled automation, verify all of these:

- [ ] Repository is pushed to GitHub.
- [ ] `config.json` contains the correct Dropbox folders.
- [ ] Dropbox application is configured.
- [ ] Dropbox refresh token works.
- [ ] Groq API key works.
- [ ] Facebook credentials work.
- [ ] Instagram credentials work.
- [ ] Threads credentials work.
- [ ] Telegram bot can post.
- [ ] Discord bot can post.
- [ ] Tumblr OAuth credentials work.
- [ ] All GitHub Secrets are configured.
- [ ] `.env` is not committed.
- [ ] API tokens are not hard-coded in source code.
- [ ] At least one test image is available in Dropbox.
- [ ] Manual GitHub Actions run succeeds.
- [ ] Failed-folder behavior has been tested.
- [ ] Scheduled workflow is enabled.

---

# Recommended First Deployment

Do not immediately put hundreds of files into the Dropbox folder.

Use this sequence:

## Test 1 — One platform

Enable one platform.

Add:

```text
test.jpg
```

Run:

```bash
python main.py
```

Confirm success.

---

## Test 2 — Video

Add:

```text
test.mp4
```

Test the platform that receives videos.

For Instagram and Threads, pay particular attention to media processing and public URL access.

---

## Test 3 — Multiple platforms

Enable all desired platforms.

Run manually from GitHub Actions.

Check every platform.

---

## Test 4 — Failure handling

Use a deliberately unsupported/oversized file where appropriate.

Confirm that the failed platform receives a copy under:

```text
/failed/<platform>/
```

---

## Test 5 — Scheduled mode

Only after manual execution is stable should you rely on the cron schedule.

---

# Typical Production Workflow

Once everything is configured, your daily workflow becomes:

```text
1. Create content
       |
       v
2. Put files into Dropbox /instagram
       |
       v
3. GitHub Actions starts PostFlow
       |
       v
4. PostFlow randomly selects one file
       |
       v
5. Caption generated for media
       |
       v
6. File-size checks performed
       |
       v
7. Publish to enabled platforms
       |
       v
8. Temporary errors retried
       |
       +-----------------------------+
       |                             |
       v                             v
 All successful                  Some failed
       |                             |
       v                             v
 Delete inbox file             /failed/platform/
       |
       v
   Run finished
```

---

# Important Operational Behavior

PostFlow is intentionally designed so that the source Dropbox folder acts as an inbox.

That means:

```text
/instagram
```

should contain content waiting to be processed.

After successful processing, the file is removed.

Therefore, do not use the inbox folder as your only permanent archive.

If you need to retain the original files, keep a separate archive folder or backup.

---

# Security

Never put credentials directly in:

```text
main.py
platforms/*.py
config.json
README.md
```

Use environment variables.

Good:

```python
os.getenv("META_TOKEN")
```

Bad:

```python
META_TOKEN = "EAABxxxxxxxxxxxxxxxx"
```

---

## If a secret was accidentally committed

Immediately:

1. Revoke/rotate the exposed credential.
2. Create a new credential.
3. Replace the GitHub Secret.
4. Remove the secret from the repository.
5. Check the Git history and rotate the credential even if the visible file has been deleted.

Deleting a secret from the latest commit does not necessarily remove it from Git history.

---

# Important API Notes

This repository communicates directly with third-party APIs.

Those APIs are controlled by their respective providers.

Platform APIs can change:

- endpoint URLs
- API versions
- permissions
- token lifetimes
- upload limits
- media requirements
- publishing eligibility
- rate limits
- authentication requirements

The code currently contains Meta Graph API version references such as:

```text
v18.0
```

That version may become unsupported over time.

If a previously working Meta integration suddenly returns endpoint/version errors, check the current Meta API documentation and update the project.

The same principle applies to Threads, Telegram, Discord, Tumblr, Dropbox, and Groq.

---

# Common Questions

## Does PostFlow publish multiple files in one run?

No.

The current workflow selects one valid file per execution.

---

## Does it randomly select between image, video and text?

Yes.

Current weights:

```text
20% image
60% video
20% text
```

approximately.

---

## Does it generate a different caption every time?

For image/video posts, caption generation is requested from Groq on each run.

The caption is based primarily on the filename.

---

## Does it store generated captions?

No persistent caption database is implemented in the current repository.

---

## Does it store videos?

No.

PostFlow uses the Dropbox file as the source.

For Instagram and Threads, it creates/uses a Dropbox shared media URL rather than maintaining a separate permanent media server.

---

## Does it use FFmpeg?

No.

There is no FFmpeg processing pipeline in the current repository.

The code does not currently:

- extract audio
- attach music
- transcode video
- change codecs
- resize video
- normalize audio

It sends the existing media to the relevant platform integration.

---

## What happens if one platform fails?

Other platforms can still succeed.

The failed platform is recorded and the source file is copied into its platform-specific failed folder.

---

## What happens if all platforms fail?

The file is placed into the failed folders for the enabled platforms.

The final summary reports the failures.

The program exits with a failure status when there are failures and no successful posts.

---

## Does the workflow automatically refresh expired social tokens?

No.

The current retry manager classifies authentication failures as:

```text
REFRESH
```

and stops.

You must update the relevant credential/token.

Dropbox is different because it is configured around a refresh token.

---

## Can I run it without GitHub Actions?

Yes.

Run:

```bash
python main.py
```

on a machine/server with the required environment variables.

---

## Can I run it from a VPS?

Yes.

Install Python and the dependencies, configure environment variables, and schedule:

```bash
python main.py
```

with cron/systemd or another scheduler.

---

# Maintenance

Periodically check:

```text
Meta API versions
Instagram publishing requirements
Threads API requirements
Telegram Bot API
Discord API
Tumblr API
Dropbox API
Groq model availability
Python dependencies
GitHub Actions runner behavior
```

A social automation project requires occasional maintenance because external APIs are not static.

---

# Useful Files to Know

## `main.py`

The main orchestration layer.

Responsible for:

- loading configuration
- initializing platforms
- selecting files
- generating captions
- publishing
- handling success/failure
- final reporting

---

## `config.json`

Main configuration file.

Controls:

- platform caption limits
- text-post enablement
- Dropbox folders
- retries
- delays
- AI hashtag
- Instagram processing
- Threads behavior

---

## `modules/dropbox_handler.py`

Handles:

- Dropbox authentication
- file listing
- random media selection
- downloading
- shared links
- temporary links
- deletion
- failed-file organization

---

## `modules/caption_generator.py`

Handles:

- Groq connection
- AI caption generation
- hashtag extraction
- fixed hashtag handling
- fallback caption generation

---

## `core/verifier.py`

Handles:

- platform media-size checks

---

## `core/error_classifier.py`

Handles:

- classifying errors as:
  - retry
  - skip
  - stop
  - refresh

---

## `core/retry_manager.py`

Handles:

- retry attempts
- retry delays
- `Retry-After`
- temporary failures
- maximum retries

---

## `platforms/facebook.py`

Facebook publishing.

---

## `platforms/instagram.py`

Instagram publishing and video processing polling.

---

## `platforms/threads.py`

Threads text/image/video publishing and container processing.

---

## `platforms/telegram.py`

Telegram message/image/video publishing.

---

## `platforms/discord.py`

Discord message/file publishing.

---

## `platforms/tumblr.py`

Tumblr text/photo/video publishing.

---

## `.github/workflows/main.yml`

GitHub Actions automation.

It controls:

- Python version
- dependency installation
- secrets
- scheduled execution
- manual execution

---

# Final Setup Summary

If you are setting PostFlow up from zero, the shortest complete path is:

```text
1. Clone repository
       |
       v
2. Install Python 3.12
       |
       v
3. Install dependencies
       |
       v
4. Create Dropbox application
       |
       v
5. Generate Dropbox refresh token
       |
       v
6. Create Groq API key
       |
       v
7. Configure Meta/Facebook/Instagram
       |
       v
8. Configure Threads
       |
       v
9. Configure Telegram
       |
       v
10. Configure Discord
       |
       v
11. Configure Tumblr
       |
       v
12. Put credentials into local environment
       |
       v
13. Configure config.json
       |
       v
14. Put a test file into Dropbox /instagram
       |
       v
15. Run python main.py
       |
       v
16. Verify the post
       |
       v
17. Verify Dropbox file handling
       |
       v
18. Add credentials to GitHub Secrets
       |
       v
19. Run GitHub Actions manually
       |
       v
20. Verify all platforms
       |
       v
21. Enable scheduled execution
```

---

# License

Add your preferred license here before publishing the repository.

For example, if you intend to use the MIT License, add a `LICENSE` file containing the official MIT license text and update this section accordingly.
