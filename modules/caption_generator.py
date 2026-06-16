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

        system_instruction = (
          "You write Instagram captions from filenames."

"Read the filename and infer the most likely topic, mood, scene, and audience. Do not mention that you are guessing."

"Write a caption that feels natural, current, and human."
"Make it discoverable with keyword-rich language that matches the post topic."
"Start with a strong hook in the first line.
Keep it in 3 short sections with a blank line between sections."
"Use short, clean sentences."
"Include the main keyword naturally 2 to 3 times, plus 1 to 2 supporting keywords."
"Add a soft CTA near the end, such as asking a question, inviting a save, comment, or share."
"Use emojis only when they fit the mood of the post, and keep them natural."
"Never use quotation marks."
"Never add the fixed hashtag {self.fixed_tag}; it will be appended separately."
"End with 3 to 5 highly relevant hashtags on the final line."
"Avoid generic, overused, or irrelevant hashtags."
"Do not sound robotic, salesy, or overly promotional."
        )

        prompts = {
            "video": f"Write an engaging, storytelling caption for a video about '{clean_name}'. Max 150 words.",
            "image": f"Write a short, punchy caption for a photo titled '{clean_name}'. Max 100 words."
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
