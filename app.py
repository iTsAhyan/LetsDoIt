import os, asyncio, requests, re, gc
from moviepy.editor import *
import edge_tts
from huggingface_hub import HfApi

async def render():
    hf_token = os.getenv("HF_TOKEN")
    pexels_key = os.getenv("PEXELS_KEY")
    repo_id = "AhyanCreationsLTD/coldcasevid"
    
    # script.txt থেকে আপনার স্টোরি পড়বে
    with open("script.txt", "r") as f:
        script = f.read()

    # ১. ভয়েস তৈরি
    print("🎙️ ভয়েস তৈরি হচ্ছে...")
    comm = edge_tts.Communicate(script, "en-US-AvaNeural", rate="-10%", pitch="-5Hz")
    await comm.save("voice.mp3")
    audio = AudioFileClip("voice.mp3")

    # ২. ফুটেজ ডাউনলোড (Sequential Logic to save RAM)
    sentences = re.split(r'[,.!?]', script)
    keywords = [re.findall(r'\w+', s)[-1] for s in sentences if len(s.strip()) > 5]
    
    final_clips = []
    curr_time = 0
    headers = {"Authorization": pexels_key}

    print(f"🎬 {len(keywords)}টি ফুটেজ প্রসেস হচ্ছে...")
    for i, kw in enumerate(keywords[:120]): 
        if curr_time >= audio.duration: break
        try:
            url = f"https://api.pexels.com/videos/search?query={kw}&per_page=1&orientation=landscape"
            res = requests.get(url, headers=headers).json()
            v_url = res['videos'][0]['video_files'][0]['link']
            
            v_path = f"v_{i}.mp4"
            with open(v_path, "wb") as f: f.write(requests.get(v_url).content)
            
            clip = VideoFileClip(v_path).subclip(0, 5).resize(width=1280).without_audio().crossfadein(0.5)
            final_clips.append(clip)
            curr_time += clip.duration
            os.remove(v_path)
            if i % 10 == 0: gc.collect()
        except: continue

    # ৩. ফাইনাল অ্যাসেম্বলি
    print("🎞️ রেন্ডারিং...")
    final_video = concatenate_videoclips(final_clips, method="compose").set_audio(audio)
    output = "AHYAN_COLDCASE_FINAL.mp4"
    final_video.write_videofile(output, fps=24, bitrate="6000k", codec="libx264")

    # ৪. হাগিং ফেস-এ আপলোড
    api = HfApi()
    api.upload_file(path_or_fileobj=output, path_in_repo=f"renders/{output}", 
                    repo_id=repo_id, repo_type="dataset", token=hf_token)
    print("🏆 মিশন সফল আব্দুল্লাহ ভাই!")

if __name__ == "__main__":
    asyncio.run(render())
