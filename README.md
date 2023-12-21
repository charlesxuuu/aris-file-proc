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

- Make sure to update `arisFolderPath`, `salmonNoteFolderPath` and `outputVideoPath`
- Make sure to update the `fps` under the main function

### Settings for the video

- **numFramesBefore**: Number of frames to be included in the video before the recorded frame from the excel file

- **numFramesAfter**: Number of frames to be included in the video after the recorded frame from the excel file

```python
Total video frames = numFramesBefore + numFramesAfter
```

- numFramesToBeConsideredTogether: Number of frames to considered together as one video from the excel file