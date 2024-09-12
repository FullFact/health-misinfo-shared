### Multimodal Raphael

> None of this currently has any impact on production code

This directory contains some initial dev scripts for doing what we do for captions in Raphael right now, but with raw video as input, using Gemini's multimodal capability.

If we decide to put it in Raphael proper, then we can start moving this to src.

#### Main differences from text Raphael

The main difference with this multimodal stuff is that instead of giving the model some text inside a prompt, we give it a prompt and a Google Cloud URI directing it to an mp4 video file.

The prompt has been modified to try and extract non-audio claims.
It will try to extract:

1. Claims made audibly in the video, just like normal Raphael.
2. Claims made in text on the video
3. Claims implied or suggested by the action of the video

The actual format of the output is almost exactly the same, with the addition of timestamps, so we can work out when claims appeared even if they're not in the text of the captions.

I expect it will be harder to verify whether the model has made anything up in a multimodal setting, but as long as it is presented in such a way that the user can verify it, it may be fine.

I have not yet verified if the timestamps are nonsense.

#### Example of output

Take [this TikTok](https://www.tiktok.com/@elleighhasababy/video/7234318005587447083) as an example.

This is a video of a baby, with some text over that suggests that it died because of the vaccine it had been given.
The implication is that vaccines cause babies to die.
This would not have been picked up by Raphael though, because it would only have the spoken words in the video, which are totally innocuous.

The multimodal prompt pulls out six claims:
* **Vaccines can cause death in babies. (worth checking)**
* **A baby died 3 days old.**
* A baby had a bandage from a vaccine.
* A baby did not cry or flinch when getting a vaccine.
* A baby was given an antibiotic.
* **The video is trying to claim that vaccines are dangerous and cause death in babies. (worth checking)**

The claims in bold are ones that would not be evident from just the spoken words in the video.

> This is only one example. I've run it on a few videos and the results are similar, but a larger scale analysis should be done to see if it works more generally.

#### How to use it

Using it in code is pretty straight forward.

```python
from multimodal.multimodal_analyser import MultiModalRaphael
from pprint import pp

analyser = MultiModalRaphael()
output = analyser.analyse_video(
    "gs://bucket-name/path/to/video.mp4"
)

pp(output)
```

If you want to run the examples I have run so far, do the following:

1. Download the videos in `data/tiktoks.txt` by running `download_videos.py`. 
This will download the videos using yt-dlp (so you will need that installed, which I did with brew), and upload them to Google Cloud Storage.
2. Run `run_multimodal_on_tiktoks.py` to produce the file `analysed.json`, which contains the claims from each video.