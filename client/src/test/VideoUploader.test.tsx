import { describe, it, expect, vi } from "vitest";

// Simple import test - verify the new components can be imported
describe("VideoUploader imports", () => {
  it("should be able to import VideoUploader component", async () => {
    const { default: VideoUploader } = await import("../components/VideoUploader");
    expect(VideoUploader).toBeDefined();
  });

  it("should export useGetUploadUrl from assessments API", async () => {
    const api = await import("@/lib/api/assessments");
    expect(api.useGetUploadUrl).toBeDefined();
  });

  it("should export useBulkCreateAssessment from assessments API", async () => {
    const api = await import("@/lib/api/assessments");
    expect(api.useBulkCreateAssessment).toBeDefined();
  });
});
