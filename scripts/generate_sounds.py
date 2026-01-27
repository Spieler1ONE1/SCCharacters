import wave
import math
import struct
import os

def create_beep(filename, duration=0.1, frequency=440.0, volume=0.5):
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        data = bytearray()
        for i in range(n_samples):
            # Simple sine wave
            t = float(i) / sample_rate
            value = int(volume * 32767.0 * math.sin(2.0 * math.pi * frequency * t))
            # Envelope to avoid clicking at start/end
            if i < 100: value = int(value * (i/100))
            if i > n_samples - 100: value = int(value * ((n_samples - i)/100))
            
            data.extend(struct.pack('<h', value))
            
        wav_file.writeframes(data)
    print(f"Generated {filename}")

def main():
    base_dir = r"c:\Users\joeln\Desktop\SCcharacters\src\assets\sounds"
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    # Hover / Tick: Short, high pitch, very short
    create_beep(os.path.join(base_dir, "hover.wav"), duration=0.03, frequency=800.0, volume=0.2)
    
    # Click: Standard UI click
    create_beep(os.path.join(base_dir, "click.wav"), duration=0.05, frequency=1200.0, volume=0.3)
    
    # Success: Chord-like (arpeggio not easy here, just a pleasant tone)
    create_beep(os.path.join(base_dir, "success.wav"), duration=0.4, frequency=660.0, volume=0.4)
    
    # Error: Low buzz
    create_beep(os.path.join(base_dir, "error.wav"), duration=0.3, frequency=150.0, volume=0.4)
    
    # Startup
    create_beep(os.path.join(base_dir, "startup.wav"), duration=0.5, frequency=440.0, volume=0.3)
    
    # Trash
    create_beep(os.path.join(base_dir, "trash.wav"), duration=0.1, frequency=200.0, volume=0.3)

    # Card Hover: Very light, high pitch 'glint' (Glass-like), subtle
    create_beep(os.path.join(base_dir, "card_hover.wav"), duration=0.02, frequency=1600.0, volume=0.08)

    # Sci-Fi Login: Elegant Glassy Boot with Ambient Tail
    create_elegant_glass_boot(os.path.join(base_dir, "login.wav"), duration=6.0)

def create_elegant_glass_boot(filename, duration=6.0):
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    
    # Concept: "Airy" startup -> Ambience.
    freqs = [523.25, 783.99, 1046.50]
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        
        data = bytearray()
        for i in range(n_samples):
            t = float(i) / sample_rate
            
            val = 0.0
            for f in freqs:
                val += math.sin(2.0 * math.pi * f * t)
                val += 0.5 * math.sin(2.0 * math.pi * (f + 1.5) * t)
            
            val = val / (len(freqs) * 1.5)
            
            # Ping at start
            ping = 0.0
            if t < 0.2:
                ping_freq = 2093.0 
                ping_env = math.exp(-20.0 * t) 
                ping = math.sin(2.0 * math.pi * ping_freq * t) * ping_env * 0.3
            
            # Master Envelope: Swell -> Sustain (Ambience) -> Fade Out
            # 0.0 - 1.0s: Swell IN
            # 1.0 - 5.0s: Sustain at lower volume (Ambience)
            # 5.0 - 6.0s: Fade OUT
            
            env = 0.0
            if t < 1.0:
                # Swell up
                x = t / 1.0
                env = 0.5 * (1 - math.cos(x * math.pi))
            elif t < 5.0:
                # Sustain (slowly dip to 40% volume for ambience)
                # Linear interpolation from 1.0 down to 0.4 over 4 seconds is boring?
                # Let's oscillate slightly or just hold steady/slow decay.
                # Let's slowly decay to 0.3 to sit in background
                progress = (t - 1.0) / 4.0
                env = 1.0 - (progress * 0.7) # Goes from 1.0 down to 0.3
            else:
                # Final Fade Out
                rel_t = (t - 5.0) / 1.0
                current_vol = 0.3 # Starting from where sustain left off
                env = current_vol * (1.0 - rel_t)
            
            final_mix = (val * env) + ping
            
            # Volume Adjustment
            final_sample = int(final_mix * 32767.0 * 0.25)
            data.extend(struct.pack('<h', final_sample))
            
        wav_file.writeframes(data)
    print(f"Generated {filename}")

if __name__ == "__main__":
    main()
