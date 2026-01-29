import moviepy.editor as mp
from common_utils import parse_time

import os

import subprocess

# Check for GPU acceleration (NVIDIA NVENC)
HAS_GPU = False
try:
    # Check ffmpeg encoders for nvenc presence
    res = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True)
    if "h264_nvenc" in res.stdout:
        HAS_GPU = True
except:
    pass

# Set global codec settings
VIDEO_CODEC = "h264_nvenc" if HAS_GPU else "libx264"
# nvenc presets: slow, medium, fast. x264 presets: ultrafast, superfast, etc.
PRESET = "fast" if HAS_GPU else "ultrafast"
# Fallback preset for compression which used 'faster' previously
COMPRESS_PRESET = "fast" if HAS_GPU else "faster"

print(f"Video Backend: Using {'GPU (NVENC)' if HAS_GPU else 'CPU (libx264)'}")

def join_videos(input_paths, output_path):
    if not input_paths: return
    
    # Normalize paths
    input_paths = [os.path.abspath(p) for p in input_paths]
    output_path = os.path.abspath(output_path)
    
    # Preventive check
    if output_path in input_paths:
        raise ValueError("Output file cannot be one of the input files")

    # Temp audio file in output directory to avoid permission/path issues
    temp_audio = os.path.join(os.path.dirname(output_path), "temp_merged_audio.m4a")

    clips = []
    try:
        for p in input_paths:
             if os.path.exists(p):
                 clips.append(mp.VideoFileClip(p))
        
        if not clips: raise Exception("No valid video clips found")

        # method='compose' handles different resolutions/aspect ratios
        final_clip = mp.concatenate_videoclips(clips, method="compose")
        
        # Explicit temp_audiofile helps avoid OSError 22 on Windows
        final_clip.write_videofile(output_path, codec=VIDEO_CODEC, audio_codec="aac", temp_audiofile=temp_audio, remove_temp=True, preset=PRESET, threads=4)
        final_clip.close()
    except Exception as e:
        raise Exception(f"Merge Failed: {str(e)}")
    finally:
        for clip in clips: 
            try: clip.close()
            except: pass
        if os.path.exists(temp_audio):
             try: os.remove(temp_audio)
             except: pass

def cut_video(input_path, output_path, start_time, end_time):
    t1 = parse_time(str(start_time))
    t2 = parse_time(str(end_time))
    
    with mp.VideoFileClip(input_path) as video:
        if t2 == 0 or t2 > video.duration:
             t2 = video.duration
        
        new = video.subclip(t1, t2)
        new.write_videofile(output_path, codec=VIDEO_CODEC, audio_codec="aac", preset=PRESET, threads=4)

def convert_video(input_path, output_path):
    clip = mp.VideoFileClip(input_path)
    clip.write_videofile(output_path, codec=VIDEO_CODEC, preset=PRESET, threads=4)
    clip.close()

def compress_video(input_path, output_path, bitrate="1000k"):
    clip = mp.VideoFileClip(input_path)
    if clip.h > 720:
        clip = clip.resize(height=720)
    
    clip.write_videofile(output_path, bitrate=bitrate, preset=COMPRESS_PRESET, codec=VIDEO_CODEC, audio_codec="aac", threads=4)
    clip.close()

def extract_audio(input_path, output_path):
    clip = mp.VideoFileClip(input_path)
    if clip.audio:
         clip.audio.write_audiofile(output_path)
    clip.close()

def add_watermark(input_path, output_path, watermark_image, position="bottom-right", opacity=0.7):
    """Add a watermark/logo image to video."""
    video = mp.VideoFileClip(input_path)
    logo = mp.ImageClip(watermark_image).set_duration(video.duration)
    
    # Resize logo to reasonable size (1/5 of video width)
    logo = logo.resize(width=video.w // 5)
    
    # Set opacity
    logo = logo.set_opacity(opacity)
    
    # Position the watermark
    if position == "top-left":
        pos = (10, 10)
    elif position == "top-right":
        pos = (video.w - logo.w - 10, 10)
    elif position == "bottom-left":
        pos = (10, video.h - logo.h - 10)
    else:  # bottom-right (default)
        pos = (video.w - logo.w - 10, video.h - logo.h - 10)
    
    logo = logo.set_position(pos)
    
    final = mp.CompositeVideoClip([video, logo])
    final.write_videofile(output_path, codec=VIDEO_CODEC, audio_codec="aac", preset=PRESET, threads=4)
    video.close()

def change_speed(input_path, output_path, speed_factor=1.0):
    """Change video playback speed. >1 = faster, <1 = slower."""
    clip = mp.VideoFileClip(input_path)
    
    # Speed up or slow down
    new_clip = clip.fx(mp.vfx.speedx, speed_factor)
    
    new_clip.write_videofile(output_path, codec=VIDEO_CODEC, audio_codec="aac", preset=PRESET, threads=4)
    clip.close()

def mute_video(input_path, output_path):
    """Remove audio from video."""
    clip = mp.VideoFileClip(input_path)
    clip = clip.without_audio()
    clip.write_videofile(output_path, codec=VIDEO_CODEC, preset=PRESET, threads=4)
    clip.close()

def add_background_music(input_path, output_path, audio_path, volume=0.5):
    """Add background music to video, mixing with original audio."""
    video = mp.VideoFileClip(input_path)
    music = mp.AudioFileClip(audio_path)
    
    # Loop music if shorter than video
    if music.duration < video.duration:
        music = mp.afx.audio_loop(music, duration=video.duration)
    else:
        music = music.subclip(0, video.duration)
    
    # Adjust music volume
    music = music.volumex(volume)
    
    # Mix audio
    if video.audio:
        final_audio = mp.CompositeAudioClip([video.audio, music])
    else:
        final_audio = music
    
    video = video.set_audio(final_audio)
    video.write_videofile(output_path, codec=VIDEO_CODEC, audio_codec="aac", preset=PRESET, threads=4)
    video.close()
