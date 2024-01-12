import os

from pytube import YouTube, exceptions as pytube_exceptions
import math
from openai import OpenAI
import tiktoken

# Cost of models
TRANSCRIPTION_COST_PER_MIN = 0.006
GPT4_INPUT_COST_PER_1K_TOKENS = 0.01
GPT4_OUTPUT_COST_PER_1K_TOKENS = 0.03

MAX_OUTPUT_TOKENS = 1500

def estimate_token_length(text: str) -> int:
    """Estimate the number of tokens in a given text for GPT-4."""
    encoder = tiktoken.encoding_for_model("gpt-4")
    tokens = encoder.encode(text)
    return len(tokens)

def calculate_progress(total_size: int, bytes_remaining: int) -> int:
    """Calculate the percentage of download completion."""
    bytes_downloaded = total_size - bytes_remaining
    return math.floor((bytes_downloaded / total_size) * 100)


def display_speed(chunk_size: int, interval: float = 0.5) -> float:
    """Calculate and return the download speed in MB/s."""
    return chunk_size / (1024 * interval) / 1000


def progress_function(stream, chunk, bytes_remaining):
    """Function to handle progress updates during download."""
    total_size = stream.filesize
    percentage_of_completion = calculate_progress(total_size, bytes_remaining)
    speed = display_speed(len(chunk))

    print(f"Downloaded {percentage_of_completion}% at {speed:.2f} MB/s", flush=True)


def download_audio(video_url: str, download_directory: str) -> tuple:
    try:
        print("Beginning youtube download process")

        yt = YouTube(video_url, on_progress_callback=progress_function)
        filename = f"{yt.title}.mp3"

        audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
        video_duration_seconds = yt.length  # Duration of the video in seconds

        print(f"Downloading: {yt.title}...")
        audio_stream.download(output_path=download_directory, filename=filename)

        return filename, video_duration_seconds

    except pytube_exceptions.PytubeError as e:
        print(f"Error downloading video: {e}")
        return None, 0


def calculate_transcription_cost(duration_seconds: int) -> float:
    """Calculate the cost of transcription based on duration in seconds."""
    duration_minutes = math.ceil(duration_seconds / 60)  # Rounding up to the nearest minute
    return duration_minutes * TRANSCRIPTION_COST_PER_MIN


def transcribe_audio(audio_file_path: str, output_file: str) -> str:
    """Transcribe audio and return the transcript. Uses cached file if it exists."""
    try:

        # See if the file exists, if it does then we can skip the transcription and just read the file
        if os.path.exists(output_file):
            with open(output_file, "r") as f:
                print("Transcript already exists, reading from file...")
                return f.read()

        with open(audio_file_path, "rb") as audio_file:
            client = OpenAI()

            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )

            # Write the transcript to a file
            with open(output_file, "w") as f:
                f.write(transcript.text)
                print(f"Transcript cached to file: {output_file}")

            return transcript.text

    except (IOError) as e:
        print(f"Error in transcription: {e}")
        return None


def summarize_text(input_text: str, gpt_model: str = "gpt-4-1106-preview") -> str:
    """Summarize the text using the given OpenAI model."""
    try:
        # Read system prompt from 'prompt.txt'
        with open('prompt.txt', 'r') as prompt_file:
            system_prompt = prompt_file.read()

        client = OpenAI()

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
    total_cost = 0

    video_url = 'https://www.youtube.com/watch?v=xPd8FFzIeOw'  # Replace with your URL
    download_directory = ''  # Specify your download directory here

    filename, video_duration_seconds = download_audio(video_url, download_directory)
    print("Audio finished downloading")

    # Calculate and display the transcription cost
    cost = calculate_transcription_cost(video_duration_seconds)
    total_cost += cost
    print(f"Cost of Transcription: ${cost:.2f}")

    print("Transcribing audio...")

    transcript = transcribe_audio(filename, f"{filename}-transcript.txt")

    if transcript:
        token_count = estimate_token_length(transcript)
        print(f"Estimated token count of summary: {token_count}")

        input_token_cost = token_count / 1000 * GPT4_INPUT_COST_PER_1K_TOKENS
        total_cost += input_token_cost
        print(f"Input cost of transcript: ${input_token_cost:.2f}")

        # Call summarize_text with the transcript
        summary = summarize_text(transcript)
        if summary:
            print("Summary:")
            print(summary)

            output_token_count = estimate_token_length(summary)
            output_token_cost = output_token_count / 1000 * GPT4_OUTPUT_COST_PER_1K_TOKENS
            total_cost += output_token_cost
            print(f"Output Cost for GPT-4: ${output_token_cost:.2f}")
            print(f"Total Cost: ${total_cost:.2f}")


if __name__ == "__main__":
    main()
    print("== DONE ==")
