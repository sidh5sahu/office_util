import moviepy.editor as mp
from common_utils import parse_time

def convert_audio(input_path, output_path):
    clip = mp.AudioFileClip(input_path)
    clip.write_audiofile(output_path)
    clip.close()

def cut_audio(input_path, output_path, start_time, end_time):
    t1 = parse_time(str(start_time))
    t2 = parse_time(str(end_time))
    
    with mp.AudioFileClip(input_path) as clip:
         if t2 == 0 or t2 > clip.duration: t2 = clip.duration
         new = clip.subclip(t1, t2)
         new.write_audiofile(output_path)

def join_audio(input_paths, output_path):
    if not input_paths: return
    clips = [mp.AudioFileClip(p) for p in input_paths]
    final = mp.concatenate_audioclips(clips)
    final.write_audiofile(output_path)
    for c in clips: c.close()

def adjust_volume(input_path, output_path, factor=1.5):
    """Adjust audio volume. factor > 1 = louder, < 1 = quieter."""
    clip = mp.AudioFileClip(input_path)
    clip = clip.volumex(factor)
    clip.write_audiofile(output_path)
    clip.close()

def add_fade(input_path, output_path, fade_in=0, fade_out=0):
    """Add fade in and/or fade out effects to audio."""
    clip = mp.AudioFileClip(input_path)
    
    if fade_in > 0:
        clip = clip.audio_fadein(fade_in)
    if fade_out > 0:
        clip = clip.audio_fadeout(fade_out)
    
    clip.write_audiofile(output_path)
    clip.close()
