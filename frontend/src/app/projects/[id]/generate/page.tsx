'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { getDocuments, generateTestCases } from '@/lib/api-client';
import type { Document } from '@/types';

export default function GeneratePage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDoc, setSelectedDoc] = useState('');
  const [featureDescription, setFeatureDescription] = useState('');
  const [includePositive, setIncludePositive] = useState(true);
  const [includeNegative, setIncludeNegative] = useState(true);
  const [includeApi, setIncludeApi] = useState(true);
  const [includeE2e, setIncludeE2e] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState<any>(null);

  useEffect(() => {
    getDocuments(projectId).then((docs) => {
      setDocuments(docs.filter((d: Document) => d.status === 'processed'));
    });
  }, [projectId]);

  const handleGenerate = async () => {
    setGenerating(true);
    setResult(null);
    try {
      const res = await generateTestCases(projectId, {
        documentId: selectedDoc || undefined,
        featureDescription: featureDescription || undefined,
        includePositive,
        includeNegative,
        includeApiTests: includeApi,
        includeE2eTests: includeE2e,
      });
      setResult(res);
    } catch (err) {
      console.error('Generation failed:', err);
      setResult({ error: 'Generation failed. Please try again.' });
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold mb-6">Generate Test Cases</h1>

      <Card>
        <CardHeader>
          <CardTitle>Configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-1 block">Document (optional)</label>
            <Select value={selectedDoc} onValueChange={(v) => setSelectedDoc(v || '')}>
              <SelectTrigger>
                <SelectValue placeholder="All documents" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">All documents</SelectItem>
                {documents.map((doc) => (
                  <SelectItem key={doc.id} value={doc.id}>
                    {doc.originalName}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <label className="text-sm font-medium mb-1 block">
              Feature focus (optional)
            </label>
            <Textarea
              placeholder="e.g., User authentication API, Payment workflow..."
              value={featureDescription}
              onChange={(e) => setFeatureDescription(e.target.value)}
              rows={2}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            {[
              { label: 'Positive Tests', checked: includePositive, set: setIncludePositive },
              { label: 'Negative Tests', checked: includeNegative, set: setIncludeNegative },
              { label: 'API Tests', checked: includeApi, set: setIncludeApi },
              { label: 'E2E Tests', checked: includeE2e, set: setIncludeE2e },
            ].map((opt) => (
              <label key={opt.label} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={opt.checked}
                  onChange={(e) => opt.set(e.target.checked)}
                  className="rounded"
                />
                {opt.label}
              </label>
            ))}
          </div>

          <Button
            onClick={handleGenerate}
            disabled={generating}
            className="w-full"
          >
            {generating ? 'Generating... (this may take a minute)' : 'Generate Test Cases'}
          </Button>
        </CardContent>
      </Card>

      {result && !result.error && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Results</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm mb-4">
              Generated {result.length} feature(s).
            </p>
            <Button onClick={() => router.push(`/projects/${projectId}/features`)}>
              View Test Cases
            </Button>
          </CardContent>
        </Card>
      )}

      {result?.error && (
        <Card className="mt-6 border-red-200">
          <CardContent className="py-4">
            <p className="text-red-600">{result.error}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
