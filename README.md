# aris-file-proc

## Convert ARIS to mp4

For Ubuntu or WSL2

```bash
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
python3 process_ARIS.py

# To exit the virtual environment
deactivate
```

Main files:

1. sonar_denoise_NLM_g8f2.py: NLM desnoising
2. sonar_enhanced_modet.py: motion detection


### Settings for the video

- **numFramesBefore**: Number of frames to be included in the video before the recorded frame from the excel file

- **numFramesAfter**: Number of frames to be included in the video after the recorded frame from the excel file

```python
Total video frames = numFramesBefore + numFramesAfter
```

- numFramesToBeConsideredTogether: Number of frames to considered together as one video from the excel file