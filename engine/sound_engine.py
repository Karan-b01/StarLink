import numpy as np
import pygame

class SoundEngine:
    def __init__(self, enabled=True):
        self.enabled = enabled
        self.music_enabled = True
        self.sample_rate = 44100
        self.sounds = {}
        self.music_sound = None
        self.music_channel = None
        
        if not self.enabled:
            return

        try:
            # Pre-init mixer if not already initialized
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=self.sample_rate, size=-16, channels=2, buffer=512)
            if pygame.mixer.get_num_channels() < 16:
                pygame.mixer.set_num_channels(16)

            self.sounds = {
                "link": self._make_tone(freq=587.33, duration=0.22),                   # D5 Chime
                "cycle": self._make_buzz(freq=120.0, duration=0.30),                   # Harsh square buzz
                "undo": self._make_sweep(start_f=650, end_f=220, duration=0.15),      # Descending swoosh
                "redo": self._make_sweep(start_f=220, end_f=650, duration=0.15),      # Ascending swoosh
                "win": self._make_chord([523.25, 659.25, 783.99, 1046.50], 0.65)      # C Major Triad
            }
            self.music_sound = self._make_ambient_loop()
            self.music_channel = pygame.mixer.Channel(15)
            self.set_music(True)
        except Exception as e:
            print(f"[SoundEngine Warning] Audio hardware initialization failed: {e}")
            self.enabled = False
            self.music_enabled = False

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

    def _make_ambient_loop(self):
        """Synthesize a slow space-ambient theme with chords and soft bell notes."""
        duration = 16.0
        n_samples = int(self.sample_rate * duration)
        t = np.arange(n_samples, dtype=np.float64) / self.sample_rate
        wave = np.zeros(n_samples, dtype=np.float64)

        # Four mellow minor-key chords, one per four-beat bar at 60 BPM.
        progression = [
            (65.41, 77.78, 98.00),    # C minor
            (51.91, 65.41, 77.78),    # A-flat
            (77.78, 98.00, 116.54),   # E-flat
            (58.27, 73.42, 87.31),    # B-flat
        ]
        for bar, chord in enumerate(progression):
            start = bar * 4.0
            mask = (t >= start) & (t < start + 4.0)
            local_t = t[mask] - start
            attack = np.clip(local_t / 0.65, 0.0, 1.0)
            release = np.clip((4.0 - local_t) / 0.8, 0.0, 1.0)
            envelope = np.minimum(attack, release) * (0.86 + 0.14 * np.sin(2 * np.pi * local_t / 4.0) ** 2)
            for index, frequency in enumerate(chord):
                volume = (0.078, 0.048, 0.028)[index]
                wave[mask] += volume * envelope * np.sin(2 * np.pi * frequency * t[mask])

        # A simple arpeggio supplies a gentle tune above the sustained chords.
        melody = [
            (0, 523.25), (1, 622.25), (2, 783.99), (3, 622.25),
            (4, 523.25), (5, 622.25), (6, 830.61), (7, 783.99),
            (8, 466.16), (9, 587.33), (10, 783.99), (11, 932.33),
            (12, 698.46), (13, 587.33), (14, 466.16), (15, 587.33),
        ]
        for start, frequency in melody:
            mask = (t >= start) & (t < min(start + 0.92, duration))
            note_t = t[mask] - start
            attack = np.clip(note_t / 0.025, 0.0, 1.0)
            decay = np.exp(-3.2 * note_t)
            bell = np.sin(2 * np.pi * frequency * note_t) + 0.18 * np.sin(4 * np.pi * frequency * note_t)
            wave[mask] += 0.038 * attack * decay * bell

        # Fade only the loop boundary to prevent a click when it repeats.
        fade_len = int(self.sample_rate * 0.35)
        fade = np.linspace(0.0, 1.0, fade_len)
        wave[:fade_len] *= fade
        wave[-fade_len:] *= fade[::-1]
        wave = np.clip(wave, -0.24, 0.24)
        audio = (wave * 32767 * 0.48).astype(np.int16)
        stereo = np.column_stack((audio, audio))
        return pygame.sndarray.make_sound(stereo)

    def set_music(self, enabled):
        """Start or stop the independent ambient music channel."""
        self.music_enabled = bool(enabled)
        if self.music_channel is None or self.music_sound is None:
            return
        if self.music_enabled:
            if not self.music_channel.get_busy():
                self.music_channel.play(self.music_sound, loops=-1)
        else:
            self.music_channel.stop()

    def play(self, sound_name):
        if self.enabled and sound_name in self.sounds:
            self.sounds[sound_name].play()
