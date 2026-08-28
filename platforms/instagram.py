import logging
import os
import time

import requests


class InstagramPoster:
    def __init__(self, settings=None):
        settings = settings or {}
        self.logger = logging.getLogger(__name__)
        self.ig_id = os.getenv("IG_ID")
        self.token = os.getenv("META_TOKEN")
        self.graph_version = str(settings.get("instagram_graph_version", "v18.0")).strip()
        self.base_url = f"https://graph.instagram.com/{self.graph_version}/{self.ig_id}"
        self.processing_wait_seconds = int(
            settings.get("instagram_processing_wait_seconds", 10)
        )
        self.processing_max_attempts = int(
            settings.get("instagram_processing_max_attempts", 30)
        )
        self.publish_delay_seconds = int(
            settings.get("instagram_publish_delay_seconds", 15)
        )

        if not self.ig_id or not self.token:
            raise ValueError("Missing Instagram credentials")

    def post_text(self, text):
        self.logger.info("Instagram does not support text-only publishing, skipping")
        return "SKIPPED"

    def post_video(self, video_url, caption):
        return self._create_publish_container(video_url, caption, "VIDEO")

    def post_image(self, image_url, caption):
        return self._create_publish_container(image_url, caption, "IMAGE")

    def _create_publish_container(self, media_url, caption, media_type):
        if not media_url or not str(media_url).strip():
            raise ValueError("Instagram requires a public media URL")

        url = f"{self.base_url}/media"
        payload = {
            "access_token": self.token,
            "caption": caption,
            "media_type": "REELS" if media_type == "VIDEO" else "IMAGE",
        }

        if media_type == "VIDEO":
            payload["video_url"] = str(media_url).strip()
            payload["share_to_feed"] = "true"
        else:
            payload["image_url"] = str(media_url).strip()

        response = requests.post(url, data=payload, timeout=60)
        if response.status_code != 200:
            raise requests.HTTPError(
                f"Instagram create container failed: {response.text}",
                response=response,
            )

        creation_id = response.json().get("id")
        if not creation_id:
            raise Exception("Instagram create container failed: missing creation id")

        if media_type == "VIDEO":
            self._wait_for_video_processing(creation_id)

        publish_url = f"{self.base_url}/media_publish"
        publish_response = requests.post(
            publish_url,
            data={"creation_id": creation_id, "access_token": self.token},
            timeout=60,
        )

        if publish_response.status_code != 200:
            raise requests.HTTPError(
                f"Instagram publish failed: {publish_response.text}",
                response=publish_response,
            )

        return bool(publish_response.json().get("id"))

    def _wait_for_video_processing(self, creation_id):
        status = "IN_PROGRESS"

        for attempt in range(1, self.processing_max_attempts + 1):
            status_response = requests.get(
                f"https://graph.instagram.com/{self.graph_version}/{creation_id}",
                params={"fields": "status_code", "access_token": self.token},
                timeout=30,
            )

            if status_response.status_code != 200:
                self.logger.warning(f"Instagram poll error: {status_response.text}")
                if attempt < self.processing_max_attempts:
                    time.sleep(self.processing_wait_seconds)
                continue

            status = status_response.json().get("status_code", "ERROR")
            self.logger.info(
                "Instagram poll attempt %s/%s: %s",
                attempt,
                self.processing_max_attempts,
                status,
            )

            if status == "ERROR":
                raise Exception("Instagram video processing failed")

            if status == "FINISHED":
                if self.publish_delay_seconds > 0:
                    time.sleep(self.publish_delay_seconds)
                return

            if attempt < self.processing_max_attempts:
                time.sleep(self.processing_wait_seconds)

        raise Exception(f"Instagram video processing timeout: last_status={status}")
