import moviepy as mp
from moviepy.video.VideoClip import TextClip, ColorClip
from moviepy.audio.AudioClip import AudioClip, CompositeAudioClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.compositing.concatenate import concatenate_videoclips
from moviepy.video.fx.CrossFadeIn import CrossFadeIn
from moviepy.audio.fx.AudioFadeOut import AudioFadeOut
import numpy as np
import random

W, H = 1920, 1080
FPS = 24
SAFE_PCT = 0.1

SAFE_X1 = int(W * SAFE_PCT)
SAFE_Y1 = int(H * SAFE_PCT)
SAFE_W = int(W * (1 - 2 * SAFE_PCT))
SAFE_H = int(H * (1 - 2 * SAFE_PCT))

def make_safe_text(txt, fontsize=60, color='white', stroke=2, font='DejaVu-Sans'):
    # Updated for MoviePy v2.x: fontsize -> font_size, set_position -> with_position
    return (TextClip(text=txt, font_size=fontsize, color=color, font=font,
                     stroke_color='black', stroke_width=stroke,
                     size=(SAFE_W, SAFE_H), method='caption')
            .with_position(('center', 'center')))

def beep(duration, freq=800, vol=0.3):
    def make_frame(t):
        # Handle both scalar and array 't' for MoviePy v2 compatibility
        t_array = np.asanyarray(t)
        return (vol * np.sin(2 * np.pi * freq * t_array)).reshape(-1, 1)
    return AudioClip(make_frame, duration=duration).with_fps(FPS)

hook = ColorClip(size=(W,H), color=(0,0,0), duration=5).without_audio()
hook = CompositeVideoClip([hook, make_safe_text("GUARDIAN ANGEL: Climate Action, Automated.", 70)])

boot = ColorClip(size=(W,H), color=(0,0,0), duration=25)
lines = ["INITIALIZING SENSOR ARRAY...", "CALIBRATING PARTICLE FILTERS...",
         "ESTABLISHING SECURE CHANNEL...", "SYSTEM READY."]
clips = []
for i, line in enumerate(lines):
    t = make_safe_text(line, 40, "#00FFAA")
    t = t.with_start(i*5).with_duration(4).with_effects([CrossFadeIn(0.5)])
    clips.append(t)
sub1 = make_safe_text("Real-time industrial intelligence.", 30, "#AAAAAA")
sub1 = sub1.with_position(('center', SAFE_Y1 + SAFE_H - 60))
boot = CompositeVideoClip([boot] + clips + [sub1])
boot = boot.with_audio(CompositeAudioClip([beep(25, 200, 0.1), beep(0.02, 1500, 0.2).with_start(2)]))

industry = ColorClip(size=(W, H), color=(40,40,50), duration=50)
placeholder = TextClip(text="INDUSTRIAL FOOTAGE HERE", font_size=50, color='white', font='DejaVu-Sans',
                       stroke_color='black', stroke_width=2).with_position('center')
industry = CompositeVideoClip([industry, placeholder])
sub2 = make_safe_text("Capturing air readings from heavy stacks.", 32, "#CCCCCC")
sub2 = sub2.with_position(('center', SAFE_Y1 + SAFE_H - 60))
industry = CompositeVideoClip([industry, sub2])
industry = industry.with_audio(beep(50, 100, 0.05))

ledger_bg = ColorClip(size=(W,H), color=(10,10,15), duration=25)
hash_clips = []
for i in range(20):
    h = ''.join(random.choices('0123456789ABCDEF', k=64))
    t = make_safe_text(f"0x{h}", 20, "#66CCFF")
    t = t.with_position((SAFE_X1 + 20, SAFE_Y1 + i*25)).with_start(i*1.2)
    hash_clips.append(t)
sub3 = make_safe_text("Immutable, fingerprint-verified records.", 32, "#CCCCCC")
sub3 = sub3.with_position(('center', SAFE_Y1 + SAFE_H - 60))
ledger = CompositeVideoClip([ledger_bg] + hash_clips + [sub3])
ledger = ledger.with_audio(beep(25, 600, 0.15))

final_bg = ColorClip(size=(W,H), color=(0,0,0), duration=15).with_effects([CrossFadeIn(0.5)])
headline2 = make_safe_text("50 Million Tonnes Mitigated.\nSerious impact.", 80)
final = CompositeVideoClip([final_bg, headline2])
swell = beep(15, 250, 0.2)
final = final.with_audio(swell.with_effects([AudioFadeOut(3.0)]))

final_video = concatenate_videoclips([hook, boot, industry, ledger, final])
final_video.write_videofile("guardian_angel_draft.mp4", fps=FPS, codec='libx264', audio_codec='aac')
