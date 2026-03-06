export interface TranscriptWord {
  text: string;
  start: number;
  end: number;
}

export interface EvidencePin {
  label: string;
  timestamp: number;
  description: string;
}

export interface DemoResult {
  confidence: number; // 0–1
  transcript: TranscriptWord[];
  fullText: string;
  delivery: {
    speechRateWPM: number;
    pauseRatio: number; // 0–1
    fillerWords: { word: string; count: number }[];
    longestPauseAt: number; // seconds
  };
  structure: {
    opening: { detected: boolean; timestamp: number | null };
    signpost: { detected: boolean; timestamp: number | null };
    example: { detected: boolean; timestamp: number | null };
    conclusion: { detected: boolean; timestamp: number | null };
  };
  strengths: string[];
  nextSteps: string[];
  evidencePins: EvidencePin[];
}

export const SAMPLE_RESULT: DemoResult = {
  confidence: 0.82,
  fullText:
    "Good morning everyone. Today I'd like to talk about why our school library is my favourite place. First of all, it's incredibly peaceful — the moment you walk through the doors, the noise of the corridor just fades away. For example, last Tuesday I found a quiet corner near the window and read for a whole hour without anyone disturbing me. The light comes through the big windows and makes everything feel warm. Secondly, the library has an amazing collection. There are graphic novels, science books, and even audiobooks you can borrow. I think every student should spend at least one lunch break a week there. To sum up, the library is special because it's calm, full of great books, and open to everyone. Thank you for listening.",
  transcript: [
    { text: "Good", start: 0.2, end: 0.5 },
    { text: "morning", start: 0.5, end: 0.9 },
    { text: "everyone.", start: 0.9, end: 1.4 },
    { text: "Today", start: 1.6, end: 1.9 },
    { text: "I'd", start: 1.9, end: 2.1 },
    { text: "like", start: 2.1, end: 2.3 },
    { text: "to", start: 2.3, end: 2.4 },
    { text: "talk", start: 2.4, end: 2.7 },
    { text: "about", start: 2.7, end: 3.0 },
    { text: "why", start: 3.0, end: 3.3 },
    { text: "our", start: 3.3, end: 3.5 },
    { text: "school", start: 3.5, end: 3.8 },
    { text: "library", start: 3.8, end: 4.3 },
    { text: "is", start: 4.3, end: 4.5 },
    { text: "my", start: 4.5, end: 4.7 },
    { text: "favourite", start: 4.7, end: 5.2 },
    { text: "place.", start: 5.2, end: 5.7 },
    { text: "First", start: 6.2, end: 6.5 },
    { text: "of", start: 6.5, end: 6.6 },
    { text: "all,", start: 6.6, end: 7.0 },
    { text: "it's", start: 7.1, end: 7.3 },
    { text: "incredibly", start: 7.3, end: 7.9 },
    { text: "peaceful", start: 7.9, end: 8.5 },
    { text: "—", start: 8.5, end: 8.7 },
    { text: "the", start: 8.8, end: 9.0 },
    { text: "moment", start: 9.0, end: 9.4 },
    { text: "you", start: 9.4, end: 9.6 },
    { text: "walk", start: 9.6, end: 9.9 },
    { text: "through", start: 9.9, end: 10.2 },
    { text: "the", start: 10.2, end: 10.3 },
    { text: "doors,", start: 10.3, end: 10.8 },
    { text: "the", start: 10.9, end: 11.0 },
    { text: "noise", start: 11.0, end: 11.4 },
    { text: "of", start: 11.4, end: 11.5 },
    { text: "the", start: 11.5, end: 11.6 },
    { text: "corridor", start: 11.6, end: 12.1 },
    { text: "just", start: 12.1, end: 12.4 },
    { text: "fades", start: 12.4, end: 12.8 },
    { text: "away.", start: 12.8, end: 13.3 },
    { text: "For", start: 14.0, end: 14.2 },
    { text: "example,", start: 14.2, end: 14.8 },
    { text: "last", start: 14.9, end: 15.2 },
    { text: "Tuesday", start: 15.2, end: 15.7 },
    { text: "I", start: 15.7, end: 15.8 },
    { text: "found", start: 15.8, end: 16.1 },
    { text: "a", start: 16.1, end: 16.2 },
    { text: "quiet", start: 16.2, end: 16.6 },
    { text: "corner", start: 16.6, end: 17.0 },
    { text: "near", start: 17.0, end: 17.3 },
    { text: "the", start: 17.3, end: 17.4 },
    { text: "window.", start: 17.4, end: 18.0 },
    { text: "Secondly,", start: 25.0, end: 25.6 },
    { text: "the", start: 25.6, end: 25.7 },
    { text: "library", start: 25.7, end: 26.2 },
    { text: "has", start: 26.2, end: 26.4 },
    { text: "an", start: 26.4, end: 26.5 },
    { text: "amazing", start: 26.5, end: 27.0 },
    { text: "collection.", start: 27.0, end: 27.6 },
    { text: "To", start: 45.0, end: 45.2 },
    { text: "sum", start: 45.2, end: 45.5 },
    { text: "up,", start: 45.5, end: 45.9 },
    { text: "the", start: 46.0, end: 46.1 },
    { text: "library", start: 46.1, end: 46.6 },
    { text: "is", start: 46.6, end: 46.8 },
    { text: "special.", start: 46.8, end: 47.4 },
    { text: "Thank", start: 52.0, end: 52.3 },
    { text: "you", start: 52.3, end: 52.5 },
    { text: "for", start: 52.5, end: 52.7 },
    { text: "listening.", start: 52.7, end: 53.3 },
  ],
  delivery: {
    speechRateWPM: 138,
    pauseRatio: 0.18,
    fillerWords: [
      { word: "um", count: 0 },
      { word: "uh", count: 1 },
      { word: "like", count: 0 },
    ],
    longestPauseAt: 24.5,
  },
  structure: {
    opening: { detected: true, timestamp: 0.2 },
    signpost: { detected: true, timestamp: 6.2 },
    example: { detected: true, timestamp: 14.0 },
    conclusion: { detected: true, timestamp: 45.0 },
  },
  strengths: [
    "Clear and confident opening that sets up the topic immediately.",
    "Effective use of a concrete example (the Tuesday library visit) to support the argument.",
    "Good pace at 138 WPM — easy to follow with natural pauses.",
  ],
  nextSteps: [
    "Try to vary your vocal tone more when describing emotional moments.",
    "Add a second example to strengthen the middle section of your talk.",
    "Shorten the longest pause (6.5s at 0:24) — use a bridging phrase instead.",
  ],
  evidencePins: [
    { label: "Strong opening", timestamp: 0.5, description: "Greeted the audience and stated the topic clearly." },
    { label: "Concrete example", timestamp: 14.5, description: "Used a specific personal anecdote with time and place detail." },
    { label: "Clear conclusion", timestamp: 45.2, description: "Summarised the three key points and ended with thanks." },
  ],
};

/**
 * Simulates processing with realistic staged progress.
 * Calls onStage with stage label, and resolves with the sample result.
 */
export function simulateProcessing(
  onStage: (stage: string, progress: number) => void
): Promise<DemoResult> {
  return new Promise((resolve) => {
    const stages = [
      { label: "Transcribing…", progress: 30, delay: 2500 },
      { label: "Analysing delivery…", progress: 60, delay: 2000 },
      { label: "Finding evidence…", progress: 85, delay: 2000 },
      { label: "Generating feedback…", progress: 100, delay: 1500 },
    ];

    let i = 0;
    const next = () => {
      if (i >= stages.length) {
        resolve(SAMPLE_RESULT);
        return;
      }
      const s = stages[i];
      onStage(s.label, s.progress);
      i++;
      setTimeout(next, s.delay);
    };
    next();
  });
}
