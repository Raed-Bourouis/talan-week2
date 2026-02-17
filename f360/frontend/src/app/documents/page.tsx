'use client';

import { useState, useRef } from 'react';

export default function DocumentsPage() {
  const [files, setFiles] = useState<{ name: string; size: string; type: string; status: string }[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleUpload = async (fileList: FileList | null) => {
    if (!fileList || fileList.length === 0) return;
    setUploading(true);
    setUploadResult(null);

    const newFiles: typeof files = [];
    for (const file of Array.from(fileList)) {
      const formData = new FormData();
      formData.append('file', file);

      try {
        const res = await fetch('http://localhost:8000/api/v1/sources/upload', {
          method: 'POST',
          body: formData,
        });
        const data = await res.json();
        newFiles.push({
          name: file.name,
          size: formatSize(file.size),
          type: file.type || file.name.split('.').pop() || 'unknown',
          status: res.ok ? 'success' : 'error',
        });
        if (data.entities) {
          setUploadResult(`${file.name}: ${Object.values(data.entities as Record<string, unknown[]>).flat().length} entités extraites`);
        }
      } catch {
        newFiles.push({
          name: file.name,
          size: formatSize(file.size),
          type: file.type,
          status: 'error',
        });
      }
    }

    setFiles(prev => [...newFiles, ...prev]);
    setUploading(false);
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Documents</h1>
        <p className="text-gray-500 mt-1">Upload et analyse automatique de documents financiers</p>
      </div>

      {/* Upload zone */}
      <div
        className="card border-2 border-dashed border-gray-300 hover:border-blue-400 transition-colors cursor-pointer"
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => { e.preventDefault(); handleUpload(e.dataTransfer.files); }}
      >
        <div className="text-center py-8">
          <span className="text-4xl">📤</span>
          <p className="mt-4 font-semibold text-gray-700">
            {uploading ? 'Upload en cours...' : 'Glissez vos fichiers ici ou cliquez pour sélectionner'}
          </p>
          <p className="text-sm text-gray-500 mt-1">PDF, Excel, CSV, DOCX — Max 50 MB</p>
          <input
            ref={inputRef}
            type="file"
            multiple
            accept=".pdf,.xlsx,.xls,.csv,.docx"
            className="hidden"
            onChange={(e) => handleUpload(e.target.files)}
          />
        </div>
      </div>

      {uploadResult && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-sm text-green-800">
          ✅ {uploadResult}
        </div>
      )}

      {/* File list */}
      {files.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Fichiers Uploadés</h2>
          <div className="divide-y divide-gray-100">
            {files.map((f, i) => (
              <div key={i} className="flex items-center gap-4 py-3">
                <span className="text-xl">{fileIcon(f.type)}</span>
                <div className="flex-1">
                  <p className="font-medium text-sm">{f.name}</p>
                  <p className="text-xs text-gray-500">{f.size}</p>
                </div>
                <span className={f.status === 'success' ? 'badge-success' : 'badge-danger'}>
                  {f.status === 'success' ? 'Traité' : 'Erreur'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {files.length === 0 && (
        <div className="text-center py-12 text-gray-400">
          <span className="text-4xl">📁</span>
          <p className="mt-4">Aucun document uploadé pour cette session</p>
        </div>
      )}
    </div>
  );
}

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function fileIcon(type: string) {
  if (type.includes('pdf')) return '📕';
  if (type.includes('sheet') || type.includes('excel') || type.includes('xlsx')) return '📗';
  if (type.includes('csv')) return '📊';
  if (type.includes('doc')) return '📘';
  return '📄';
}
