import numpy as np
import pygame

class SoundEngine:
    def __init__(self, enabled=True):
        self.enabled = enabled
        self.sample_rate = 44100
        self.sounds = {}
        
        if not self.enabled:
            return

        try:
            # Pre-init mixer if not already initialized
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=self.sample_rate, size=-16, channels=2, buffer=512)

            self.sounds = {
                "link": self._make_tone(freq=587.33, duration=0.22),                   # D5 Chime
                "cycle": self._make_buzz(freq=120.0, duration=0.30),                   # Harsh square buzz
                "undo": self._make_sweep(start_f=650, end_f=220, duration=0.15),      # Descending swoosh
                "redo": self._make_sweep(start_f=220, end_f=650, duration=0.15),      # Ascending swoosh
                "win": self._make_chord([523.25, 659.25, 783.99, 1046.50], 0.65)      # C Major Triad
            }
        except Exception as e:
            print(f"[SoundEngine Warning] Audio hardware initialization failed: {e}")
            self.enabled = False

    def _apply_anti_click(self, wave):
        """Applies a 5ms linear fade-in and fade-out to prevent pop/click artifacts."""
        fade_samples = int(self.sample_rate * 0.005)
        if len(wave) > 2 * fade_samples:
            fade_in = np.linspace(0.0, 1.0, fade_samples)
            fade_out = np.linspace(1.0, 0.0, fade_samples)
            wave[:fade_samples] *= fade_in
            wave[-fade_samples:] *= fade_out
        return wave

    def _make_tone(self, freq, duration):
        n_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, n_samples, False)
        wave = np.sin(2 * np.pi * freq * t)
        envelope = np.exp(-5 * t / duration)
        wave = self._apply_anti_click(wave * envelope)
        audio = (wave * 32767 * 0.35).astype(np.int16)
        stereo = np.column_stack((audio, audio))
        return pygame.sndarray.make_sound(stereo)

    def _make_buzz(self, freq, duration):
        n_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, n_samples, False)
        # Saturated square wave
        wave = np.sign(np.sin(2 * np.pi * freq * t))
        envelope = np.exp(-3 * t / duration)
        wave = self._apply_anti_click(wave * envelope)
        audio = (wave * 32767 * 0.22).astype(np.int16)
        stereo = np.column_stack((audio, audio))
        return pygame.sndarray.make_sound(stereo)

    def _make_sweep(self, start_f, end_f, duration):
        """Uses cumulative phase integration (np.cumsum) to prevent phase discontinuities."""
        n_samples = int(self.sample_rate * duration)
        freqs = np.linspace(start_f, end_f, n_samples)
        phase = 2 * np.pi * np.cumsum(freqs) / self.sample_rate
        wave = np.sin(phase)
        wave = self._apply_anti_click(wave)
        audio = (wave * 32767 * 0.30).astype(np.int16)
        stereo = np.column_stack((audio, audio))
        return pygame.sndarray.make_sound(stereo)

    def _make_chord(self, freqs, duration):
        n_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, n_samples, False)
        wave = sum(np.sin(2 * np.pi * f * t) for f in freqs) / len(freqs)
        envelope = np.exp(-3 * t / duration)
        wave = self._apply_anti_click(wave * envelope)
        audio = (wave * 32767 * 0.35).astype(np.int16)
        stereo = np.column_stack((audio, audio))
        return pygame.sndarray.make_sound(stereo)

    def play(self, sound_name):
        if self.enabled and sound_name in self.sounds:
            self.sounds[sound_name].play()
