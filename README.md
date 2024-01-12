# Video Summarizer AI
A simple AI powered youtube video summerization tool. 

# TODO
- Remove hardcoded youtube video in the script
- Make the tool compatible with arbitrary LLM endpoints so it can be run using a local LLM instance.
- Add the option to use youtube transcripts instead of generating transcripts from scratch.
- Make script compatabile with CLI arguments
- Move the video and transcript to their own folders and add those folders to the ignore
- Ensure the format of the summarizer is consistent via the sysprompt

# Installation
Pip requirements have been piped to requirements.txt

1. ``git clone https://github.com/csmct99/VideoSummarizerAI``
2. ``pip install -r requirements.txt``
3. ``python main.py``
