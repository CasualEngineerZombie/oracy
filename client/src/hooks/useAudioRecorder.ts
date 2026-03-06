import { useState, useRef, useCallback, useEffect } from "react";

export type RecorderState = "idle" | "recording" | "stopped";

interface UseAudioRecorderReturn {
  state: RecorderState;
  seconds: number;
  level: number; // 0–1 normalised input level
  audioBlob: Blob | null;
  audioUrl: string | null;
  start: () => Promise<void>;
  stop: () => void;
  reset: () => void;
  permissionGranted: boolean;
  permissionError: string | null;
  requestPermission: () => Promise<boolean>;
}

export function useAudioRecorder(maxSeconds = 60): UseAudioRecorderReturn {
  const [state, setState] = useState<RecorderState>("idle");
  const [seconds, setSeconds] = useState(0);
  const [level, setLevel] = useState(0);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [permissionGranted, setPermissionGranted] = useState(false);
  const [permissionError, setPermissionError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animFrameRef = useRef<number>(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const cleanup = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    cancelAnimationFrame(animFrameRef.current);
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    analyserRef.current = null;
    mediaRecorderRef.current = null;
  }, []);

  useEffect(() => () => cleanup(), [cleanup]);

  const requestPermission = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      // Set up analyser for level meter
      const ctx = new AudioContext();
      const source = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyserRef.current = analyser;
      streamRef.current = stream;

      // Start level meter animation
      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      const tick = () => {
        analyser.getByteTimeDomainData(dataArray);
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
          const v = (dataArray[i] - 128) / 128;
          sum += v * v;
        }
        setLevel(Math.min(1, Math.sqrt(sum / dataArray.length) * 3));
        animFrameRef.current = requestAnimationFrame(tick);
      };
      tick();

      setPermissionGranted(true);
      setPermissionError(null);
      return true;
    } catch (err: any) {
      setPermissionError(err.message || "Microphone access denied");
      setPermissionGranted(false);
      return false;
    }
  }, []);

  const start = useCallback(async () => {
    if (!streamRef.current) return;
    chunksRef.current = [];
    setAudioBlob(null);
    setAudioUrl(null);
    setSeconds(0);

    const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
      ? "audio/webm;codecs=opus"
      : "audio/webm";
    const recorder = new MediaRecorder(streamRef.current, { mimeType });
    mediaRecorderRef.current = recorder;

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };

    recorder.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: mimeType });
      setAudioBlob(blob);
      setAudioUrl(URL.createObjectURL(blob));
    };

    recorder.start(500); // collect chunks every 500ms
    setState("recording");

    timerRef.current = setInterval(() => {
      setSeconds((prev) => {
        if (prev >= maxSeconds - 1) {
          recorder.stop();
          setState("stopped");
          if (timerRef.current) clearInterval(timerRef.current);
          return maxSeconds;
        }
        return prev + 1;
      });
    }, 1000);
  }, [maxSeconds]);

  const stop = useCallback(() => {
    if (mediaRecorderRef.current?.state === "recording") {
      mediaRecorderRef.current.stop();
    }
    if (timerRef.current) clearInterval(timerRef.current);
    setState("stopped");
  }, []);

  const reset = useCallback(() => {
    setAudioBlob(null);
    setAudioUrl(null);
    setSeconds(0);
    setState("idle");
    chunksRef.current = [];
  }, []);

  return {
    state,
    seconds,
    level,
    audioBlob,
    audioUrl,
    start,
    stop,
    reset,
    permissionGranted,
    permissionError,
    requestPermission,
  };
}
