'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { getDocuments, uploadDocuments, deleteDocument, getDocumentStatus } from '@/lib/api-client';
import type { Document } from '@/types';

const ACCEPTED_TYPES = '.docx,.xlsx,.pdf,.txt,.md';

const statusColors: Record<string, string> = {
  uploaded: 'bg-yellow-100 text-yellow-800',
  processing: 'bg-blue-100 text-blue-800',
  processed: 'bg-green-100 text-green-800',
  error: 'bg-red-100 text-red-800',
};

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function DocumentsPage() {
  const params = useParams();
  const projectId = params.id as string;
  const [documents, setDocuments] = useState<Document[]>([]);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  const load = useCallback(() => {
    getDocuments(projectId).then(setDocuments).catch(console.error);
  }, [projectId]);

  useEffect(() => { load(); }, [load]);

  // Poll for processing status
  useEffect(() => {
    const processing = documents.filter(
      (d) => d.status === 'uploaded' || d.status === 'processing',
    );
    if (processing.length === 0) return;

    const interval = setInterval(() => {
      Promise.all(processing.map((d) => getDocumentStatus(d.id))).then(() => load());
    }, 3000);

    return () => clearInterval(interval);
  }, [documents, load]);

  const handleUpload = async (files: FileList | File[]) => {
    setUploading(true);
    try {
      await uploadDocuments(projectId, Array.from(files));
      load();
    } catch (err) {
      console.error('Upload failed:', err);
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files.length) handleUpload(e.dataTransfer.files);
  };

  const handleDelete = async (id: string) => {
    await deleteDocument(id);
    load();
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Documents</h1>

      {/* Upload Dropzone */}
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center mb-6 transition-colors ${
          dragOver ? 'border-primary bg-primary/5' : 'border-muted-foreground/25'
        }`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
      >
        <p className="text-muted-foreground mb-2">
          {uploading ? 'Uploading...' : 'Drag & drop files here, or click to browse'}
        </p>
        <p className="text-xs text-muted-foreground mb-4">
          Supported: Word (.docx), Excel (.xlsx), PDF, Text (.txt), Markdown (.md)
        </p>
        <input
          type="file"
          multiple
          accept={ACCEPTED_TYPES}
          className="hidden"
          id="file-upload"
          onChange={(e) => e.target.files && handleUpload(e.target.files)}
        />
        <Button variant="outline" onClick={() => document.getElementById('file-upload')?.click()}>
          Browse Files
        </Button>
      </div>

      {/* Document List */}
      <div className="space-y-3">
        {documents.map((doc) => (
          <Card key={doc.id}>
            <CardContent className="flex items-center justify-between py-4">
              <div className="min-w-0 flex-1">
                <p className="font-medium">{doc.originalName}</p>
                <p className="text-sm text-muted-foreground">
                  {doc.fileType.toUpperCase()} &middot; {formatSize(doc.fileSize)}
                  {doc.chunkCount > 0 && ` \u00b7 ${doc.chunkCount} chunks`}
                </p>
                {doc.status === 'error' && doc.errorMessage && (
                  <p className="text-sm text-red-600 mt-1">{doc.errorMessage}</p>
                )}
              </div>
              <div className="flex items-center gap-3">
                <Badge className={statusColors[doc.status] || ''}>
                  {doc.status}
                </Badge>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleDelete(doc.id)}
                >
                  Delete
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
        {documents.length === 0 && (
          <p className="text-muted-foreground text-center py-8">
            No documents uploaded yet.
          </p>
        )}
      </div>
    </div>
  );
}
