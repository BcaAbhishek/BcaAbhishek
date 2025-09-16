# import threading, time
# import numpy as np
# import sounddevice as sd

# class DesktopAudioListener:
#     def __init__(self, sample_rate=44100, chunk=2048, threshold=0.02, cooldown=3.0):
#         self.sample_rate = sample_rate
#         self.chunk = chunk
#         self.threshold = threshold
#         self.cooldown = cooldown
#         self._running = False
#         self._last = 0.0
#         self.device = self._find_input_device()

#     def _find_input_device(self):
#         """Auto-select a microphone with input channels"""
#         devices = sd.query_devices()
#         for i, dev in enumerate(devices):
#             if dev['max_input_channels'] > 0:
#                 print(f"[INFO] Using input device {i}: {dev['name']}")
#                 return i
#         raise RuntimeError("No microphone input devices found!")

#     def start(self, on_whistle, on_volume=None):
#         if self._running:
#             return
#         self._running = True

#         def _loop():
#             while self._running:
#                 try:
#                     data = sd.rec(
#                         self.chunk,
#                         samplerate=self.sample_rate,
#                         channels=1,
#                         dtype='float32',
#                         device=self.device
#                     )
#                     sd.wait()
#                     rms = float(np.sqrt(np.mean(data**2)))

#                     # 🔊 send live volume level
#                     if on_volume:
#                         try:
#                             on_volume(rms)
#                         except:
#                             pass

#                     if rms > self.threshold and (time.time() - self._last) > self.cooldown:
#                         self._last = time.time()
#                         try:
#                             on_whistle()
#                         except Exception:
#                             pass
#                 except Exception as e:
#                     print("[ERROR] Mic capture failed:", e)
#                 time.sleep(0.01)

#         t = threading.Thread(target=_loop, daemon=True)
#         t.start()

#     def stop(self):
#         self._running = False
# desktop_audio.py
import threading
import time
import numpy as np
import sounddevice as sd

class DesktopAudioListener:
    """
    Detects whistles using FFT-based, tonal detection to avoid music false positives.

    Parameters you can tune:
      - sample_rate: audio sample rate
      - chunk: number of samples per frame (bigger = better freq resolution)
      - threshold_rms: minimum RMS energy to consider (ignore very quiet noise)
      - peak_ratio: peak_mag / total_energy must be >= this (whistles are narrowband)
      - flatness_thresh: spectral flatness must be <= this (whistles -> low flatness)
      - min_peak_freq / max_peak_freq: accept peaks only in this freq range (Hz)
      - cooldown: seconds to wait between whistle detections
      - debug: print debug info (rms, peak freq, ratio, flatness)
    """

    def __init__(self,
                 sample_rate=44100,
                 chunk=4096,
                 threshold_rms=0.004,
                 peak_ratio=0.35,
                 flatness_thresh=0.25,
                 min_peak_freq=700,
                 max_peak_freq=9000,
                 cooldown=1.5,
                 debug=False):
        self.sample_rate = sample_rate
        self.chunk = chunk
        self.threshold_rms = threshold_rms
        self.peak_ratio = peak_ratio
        self.flatness_thresh = flatness_thresh
        self.min_peak_freq = min_peak_freq
        self.max_peak_freq = max_peak_freq
        self.cooldown = cooldown
        self.debug = debug

        self._running = False
        self._last = 0.0
        self.device = self._find_input_device()

    def _find_input_device(self):
        """Auto-selects first device with input channels."""
        devices = sd.query_devices()
        for i, dev in enumerate(devices):
            if dev['max_input_channels'] > 0:
                print(f"[INFO] Using input device {i}: {dev['name']}")
                return i
        raise RuntimeError("No microphone input devices found!")

    def start(self, on_whistle, on_volume=None):
        """
        on_whistle(): callback invoked when whistle detected
        on_volume(rms): callback for raw RMS level (0..1)
        """
        if self._running:
            return
        self._running = True

        def _loop():
            while self._running:
                try:
                    # capture
                    data = sd.rec(self.chunk,
                                  samplerate=self.sample_rate,
                                  channels=1,
                                  dtype='float32',
                                  device=self.device)
                    sd.wait()
                    buf = np.asarray(data).reshape(-1).astype('float32')

                    # apply window for better spectral estimates
                    win = np.hanning(len(buf))
                    buf_win = buf * win

                    # RMS energy
                    rms = float(np.sqrt(np.mean(buf_win * buf_win)))

                    # volume callback
                    if on_volume:
                        try:
                            on_volume(rms)
                        except Exception:
                            pass

                    # quick reject: too quiet
                    if rms < self.threshold_rms:
                        time.sleep(0.01)
                        continue

                    # FFT
                    N = len(buf_win)
                    spec = np.fft.rfft(buf_win)
                    mag = np.abs(spec)
                    mag[0] = 0.0  # ignore DC

                    total_energy = np.sum(mag) + 1e-12
                    peak_idx = int(np.argmax(mag))
                    peak_mag = float(mag[peak_idx])
                    peak_freq = peak_idx * self.sample_rate / float(N)

                    peak_ratio = peak_mag / total_energy  # narrowbandness
                    # spectral flatness: tonal -> small flatness
                    eps = 1e-12
                    geo_mean = float(np.exp(np.mean(np.log(mag + eps))))
                    arith_mean = float(np.mean(mag + eps))
                    flatness = geo_mean / (arith_mean + eps)

                    if self.debug:
                        print(f"[DBG] rms={rms:.5f} freq={peak_freq:.0f}Hz "
                              f"ratio={peak_ratio:.3f} flat={flatness:.3f}")

                    # detection decision
                    now = time.time()
                    if (
                        (now - self._last) > self.cooldown
                        and self.min_peak_freq <= peak_freq <= self.max_peak_freq
                        and peak_ratio >= self.peak_ratio
                        and flatness <= self.flatness_thresh
                    ):
                        self._last = now
                        try:
                            on_whistle()
                        except Exception:
                            pass

                except Exception as e:
                    # printing the exception is helpful for debugging mic/device issues
                    print("[ERROR] Mic capture error:", e)
                time.sleep(0.01)

        t = threading.Thread(target=_loop, daemon=True)
        t.start()

    def stop(self):
        self._running = False
