import os 
from google import genai
from youtube_transcript_api import YouTubeTranscriptApi
import re

def get_language():
    idioma = input("What language would you like to translate to? ")
    
    method = 0 # Initialize with an invalid value
    while method not in [1, 2]:
        try:
            method = int(input("What would you like to translate? (1) Youtube Transcript (2) Text Input: "))
            if method not in [1, 2]:
                print("Invalid choice. Please enter 1 or 2.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    # Now that we have a valid method, we can act on it
    if method == 1:
        url = input("Please provide the Youtube URL: ")
        final_transcript = youtube_transcript(url)
        # Handle case where transcript fails
        if final_transcript is None:
            return None 
        return function(final_transcript, idioma)
    elif method == 2:
        final_transcript = input("Please provide the text you would like to translate: ")
        return function(final_transcript, idioma)
    

def youtube_transcript(url):
    video_id = re.search(r"v=([^&]+)", url).group(1)
    ytt_api = YouTubeTranscriptApi()
    fetched_transcript = ytt_api.fetch(video_id, languages=["en", "ja",'es','fr','de','it','pt','ru','zh'])
    final_transcript = ""
    for snippet in fetched_transcript:
        final_transcript += snippet.text + " "
    # indexable
    last_snippet = fetched_transcript[-1]
    # provides a length
    snippet_count = len(fetched_transcript)
    return final_transcript

def function(final_transcript, language):
    translation = final_transcript
    prompt = "Translate the following content to "+ language + ": " + translation
    return prompt


# The client gets the API key from the environment variable `GEMINI_API_KEY`. 
client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.5-flash", contents=get_language()
)

print(response.text)