'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import dynamic from 'next/dynamic';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  getFeature,
  updateFeature,
  updateFeatureStatus,
  generateTestCode,
  getGeneratedCode,
} from '@/lib/api-client';
import type { Feature, GeneratedCode } from '@/types';

const MonacoEditor = dynamic(() => import('@monaco-editor/react'), { ssr: false });

export default function FeatureDetailPage() {
  const params = useParams();
  const featureId = params.featureId as string;
  const [feature, setFeature] = useState<Feature | null>(null);
  const [gherkin, setGherkin] = useState('');
  const [reviewNotes, setReviewNotes] = useState('');
  const [saving, setSaving] = useState(false);
  const [codeLanguage, setCodeLanguage] = useState('python');
  const [generatingCode, setGeneratingCode] = useState(false);
  const [generatedCode, setGeneratedCode] = useState<GeneratedCode[]>([]);

  useEffect(() => {
    getFeature(featureId).then((f) => {
      setFeature(f);
      setGherkin(f.gherkinContent);
    });
    getGeneratedCode(featureId).then(setGeneratedCode).catch(() => {});
  }, [featureId]);

  const handleSave = async () => {
    setSaving(true);
    await updateFeature(featureId, { gherkinContent: gherkin });
    const updated = await getFeature(featureId);
    setFeature(updated);
    setSaving(false);
  };

  const handleStatusChange = async (status: string) => {
    await updateFeatureStatus(featureId, {
      status,
      reviewNotes: reviewNotes || undefined,
    });
    const updated = await getFeature(featureId);
    setFeature(updated);
  };

  const handleGenerateCode = async () => {
    setGeneratingCode(true);
    try {
      await generateTestCode(featureId, codeLanguage);
      const code = await getGeneratedCode(featureId);
      setGeneratedCode(code);
    } finally {
      setGeneratingCode(false);
    }
  };

  if (!feature) return <div className="text-muted-foreground">Loading...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{feature.name}</h1>
          <p className="text-sm text-muted-foreground">
            {feature.scenarioCount} scenarios &middot; v{feature.version}
          </p>
        </div>
        <Badge className="text-sm">{feature.status.replace('_', ' ')}</Badge>
      </div>

      {/* Gherkin Editor */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle>Gherkin Editor</CardTitle>
            <Button onClick={handleSave} disabled={saving}>
              {saving ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="border rounded-md overflow-hidden">
            <MonacoEditor
              height="400px"
              language="plaintext"
              value={gherkin}
              onChange={(v) => setGherkin(v || '')}
              options={{
                minimap: { enabled: false },
                fontSize: 14,
                lineNumbers: 'on',
                wordWrap: 'on',
              }}
            />
          </div>
        </CardContent>
      </Card>

      {/* Review Panel */}
      <Card>
        <CardHeader>
          <CardTitle>Review</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-1">
            {feature.tags?.map((tag) => (
              <Badge key={tag} variant="secondary">{tag}</Badge>
            ))}
          </div>
          <Textarea
            placeholder="Review notes..."
            value={reviewNotes}
            onChange={(e) => setReviewNotes(e.target.value)}
            rows={3}
          />
          <div className="flex gap-2">
            {feature.status !== 'approved' && (
              <Button onClick={() => handleStatusChange('approved')}>Approve</Button>
            )}
            {feature.status !== 'rejected' && (
              <Button
                variant="destructive"
                onClick={() => handleStatusChange('rejected')}
              >
                Reject
              </Button>
            )}
            {feature.status !== 'in_review' && feature.status === 'draft' && (
              <Button
                variant="outline"
                onClick={() => handleStatusChange('in_review')}
              >
                Submit for Review
              </Button>
            )}
          </div>
          {feature.reviewNotes && (
            <div className="text-sm text-muted-foreground">
              <p className="font-medium">Previous review notes:</p>
              <p>{feature.reviewNotes}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Code Generation */}
      {feature.status === 'approved' && (
        <Card>
          <CardHeader>
            <CardTitle>Generate Test Code</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-3 items-center">
              <Select value={codeLanguage} onValueChange={(v) => v && setCodeLanguage(v)}>
                <SelectTrigger className="w-48">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="python">Python (pytest-bdd)</SelectItem>
                  <SelectItem value="javascript">JavaScript (Cucumber.js)</SelectItem>
                </SelectContent>
              </Select>
              <Button onClick={handleGenerateCode} disabled={generatingCode}>
                {generatingCode ? 'Generating...' : 'Generate Code'}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Generated Code */}
      {generatedCode.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Generated Code</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {generatedCode.map((code) => (
              <div key={code.id}>
                <p className="text-sm font-medium mb-1">
                  {code.filePath.split('/').pop()} ({code.framework})
                </p>
                <div className="border rounded-md overflow-hidden">
                  <MonacoEditor
                    height="300px"
                    language={code.language === 'python' ? 'python' : 'javascript'}
                    value={code.codeContent}
                    options={{
                      readOnly: true,
                      minimap: { enabled: false },
                      fontSize: 13,
                    }}
                  />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
