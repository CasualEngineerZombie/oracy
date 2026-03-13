import { describe, it, expect, vi, beforeEach } from "vitest";
import { render } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import VideoUploader from "../components/VideoUploader";

// Mock the API hooks
vi.mock("@/lib/api/assessments", () => ({
  useGetUploadUrl: () => ({
    mutateAsync: vi.fn().mockResolvedValue({
      upload_url: "https://test-bucket.s3.amazonaws.com/test-key",
      file_key: "recordings/test-id/test-video.mp4",
      assessment_id: "test-id",
      expires_in: 3600,
    }),
  }),
  useUpdateAssessment: () => ({
    mutateAsync: vi.fn().mockResolvedValue({}),
  }),
}));

vi.mock("@/hooks/use-toast", () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

const renderWithRouter = (component: React.ReactNode) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe("VideoUploader", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the uploader component", () => {
    const { getByText } = renderWithRouter(<VideoUploader assessmentId="test-id" />);
    
    expect(getByText("Upload Recording")).toBeInTheDocument();
    expect(getByText("Drop your video here or click to browse")).toBeInTheDocument();
  });

  it("has upload button initially disabled", () => {
    const { getByRole } = renderWithRouter(<VideoUploader assessmentId="test-id" />);
    
    const uploadButton = getByRole("button", { name: /start upload/i });
    expect(uploadButton).toBeDisabled();
  });

  it("displays supported formats info", () => {
    const { getByText } = renderWithRouter(<VideoUploader assessmentId="test-id" />);
    
    expect(getByText("Supports MP4, WebM, QuickTime (max 500MB)")).toBeInTheDocument();
  });
});
