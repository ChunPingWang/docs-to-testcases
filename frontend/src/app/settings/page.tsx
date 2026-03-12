'use client';

import { useEffect, useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  getSettings,
  updateSettings,
  resetSettings,
  getHealthStatus,
  getAvailableModels,
} from '@/lib/api-client';
import type { ModelSettings, HealthStatus } from '@/types';

const DEFAULT_SETTINGS: ModelSettings = {
  llm_model: '',
  embedding_model: '',
  temperature_qa: 0.7,
  temperature_test_case: 0.3,
  temperature_test_code: 0.2,
  temperature_finetune: 0.5,
  max_tokens_qa: 4096,
  max_tokens_test_case: 8192,
  max_tokens_test_code: 8192,
  max_tokens_finetune: 2048,
  chunk_size: 1000,
  chunk_overlap: 200,
  retrieval_top_k: 10,
  min_relevance_score: 0.3,
  use_reranker: false,
  reranker_initial_k: 30,
  chunking_strategy: 'fixed',
  semantic_chunk_threshold: 0.5,
};

export default function SettingsPage() {
  const [settings, setSettings] = useState<ModelSettings>(DEFAULT_SETTINGS);
  const [original, setOriginal] = useState<ModelSettings>(DEFAULT_SETTINGS);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [models, setModels] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const loadData = useCallback(async () => {
    try {
      const [s, h, m] = await Promise.all([
        getSettings(),
        getHealthStatus().catch(() => null),
        getAvailableModels().catch(() => ({ models: [] })),
      ]);
      setSettings(s);
      setOriginal(s);
      setHealth(h);
      const modelList = m?.models
        ? m.models.map((item: { name: string }) => item.name)
        : Array.isArray(m) ? m : [];
      setModels(modelList);
    } catch {
      setMessage({ type: 'error', text: 'Failed to load settings' });
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const hasChanges = JSON.stringify(settings) !== JSON.stringify(original);

  const handleSave = async () => {
    setSaving(true);
    setMessage(null);
    try {
      const diff: Record<string, unknown> = {};
      for (const key of Object.keys(settings) as (keyof ModelSettings)[]) {
        if (settings[key] !== original[key]) {
          diff[key] = settings[key];
        }
      }
      const updated = await updateSettings(diff);
      setSettings(updated);
      setOriginal(updated);
      setMessage({ type: 'success', text: 'Settings saved successfully' });
    } catch {
      setMessage({ type: 'error', text: 'Failed to save settings' });
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    setSaving(true);
    setMessage(null);
    try {
      const updated = await resetSettings();
      setSettings(updated);
      setOriginal(updated);
      setMessage({ type: 'success', text: 'Settings reset to defaults' });
    } catch {
      setMessage({ type: 'error', text: 'Failed to reset settings' });
    } finally {
      setSaving(false);
    }
  };

  const update = (key: keyof ModelSettings, value: string | number | boolean) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
  };

  const updateNumber = (key: keyof ModelSettings, raw: string, isFloat = false) => {
    const value = isFloat ? parseFloat(raw) : parseInt(raw, 10);
    if (!isNaN(value)) update(key, value);
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Settings</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Configure model parameters and RAG settings
          </p>
        </div>
        <div className="flex items-center gap-2">
          {health && (
            <Badge variant={health.llm_api_connected ? 'default' : 'destructive'}>
              LLM API: {health.llm_api_connected ? 'Connected' : 'Disconnected'}
            </Badge>
          )}
          {health && (
            <Badge variant={health.chroma_connected ? 'default' : 'destructive'}>
              ChromaDB: {health.chroma_connected ? 'Connected' : 'Disconnected'}
            </Badge>
          )}
        </div>
      </div>

      {message && (
        <div
          className={`mb-4 p-3 rounded-md text-sm ${
            message.type === 'success'
              ? 'bg-green-500/10 text-green-700 dark:text-green-400'
              : 'bg-destructive/10 text-destructive'
          }`}
        >
          {message.text}
        </div>
      )}

      <Tabs defaultValue="models">
        <TabsList>
          <TabsTrigger value="models">Model Selection</TabsTrigger>
          <TabsTrigger value="generation">Generation Parameters</TabsTrigger>
          <TabsTrigger value="rag">RAG Parameters</TabsTrigger>
        </TabsList>

        {/* ── Tab 1: Model Selection ── */}
        <TabsContent value="models">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">LLM Model</CardTitle>
              </CardHeader>
              <CardContent>
                {models.length > 0 ? (
                  <Select
                    value={settings.llm_model}
                    onValueChange={(v) => v && update('llm_model', v)}
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Select model" />
                    </SelectTrigger>
                    <SelectContent>
                      {models.map((m) => (
                        <SelectItem key={m} value={m}>
                          {m}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                ) : (
                  <Input
                    value={settings.llm_model}
                    onChange={(e) => update('llm_model', e.target.value)}
                    placeholder="e.g. MiniMax-M2.5"
                  />
                )}
                <p className="text-xs text-muted-foreground mt-2">
                  Used for text generation, QA, and test case creation
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">Embedding Model</CardTitle>
              </CardHeader>
              <CardContent>
                {models.length > 0 ? (
                  <Select
                    value={settings.embedding_model}
                    onValueChange={(v) => v && update('embedding_model', v)}
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Select model" />
                    </SelectTrigger>
                    <SelectContent>
                      {models.map((m) => (
                        <SelectItem key={m} value={m}>
                          {m}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                ) : (
                  <Input
                    value={settings.embedding_model}
                    onChange={(e) => update('embedding_model', e.target.value)}
                    placeholder="e.g. embo-01"
                  />
                )}
                <p className="text-xs text-muted-foreground mt-2">
                  Used for document embedding and similarity search
                </p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* ── Tab 2: Generation Parameters ── */}
        <TabsContent value="generation">
          <div className="space-y-4 mt-4">
            {[
              { label: 'QA / Chat', tempKey: 'temperature_qa' as const, tokKey: 'max_tokens_qa' as const },
              { label: 'Test Case Generation', tempKey: 'temperature_test_case' as const, tokKey: 'max_tokens_test_case' as const },
              { label: 'Test Code Generation', tempKey: 'temperature_test_code' as const, tokKey: 'max_tokens_test_code' as const },
              { label: 'Fine-tune', tempKey: 'temperature_finetune' as const, tokKey: 'max_tokens_finetune' as const },
            ].map(({ label, tempKey, tokKey }) => (
              <Card key={tempKey}>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm">{label}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="text-xs text-muted-foreground mb-1 block">
                        Temperature ({settings[tempKey]})
                      </label>
                      <Input
                        type="range"
                        min="0"
                        max="2"
                        step="0.1"
                        value={settings[tempKey]}
                        onChange={(e) => updateNumber(tempKey, e.target.value, true)}
                        className="w-full"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-muted-foreground mb-1 block">
                        Max Tokens
                      </label>
                      <Input
                        type="number"
                        min="256"
                        max="32768"
                        step="256"
                        value={settings[tokKey]}
                        onChange={(e) => updateNumber(tokKey, e.target.value)}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* ── Tab 3: RAG Parameters ── */}
        <TabsContent value="rag">
          <div className="space-y-4 mt-4">
            {/* Row 1: Basic chunking settings */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm">Chunk Size</CardTitle>
                </CardHeader>
                <CardContent>
                  <Input
                    type="number"
                    min="100"
                    max="10000"
                    step="100"
                    value={settings.chunk_size}
                    onChange={(e) => updateNumber('chunk_size', e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground mt-2">
                    Maximum characters per document chunk
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm">Chunk Overlap</CardTitle>
                </CardHeader>
                <CardContent>
                  <Input
                    type="number"
                    min="0"
                    max="2000"
                    step="50"
                    value={settings.chunk_overlap}
                    onChange={(e) => updateNumber('chunk_overlap', e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground mt-2">
                    Overlap between consecutive chunks
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm">Retrieval Top K</CardTitle>
                </CardHeader>
                <CardContent>
                  <Input
                    type="number"
                    min="1"
                    max="50"
                    step="1"
                    value={settings.retrieval_top_k}
                    onChange={(e) => updateNumber('retrieval_top_k', e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground mt-2">
                    Number of chunks retrieved for context
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Row 2: Relevance filtering */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">Min Relevance Score</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-4">
                  <Input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={settings.min_relevance_score}
                    onChange={(e) => updateNumber('min_relevance_score', e.target.value, true)}
                    className="flex-1"
                  />
                  <span className="text-sm font-mono w-12 text-right">
                    {settings.min_relevance_score.toFixed(2)}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mt-2">
                  Chunks with relevance score below this threshold will be filtered out (0 = no filtering)
                </p>
              </CardContent>
            </Card>

            {/* Row 3: Reranker settings */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">LLM Reranker</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label htmlFor="use-reranker">Enable Reranker</Label>
                      <p className="text-xs text-muted-foreground">
                        Use LLM to re-score and rerank retrieved chunks for better relevance
                      </p>
                    </div>
                    <Switch
                      id="use-reranker"
                      checked={settings.use_reranker}
                      onCheckedChange={(checked) => update('use_reranker', checked)}
                    />
                  </div>
                  {settings.use_reranker && (
                    <div>
                      <Label className="text-xs text-muted-foreground mb-1 block">
                        Initial K (candidates for reranking)
                      </Label>
                      <Input
                        type="number"
                        min="10"
                        max="100"
                        step="5"
                        value={settings.reranker_initial_k}
                        onChange={(e) => updateNumber('reranker_initial_k', e.target.value)}
                      />
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Row 4: Chunking strategy */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm">Chunking Strategy</CardTitle>
                </CardHeader>
                <CardContent>
                  <Select
                    value={settings.chunking_strategy}
                    onValueChange={(v) => update('chunking_strategy', v)}
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Select strategy" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="fixed">Fixed Size (default)</SelectItem>
                      <SelectItem value="table_aware">Table Aware</SelectItem>
                      <SelectItem value="semantic">Semantic</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-muted-foreground mt-2">
                    How documents are split into chunks during processing
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm">Semantic Chunk Threshold</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-4">
                    <Input
                      type="range"
                      min="0"
                      max="1"
                      step="0.05"
                      value={settings.semantic_chunk_threshold}
                      onChange={(e) => updateNumber('semantic_chunk_threshold', e.target.value, true)}
                      className="flex-1"
                      disabled={settings.chunking_strategy !== 'semantic'}
                    />
                    <span className="text-sm font-mono w-12 text-right">
                      {settings.semantic_chunk_threshold.toFixed(2)}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    Similarity threshold for semantic chunking (only applies when strategy is &quot;semantic&quot;)
                  </p>
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>
      </Tabs>

      {/* ── Action buttons ── */}
      <div className="flex items-center justify-end gap-2 mt-6">
        <Button variant="outline" onClick={handleReset} disabled={saving}>
          Reset to Defaults
        </Button>
        <Button onClick={handleSave} disabled={!hasChanges || saving}>
          {saving ? 'Saving...' : 'Save Changes'}
        </Button>
      </div>
    </div>
  );
}
