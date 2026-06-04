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


def reduce_noise(input_path, output_path, cutoff_freq=200):
    """Basic noise reduction using high-pass filter to remove low-frequency hum/noise."""
    try:
        from scipy.io import wavfile
        from scipy.signal import butter, filtfilt
        import numpy as np
        import tempfile
        import os

        # Convert to wav first using moviepy
        temp_wav = tempfile.mktemp(suffix=".wav")
        clip = mp.AudioFileClip(input_path)
        clip.write_audiofile(temp_wav, codec='pcm_s16le')
        clip.close()

        # Apply high-pass filter
        sample_rate, data = wavfile.read(temp_wav)
        nyquist = sample_rate / 2
        normalized_cutoff = cutoff_freq / nyquist

        if normalized_cutoff >= 1.0:
            normalized_cutoff = 0.9

        b, a = butter(5, normalized_cutoff, btype='high')

        if len(data.shape) > 1:
            # Stereo
            filtered = np.zeros_like(data)
            for ch in range(data.shape[1]):
                filtered[:, ch] = filtfilt(b, a, data[:, ch].astype(np.float64)).astype(data.dtype)
        else:
            # Mono
            filtered = filtfilt(b, a, data.astype(np.float64)).astype(data.dtype)

        wavfile.write(temp_wav, sample_rate, filtered)

        # Convert back to original format
        out_clip = mp.AudioFileClip(temp_wav)
        out_clip.write_audiofile(output_path)
        out_clip.close()

        os.remove(temp_wav)
        print("Noise reduction applied")
    except ImportError:
        raise ImportError("scipy is required for noise reduction. Install with: pip install scipy")


def normalize_audio(input_path, output_path, target_db=-3.0):
    """Normalize audio levels to a target peak dB."""
    import numpy as np
    import tempfile
    import os

    temp_wav = tempfile.mktemp(suffix=".wav")
    clip = mp.AudioFileClip(input_path)
    clip.write_audiofile(temp_wav, codec='pcm_s16le')
    
    fps = clip.fps
    clip.close()

    try:
        from scipy.io import wavfile
        sample_rate, data = wavfile.read(temp_wav)
    except ImportError:
        # Fallback: use moviepy only
        clip = mp.AudioFileClip(temp_wav)
        # Simple normalization via volumex
        max_vol = 1.0
        clip = clip.volumex(1.0 / max_vol if max_vol > 0 else 1.0)
        clip.write_audiofile(output_path)
        clip.close()
        os.remove(temp_wav)
        return

    float_data = data.astype(np.float64)
    peak = np.max(np.abs(float_data))
    
    if peak == 0:
        print("Audio is silent, nothing to normalize")
        os.remove(temp_wav)
        return

    target_linear = 10 ** (target_db / 20.0) * (32767 if data.dtype == np.int16 else 1.0)
    gain = target_linear / peak
    
    normalized = (float_data * gain).clip(-32768, 32767).astype(data.dtype)
    
    from scipy.io import wavfile as wf
    wf.write(temp_wav, sample_rate, normalized)

    out_clip = mp.AudioFileClip(temp_wav)
    out_clip.write_audiofile(output_path)
    out_clip.close()
    os.remove(temp_wav)
    print(f"Audio normalized to {target_db} dB peak")


def transcribe_audio(input_path):
    """Transcribe audio/video file to text using Google Web Speech API."""
    import speech_recognition as sr
    import tempfile
    import os
    import moviepy.editor as mp
    
    # Convert to WAV first since SpeechRecognition works best with WAV
    temp_wav = tempfile.mktemp(suffix=".wav")
    try:
        clip = mp.AudioFileClip(input_path)
        clip.write_audiofile(temp_wav, codec='pcm_s16le', verbose=False, logger=None)
        clip.close()
    except Exception as e:
        return False, f"Failed to extract audio: {str(e)}"
    
    r = sr.Recognizer()
    try:
        with sr.AudioFile(temp_wav) as source:
            audio_data = r.record(source)
            text = r.recognize_google(audio_data)
        return True, text
    except sr.UnknownValueError:
        return False, "Speech was unintelligible or no speech detected."
    except sr.RequestError as e:
        return False, f"API Request Error (Check internet connection or API limits): {e}"
    except Exception as e:
        return False, str(e)
    finally:
        if os.path.exists(temp_wav):
            try: os.remove(temp_wav)
            except: pass

