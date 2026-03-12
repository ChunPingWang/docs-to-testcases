'use client';

import { useState } from 'react';
import { useParams } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { prepareFinetuneData, startFinetune, getFinetuneStatus } from '@/lib/api-client';

export default function FinetunePage() {
  const params = useParams();
  const projectId = params.id as string;
  const [prepareResult, setPrepareResult] = useState<any>(null);
  const [finetuneResult, setFinetuneResult] = useState<any>(null);
  const [preparing, setPreparing] = useState(false);
  const [training, setTraining] = useState(false);

  const handlePrepare = async () => {
    setPreparing(true);
    try {
      const result = await prepareFinetuneData(projectId);
      setPrepareResult(result);
    } catch (err) {
      console.error('Prepare failed:', err);
      setPrepareResult({ error: 'Failed to prepare training data.' });
    } finally {
      setPreparing(false);
    }
  };

  const handleStartTraining = async () => {
    setTraining(true);
    try {
      const result = await startFinetune(projectId);
      setFinetuneResult(result);
    } catch (err) {
      console.error('Training failed:', err);
      setFinetuneResult({ error: 'Failed to start fine-tuning.' });
    } finally {
      setTraining(false);
    }
  };

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold mb-6">Fine-tuning</h1>

      {/* Step 1: Prepare Data */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Step 1: Prepare Training Data</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Generate Q&A and Gherkin training pairs from your uploaded documents.
          </p>
          <Button onClick={handlePrepare} disabled={preparing}>
            {preparing ? 'Preparing...' : 'Prepare Data'}
          </Button>
          {prepareResult && !prepareResult.error && (
            <div className="text-sm space-y-1">
              <p>Training pairs: <strong>{prepareResult.training_pairs}</strong></p>
              <p>Train samples: {prepareResult.train_samples}</p>
              <p>Validation samples: {prepareResult.val_samples}</p>
              <Badge className="bg-green-100 text-green-800">Ready</Badge>
            </div>
          )}
          {prepareResult?.error && (
            <p className="text-sm text-red-600">{prepareResult.error}</p>
          )}
        </CardContent>
      </Card>

      {/* Step 2: Start Training */}
      <Card>
        <CardHeader>
          <CardTitle>Step 2: Create Custom Model</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Creates an Ollama Modelfile with an optimized system prompt based on your documents.
            For full LoRA fine-tuning, additional GPU setup is required.
          </p>
          <Button
            onClick={handleStartTraining}
            disabled={training || !prepareResult || prepareResult.error}
          >
            {training ? 'Creating...' : 'Create Custom Model'}
          </Button>
          {finetuneResult && !finetuneResult.error && (
            <div className="text-sm space-y-1">
              <p>Model name: <strong>{finetuneResult.model_name}</strong></p>
              <p>Status: <Badge className="bg-green-100 text-green-800">{finetuneResult.status}</Badge></p>
              <p className="text-muted-foreground">{finetuneResult.message}</p>
            </div>
          )}
          {finetuneResult?.error && (
            <p className="text-sm text-red-600">{finetuneResult.error}</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
