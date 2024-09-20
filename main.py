import os
import argparse
import math
import tiktoken
import requests
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from decimal import Decimal
import yt_dlp
import re

# Import the OpenAI client
from openai import OpenAI

# Create an OpenAI client instance
client = OpenAI(
    # This is the default and can be omitted if you have set the OPENAI_API_KEY environment variable
    api_key=os.environ.get("OPENAI_API_KEY"),
)

# Cost of models
TRANSCRIPTION_COST_PER_MIN = 0.006
GPT4_INPUT_COST_PER_1M_TOKENS = 5
GPT4_OUTPUT_COST_PER_1M_TOKENS = 15

MAX_OUTPUT_TOKENS = 1500

def sanitize_filename(name):
    """Sanitize the video title to create a valid directory name."""
    # Replace spaces with underscores
    name = name.replace(' ', '_')
    # Remove special characters
    name = re.sub(r'[^\w\-_\.]', '', name)
    return name

def estimate_token_length(text: str) -> int:
    """Estimate the number of tokens in a given text for GPT-4."""
    encoder = tiktoken.encoding_for_model("gpt-4")
    tokens = encoder.encode(text)
    return len(tokens)

def get_video_info(video_url):
    """Extract video information using yt-dlp."""
    try:
        ydl_opts = {'quiet': True, 'skip_download': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=False)
            title = info_dict.get('title', 'video')
            video_id = info_dict.get('id', '')
            duration = info_dict.get('duration', 0)
            return title, video_id, duration
    except Exception as e:
        print(f"Error fetching video info: {e}")
        return None, None, 0

def download_audio(video_url: str, output_directory: str) -> tuple:
    """Download audio from YouTube video using yt-dlp."""
    try:
        print("Beginning YouTube download process")

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(output_directory, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
                'nopostoverwrites': False,
            }],
            'quiet': False,
            'no_warnings': True,
        }

        audio_file_path = ''
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=False)
            filename = ydl.prepare_filename(info_dict)
            # Change extension to .mp3
            filename = os.path.splitext(filename)[0] + '.mp3'
            audio_file_path = os.path.join(output_directory, os.path.basename(filename))
            if os.path.exists(audio_file_path):
                print("Audio file already exists. Skipping download.")
                video_duration_seconds = info_dict.get('duration', 0)
                return audio_file_path, video_duration_seconds
            else:
                # Download the audio
                info_dict = ydl.extract_info(video_url, download=True)
                video_duration_seconds = info_dict.get('duration', 0)
                return audio_file_path, video_duration_seconds

    except yt_dlp.utils.DownloadError as e:
        print(f"Error downloading video: {e}")
        return None, 0

def calculate_transcription_cost(duration_seconds: int) -> float:
    """Calculate the cost of transcription based on duration in seconds."""
    duration_minutes = math.ceil(duration_seconds / 60)  # Rounding up to the nearest minute
    return duration_minutes * TRANSCRIPTION_COST_PER_MIN

def transcribe_audio(audio_file_path: str, output_file: str) -> str:
    """Transcribe audio and return the transcript with timestamps."""
    try:
        if os.path.exists(output_file):
            with open(output_file, "r") as f:
                print("Transcript already exists, reading from file...")
                return f.read()

        with open(audio_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format='srt'  # Get transcript in SRT format with timestamps
            )

            # Write the transcript to a file
            with open(output_file, "w") as f:
                f.write(transcript)
                print(f"Transcript cached to file: {output_file}")

            return transcript

    except Exception as e:
        print(f"Error in transcription: {e}")
        return None

def extract_video_id(url):
    """
    Extract the video ID from a YouTube URL.
    """
    regex = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    match = re.search(regex, url)
    if match:
        return match.group(1)
    else:
        return None

def get_youtube_transcript(video_id: str) -> str:
    """Fetch the YouTube transcript for the given video ID and format it with timestamps."""
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # You can specify the language here if needed
        transcript = transcript_list.find_transcript(['en'])

        transcript_data = transcript.fetch()

        formatted_transcript = ""
        for entry in transcript_data:
            text = entry['text']
            formatted_transcript += f"{text}\n"

        return formatted_transcript

    except TranscriptsDisabled:
        print("Transcripts are disabled for this video.")
        return None
    except NoTranscriptFound:
        print("No transcript found for this video.")
        return None
    except Exception as e:
        print(f"Error fetching YouTube transcript: {e}")
        return None

