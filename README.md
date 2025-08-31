# Research Task 6: Deep Fake

## Welcome

In previous research periods, we asked our favorite LLM to create narratives, stories, or textual summaries of datasets.  
For example, one attempt used seasonal statistics from a Syracuse University sports team and asked the LLM for recommendations for the upcoming season.  

This period, the task was to take the narrative you produced and transform it into an AI-generated **“deep fake” interview**.  
If you are just joining this period, you may create your own narrative or script from scratch.  

The end goal is to create **audio or video output** that simulates a realistic interview conversation.  

---

## Project Overview

This repository contains:

- `code.py` – Main pipeline:
  - Loads a narrative (`task05_narrative.txt`) or uses an existing `Interview_script.md`
  - Generates interview dialogue if missing
  - Parses dialogue into alternating **Interviewer** / **Expert** lines
  - Synthesizes **dual-voice audio** using OpenAI TTS (`alloy` + `verse`)
  - Renders a **video with background image**
- `Interview_script.md` – Pre-written or LLM-generated script
- `task05_narrative.txt` – Narrative text source (from Research Task 5)
- `background.jpg` – Background image for video (1920x1080 recommended)
- `scripts.txt` – Saved final interview dialogue
- `prompts.txt` – System and user prompts given to the LLM
- `task06_output/` – Generated outputs:
  - `interview_script.md` – Script copy used for audio generation
  - `deepfake_interview.mp3` – Dual-voice audio
  - `deepfake_interview.mp4` – Video (if background image is present)

---

## Requirements

- **Python 3.9+**
- **ffmpeg** installed and on PATH
- Python dependencies:
  ```bash
  pip install openai python-dotenv pydub moviepy Pillow
  ```

---

## .env File

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=sk-your-api-key-here
```

---

## Workflow

1. **Prepare Inputs**
   - Write your narrative in `task05_narrative.txt`
   - Or create `Interview_script.md` with alternating dialogue
   - Add `background.jpg` for video rendering

2. **Run the Code**
   ```bash
   python code.py
   ```

3. **Outputs Generated**
   - Audio file: `task06_output/deepfake_interview.mp3`
   - Video file: `task06_output/deepfake_interview.mp4`
   - Script copy: `task06_output/interview_script.md`

---

## Outputs

- **Audio**: Dual-voice interview (`deepfake_interview.mp3`)  
- **Video**: Interview with static background image (`deepfake_interview.mp4`)  
- **Script**: Dialogue used for generation (`interview_script.md`)  

---

## Deliverables

- `code.py` – main Python pipeline  
- `README.md` – this documentation  
- `scripts.txt` – final dialogue script  
- `prompts.txt` – system + user prompts  
- `task05_narrative.txt` – input narrative  
- `Interview_script.md` – pre-written dialogue (optional)  
- `background.jpg` – background image for video  
- `task06_output/` – generated outputs  

---

**Author:** Ayush Thoniparambil Saseendran
**Course:** Research Task 6 – Deep Fake Interview  
