import os
from groq import Groq
import logging

class CaptionGenerator:
    def __init__(self, config):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.logger = logging.getLogger(__name__)
        self.fixed_tag = config['settings'].get('fixed_hashtag', '#BoyishLife')

    def generate(self, filename, media_type):
        clean_name = os.path.splitext(filename)[0].replace('_', ' ')
        
        tag_counts = {
            "video": 4,
            "image": 3
        }
        count = tag_counts.get(media_type, 3)

        system_instruction = """
You are a Facebook content strategist and caption writer for a page that wants more views, reach, comments, and shares.

Your job is to write original, human-sounding Facebook captions based on the filename and media type.
Infer the topic, mood, audience, and likely intent from the filename.

Rules:
- Prioritize originality, clarity, and emotional connection.
- Write like a real creator, not like a marketing robot.
- Start with a strong hook in the first line.
- Keep the caption natural, readable, and easy to scan.
- Use short paragraphs or line breaks.
- Encourage engagement with a question, opinion prompt, or soft CTA.
- Match the tone to the content: emotional, inspiring, funny, reflective, exciting, etc.
- Use keywords naturally so the post feels relevant and searchable.
- Use emojis sparingly and only when they fit the mood.
- Do not overuse hashtags. Avoid spammy or unrelated hashtags.
- Never write a caption that feels generic, repetitive, or copied.
- Never mention that you are an AI.
- Never use quotation marks.
- If the content is video, optimize for watch time and comments.
- If the content is an image, optimize for relatability and shares.
- Keep the output concise, clean, and platform-native.
"""

        prompts = {
            "video": (
        f"Create a Facebook Reel caption from the filename '{clean_name}'. "
        "Infer the topic, mood, and audience from the filename. "
        "Write an original, human, story-driven caption that feels natural and engaging. "
        "Start with a strong hook in the first line. "
        "Use 2 to 4 short paragraphs with blank lines between them. "
        "Make it emotional, relatable, or curiosity-driven. "
        "Include a few relevant keywords naturally. "
        "Use emojis sparingly and only if they fit the mood. "
        "End with a soft call-to-action that encourages comments, shares, or saves. "
        "Do not use quotation marks. "
        "Keep it under 150 words. "
        "Use minimal hashtags only if they are highly relevant."
    ),
            "image": (
        f"Create a Facebook photo caption from the filename '{clean_name}'. "
        "Infer the topic, mood, and audience from the filename. "
        "Write a warm, original, conversational caption that feels human. "
        "Start with a scroll-stopping hook. "
        "Use 1 to 3 short paragraphs with blank lines between them. "
        "Make it relatable, thoughtful, or engaging. "
        "Include a few relevant keywords naturally. "
        "Use emojis sparingly and only if they fit the mood. "
        "End with a question or soft call-to-action that invites comments. "
        "Do not use quotation marks. "
        "Keep it under 100 words. "
        "Use minimal hashtags only if they are highly relevant."
    )
        }

        user_prompt = prompts.get(media_type, prompts['image'])

        try:
            completion = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            raw_caption = completion.choices[0].message.content.strip().replace('"', '').replace("'", "")

            parts = raw_caption.split('#')
            main_text = parts[0].strip()

            hashtags = []
            for p in parts[1:]:
                tag = p.split()[0].strip().replace(',', '').replace('.', '')
                if len(tag) > 1:
                    hashtags.append(tag)

            return {
                "text": main_text,
                "tags": hashtags,
                "brand_tag": self.fixed_tag
            }

        except Exception as e:
            self.logger.error(f"AI Generation Failed: {e}")
            return {
                "text": clean_name,
                "tags": ["nature", "life"],
                "brand_tag": self.fixed_tag
            }
