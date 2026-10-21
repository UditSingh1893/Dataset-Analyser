"use client";

import { useState } from "react";
import axios from "axios";
import Image from "next/image";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL! || "http://localhost:8000";

export default function Home() {
  const [files, setFiles] = useState<string[]>([]);
  const [target, setTarget] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleUpload = async (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);
    if (target) {
      formData.append("target", target);
    }

    try {
      setError("");
      setLoading(true);

      const res = await axios.post(`${BACKEND_URL}/process`, formData);

      setFiles(res.data.files);
    } catch (err: unknown) {
      console.error(err);
      const detail =
        axios.isAxiosError(err) && err.response?.data?.detail
          ? err.response.data.detail
          : null;
      setError(detail || "Failed to process CSV. Check backend.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100">
      <div className="max-w-5xl mx-auto px-6 py-12">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-slate-900 mb-3">CSV Bias & SMOTE Analyzer</h1>
          <p className="text-slate-600">Upload your CSV file to analyze bias and apply SMOTE techniques</p>
        </div>

        <div className="bg-white rounded-2xl shadow-lg border border-slate-200 p-8 mb-8">
          <label className="block cursor-pointer">
            <div className="border-2 border-dashed border-slate-300 rounded-xl p-12 text-center hover:border-blue-500 hover:bg-blue-50/50 transition-all">
              <svg
                className="w-12 h-12 mx-auto mb-4 text-slate-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
              <p className="text-lg font-medium text-slate-700 mb-1">Click to upload CSV file</p>
              <p className="text-sm text-slate-500">or drag and drop</p>
            </div>
            <input type="file" accept=".csv" onChange={handleUpload} className="hidden" />
          </label>

          <div className="mt-6 pt-6 border-t border-slate-200">
            <label
              htmlFor="target"
              className="block text-sm font-medium text-slate-700 mb-2"
            >
              Target column (optional)
            </label>
            <input
              id="target"
              type="text"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              placeholder="e.g. label - leave blank to auto-detect"
              className="w-full px-4 py-2.5 border border-slate-300 rounded-lg text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p className="mt-2 text-sm text-slate-500">
              The class label you want to balance. If left blank, the backend
              detects it from the column names.
            </p>
          </div>
        </div>

        {loading && (
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-6 text-center">
            <div className="flex items-center justify-center gap-3">
              <div className="w-5 h-5 border-3 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
              <p className="text-blue-900 font-medium">Processing dataset...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-6">
            <p className="text-red-800 font-medium">{error}</p>
          </div>
        )}

        {files.length > 0 && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-slate-900">Generated Analysis Files</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {files.map((url, i) => {
                const fullUrl = `${BACKEND_URL}${url}`
                const fileName = url.split("/").pop() || `file-${i}`
                const isImage = /\.(png|jpg|jpeg|gif|svg)$/i.test(fileName)

                return (
                  <div
                    key={i}
                    className="bg-white rounded-xl shadow-md border border-slate-200 overflow-hidden hover:shadow-xl transition-shadow"
                  >
                    {/* Preview */}
                    {isImage ? (
                      <div className="aspect-video bg-slate-100 relative">
                        <Image
                          src={fullUrl}
                          alt={fileName}
                          fill
                          className="object-contain"
                          sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                          unoptimized
                        />
                      </div>
                    ) : (
                      <div className="aspect-video bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center">
                        <svg className="w-16 h-16 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                          />
                        </svg>
                      </div>
                    )}

                    {/* File Info & Download */}
                    <div className="p-4">
                      <p className="text-sm font-medium text-slate-900 mb-3 truncate" title={fileName}>
                        {fileName}
                      </p>
                      <a
                        href={fullUrl}
                        download
                        target="_blank"
                        className="flex items-center justify-center gap-2 w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2.5 px-4 rounded-lg transition-colors"
                        rel="noreferrer"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                          />
                        </svg>
                        Download
                      </a>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
