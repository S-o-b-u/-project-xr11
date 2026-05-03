import axios from "axios";

import type { GenerateReportSuccessResponse } from "@/types/report";

const GENERATE_REPORT_URL =
  "http://localhost:8000/api/generate-report";

/**
 * Uploads an image file and returns the structured report API payload.
 * Uses `FormData` so the request is sent as multipart/form-data (field name `file`).
 */
export async function generateReport(
  file: File
): Promise<GenerateReportSuccessResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const { data } = await axios.post<GenerateReportSuccessResponse>(
    GENERATE_REPORT_URL,
    formData
  );

  return data;
}