def summarize_text(input_text: str, system_prompt: str, gpt_model: str = "gpt-4o-2024-08-06", llm_endpoint: str = None) -> str:
    """Summarize the text using the given model or LLM endpoint."""
    try:
        if llm_endpoint:
            # Make a POST request to the specified LLM endpoint
            payload = {
                "prompt": system_prompt + "\n\n" + input_text,
                "max_tokens": MAX_OUTPUT_TOKENS,
            }
            response = requests.post(llm_endpoint, json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get('summary') or result.get('text') or result.get('response')
        else:
            # Use OpenAI API via the client
            response = client.chat.completions.create(
                model=gpt_model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": input_text
                    }
                ],
                max_tokens=MAX_OUTPUT_TOKENS
            )

            return response.choices[0].message.content

    except Exception as e:
        print(f"Error in summarization: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='AI Video Summarizer')
    parser.add_argument('video_url', type=str, help='YouTube video URL')
    parser.add_argument('--use-youtube-transcript', action='store_true', help='Use YouTube transcript instead of generating one')
    parser.add_argument('--cache-directory', type=str, default='./cache', help='Directory to store cached files')
    parser.add_argument('--model', type=str, default='gpt-4', help='LLM model to use for summarization')
    parser.add_argument('--llm-endpoint', type=str, default='', help='URL of the LLM endpoint')
    parser.add_argument('--prompt-file', type=str, default='prompt.txt', help='Path to system prompt file')
    args = parser.parse_args()

    total_cost = Decimal('0.00')

    video_url = args.video_url
    cache_directory = args.cache_directory
    gpt_model = args.model
    use_youtube_transcript = args.use_youtube_transcript
    llm_endpoint = args.llm_endpoint if args.llm_endpoint else None

    # Load system prompt
    with open(args.prompt_file, 'r') as prompt_file:
        system_prompt = prompt_file.read()

    # Fetch video info
    title, video_id, video_duration_seconds = get_video_info(video_url)
    if title is None:
        print("Failed to fetch video info. Exiting.")
        return

    # Sanitize video title to create a valid directory name
    sanitized_title = sanitize_filename(title)
    video_dir = os.path.join(cache_directory, sanitized_title)
    os.makedirs(video_dir, exist_ok=True)

    if use_youtube_transcript:
        print("Fetching YouTube transcript...")
        transcript_file = os.path.join(video_dir, f"{sanitized_title}-transcript.txt")
        if os.path.exists(transcript_file):
            with open(transcript_file, "r") as f:
                print("Transcript already exists, reading from file...")
                transcript = f.read()
        else:
            transcript = get_youtube_transcript(video_id)
            if transcript:
                print("YouTube transcript fetched successfully.")
                # Save transcript to file
                with open(transcript_file, "w") as f:
                    f.write(transcript)
                print(f"Transcript saved to {transcript_file}")
            else:
                print("Failed to fetch YouTube transcript. Exiting.")
                return
    else:
        # Download audio
        audio_file_path, video_duration_seconds = download_audio(video_url, video_dir)
        if audio_file_path is None:
            print("Failed to download audio. Exiting.")
            return
        print("Audio ready.")

        # Calculate and display the transcription cost
        cost = calculate_transcription_cost(video_duration_seconds)
        total_cost += Decimal(cost)
        print(f"Cost of Transcription: ${Decimal(cost):.2f}")

        print("Transcribing audio...")

        transcript_file = os.path.join(video_dir, f"{sanitized_title}-transcript.txt")
        if os.path.exists(transcript_file):
            with open(transcript_file, "r") as f:
                print("Transcript already exists, reading from file...")
                transcript = f.read()
        else:
            transcript = transcribe_audio(audio_file_path, transcript_file)
            if transcript is None:
                print("Failed to transcribe audio. Exiting.")
                return

    token_count = estimate_token_length(transcript)
    print(f"Estimated token count of transcript: {token_count}")

    input_token_cost = Decimal(token_count) / Decimal(1000000) * Decimal(GPT4_INPUT_COST_PER_1M_TOKENS)
    total_cost += input_token_cost
    print(f"Input cost of transcript: ${input_token_cost:.4f}")

    # Check if summary already exists
    summary_file = os.path.join(video_dir, f"{sanitized_title}-summary.txt")
    if os.path.exists(summary_file):
        with open(summary_file, "r") as f:
            print("Summary already exists, reading from file...")
            summary = f.read()
    else:
        # Call summarize_text with the transcript
        summary = summarize_text(transcript, system_prompt, gpt_model=gpt_model, llm_endpoint=llm_endpoint)
        if summary:
            # Save summary to file
            with open(summary_file, "w") as f:
                f.write(summary)
            print(f"Summary saved to {summary_file}")
        else:
            print("Failed to generate summary.")
            return

    print("Summary:")
    print(summary)

    output_token_count = estimate_token_length(summary)
    output_token_cost = Decimal(output_token_count) / Decimal(1000000) * Decimal(GPT4_OUTPUT_COST_PER_1M_TOKENS)
    total_cost += output_token_cost
    print(f"Output Cost for {gpt_model}: ${output_token_cost:.4f}")
    print(f"Total Cost: ${total_cost:.4f}")

if __name__ == "__main__":
    main()
    print("== DONE ==")
