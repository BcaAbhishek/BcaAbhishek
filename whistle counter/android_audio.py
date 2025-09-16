# android_audio.py
from jnius import autoclass
import threading, time, array

AudioRecord = autoclass('android.media.AudioRecord')
AudioFormat = autoclass('android.media.AudioFormat')
MediaRecorder = autoclass('android.media.MediaRecorder')

class AndroidAudioListener:
    def __init__(self, sample_rate=44100, threshold=0.15, cooldown=3.0):
        self.sample_rate = sample_rate
        self.threshold = threshold
        self.cooldown = cooldown
        self._running = False
        self._last = 0.0

        channel_config = AudioFormat.CHANNEL_IN_MONO
        encoding = AudioFormat.ENCODING_PCM_16BIT
        self._min_buf = AudioRecord.getMinBufferSize(self.sample_rate, channel_config, encoding)
        if self._min_buf <= 0:
            self._min_buf = self.sample_rate * 2

        self._buf = array.array('h', [0]) * (self._min_buf // 2)
        self._recorder = AudioRecord(MediaRecorder.AudioSource.MIC,
                                     self.sample_rate,
                                     channel_config,
                                     encoding,
                                     self._min_buf)

    def start(self, on_whistle):
        if self._running:
            return
        self._running = True
        self._recorder.startRecording()

        def _loop():
            while self._running:
                read = self._recorder.read(self._buf, 0, len(self._buf))
                if read > 0:
                    s = sum(v * v for v in self._buf[:read])
                    rms = (s / max(1, read)) ** 0.5
                    normalized = rms / 32768.0
                    if normalized > self.threshold and (time.time() - self._last) > self.cooldown:
                        self._last = time.time()
                        try:
                            on_whistle()
                        except Exception:
                            pass
                time.sleep(0.01)

        threading.Thread(target=_loop, daemon=True).start()

    def stop(self):
        self._running = False
        try:
            self._recorder.stop()
            self._recorder.release()
        except Exception:
            pass
