# Video Summarizer AI
A simple AI powered youtube video summerization tool that is meant to run from CLI.

# TODO
- [X] ~~Remove hardcoded youtube video in the script~~
- [ ] Make the tool compatible with arbitrary LLM endpoints so it can be run using a local LLM instance.
- [X] ~~Add the option to use youtube transcripts instead of generating transcripts from scratch.~~
- [X] ~~Make script compatabile with CLI arguments~~
- [X] ~~Move the video and transcript to their own folders and add those folders to the ignore~~
- [ ] Ensure the format of the summarizer is consistent via the sysprompt
- [ ] Improve modularity to ensure running from CLI is easier
- [ ] Better error handling for large videos

# Installation

1. ``git clone https://github.com/csmct99/VideoSummarizerAI``
2. ``pip install -r requirements.txt``

# Usage
Ensure your Open AI API key is in an env variable called: ``OPENAI_API_KEY``

``export OPENAI_API_KEY=""`` in your shell profile.

``python3 main.py [youtube video url]``

# CLI Arguments & Flags
``--use-youtube-transcript``
enable this flag to use the youtube transcript instead of generating a new one via whisper.

``--cache-directory [directory path]``
specify the directory to store cached files

``--model [model name]`` 
The model to use for summarization. Default is gpt-4o

``--llm-endpoint [url]``
The URL of the LLM endpoint. Default is empty. Still very WIP. Testing on prod here.

``--prompt-file [file path]``
The path to the system prompt file. Default is prompt.txt, which is included in the repo.

# Example Output

```
Beginning youtube download process
Downloading: ChatGPT "Code Interpreter" But 100% Open-Source (Open Interpreter Tutorial)...
Downloaded 68% at 18.43 MB/s
Downloaded 100% at 8.43 MB/s
Audio finished downloading
Cost of Transcription: $0.08
Transcribing audio...
Transcript cached to file: ChatGPT "Code Interpreter" But 100% Open-Source (Open Interpreter Tutorial).mp3-transcript.txt
Estimated token count of summary: 3046
Input cost of transcript: $0.03
Summary:
The video provides a thorough overview and tutorial on Open Interpreter, an open-source project that allows local execution of a ChatGPT-like code interpreter on a computer. The video explores new features, installation processes, and practical examples. Here's a summary of the key points and features discussed:

**Open Interpreter Updates and Features:**
- Open Interpreter now has the ability to fully control a computer, allowing users to build applications on top of it.
- The interpreter now includes vision capabilities, enabling it to process and interpret images.

**Installation Guide:**
- The installation is shown to be simple, involving the creation of a new Conda environment and using `pip` to install Open Interpreter.
- First-time users need to provide an OpenAI API key.

**Usage Examples:**
- The presenter demonstrates how to use Open Interpreter to manage files and execute shell commands.
- The video shows how it can convert image file formats and open specified folders using voice commands.
- The vision capabilities are demoed by interpreting a screenshot of a dropdown menu and generating HTML and CSS code to recreate the design.

**Developing Applications:**
- Developers can import the Open Interpreter module in Python and write scripts for tasks like plotting stock prices, creating reusable tools like an image conversion script, and even correcting code errors.
- The presenter faces some issues with the interpreter in Visual Studio Code, which illustrates that while powerful, the tool can experience technical glitches.

**Local Power with Open Source Models:**
- Open Interpreter can be completely powered locally using open-source models from projects like LM Studio.
- The presenter uses the "Dolphin" and "Mistral" models for local use, but acknowledges that smaller models may not perform as well as GPT-4 due to their limitations.

**Conclusion and Vision:**
- The author of Open Interpreter, Killian, shares his vision with the presenter, which involves using large language models as interfaces for computers, eliminating the need for traditional applications.
- The video encourages viewers to experiment with Open Interpreter and provide feedback.

**Final Thoughts:**
- The video emphasizes the potential of Open Interpreter and how it aligns with the future of human-computer interaction.
- The presenter invites the audience to try out Open Interpreter, give feedback, and consider liking and subscribing for more content.

In summary, the video offers a comprehensive guide to the Open Interpreter project, demonstrating its installation, new features, practical applications, and the potential for building tools and applications on top of it. It also shows how to run the interpreter using local open-source language models, emphasizing both the capabilities and limitations of the software.
Output Cost for GPT-4: $0.02
Total Cost: $0.13
```
