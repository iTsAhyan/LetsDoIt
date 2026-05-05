import os, asyncio, requests, re, gc
from moviepy.editor import *
import edge_tts
from huggingface_hub import HfApi

# সরাসরি এখানে আপনার টোকেন দিন [আব্দুল্লাহ ভাই স্পেশাল]
HF_TOKEN = "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"
PEXELS_KEY = "eEyJWXVZVHpFG02t8Nso0dgb1YEkW7WAXOc7y0WV76Gv1u6N9bCUzFxO"
REPO_ID = "AhyanCreationsLTD/coldcasevid"

async def render():
    # script.txt থেকে স্টোরি পড়বে
    if not os.path.exists("script.txt"):
        print("❌ script.txt ফাইলটি খুঁজে পাওয়া যায়নি!")
        return

    with open("script.txt", "r") as f:
        script = f.read()

    # ১. ভয়েস তৈরি
    print("🎙️ ভয়েস তৈরি হচ্ছে...")
    comm = edge_tts.Communicate(script, "en-US-AvaNeural", rate="-10%", pitch="-5Hz")
    await comm.save("voice.mp3")
    audio = AudioFileClip("voice.mp3")

    # ২. ফুটেজ ডাউনলোড
    sentences = re.split(r'[,.!?]', script)
    keywords = [re.findall(r'\w+', s)[-1] for s in sentences if len(s.strip()) > 5]
    
    final_clips = []
    curr_time = 0
    headers = {"Authorization": PEXELS_KEY}

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

    # ৩. ফাইনাল রেন্ডারিং
    print("🎞️ রেন্ডারিং চলছে...")
    final_video = concatenate_videoclips(final_clips, method="compose").set_audio(audio)
    output = "AHYAN_COLDCASE_FINAL.mp4"
    final_video.write_videofile(output, fps=24, bitrate="6000k", codec="libx264")

    # ৪. হাগিং ফেস-এ আপলোড
    print("☁️ হাগিং ফেস-এ আপলোড হচ্ছে...")
    api = HfApi()
    api.upload_file(path_or_fileobj=output, path_in_repo=f"renders/{output}", 
                    repo_id=REPO_ID, repo_type="dataset", token=HF_TOKEN)
    print("🏆 মিশন সফল আব্দুল্লাহ ভাই! আপনার ভিডিও রেডি।")

if __name__ == "__main__":
    asyncio.run(render())
