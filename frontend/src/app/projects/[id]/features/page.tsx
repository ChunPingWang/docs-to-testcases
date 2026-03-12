'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { getFeatures, updateFeatureStatus, deleteFeature } from '@/lib/api-client';
import type { Feature } from '@/types';

const statusColors: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-800',
  in_review: 'bg-yellow-100 text-yellow-800',
  approved: 'bg-green-100 text-green-800',
  rejected: 'bg-red-100 text-red-800',
  code_generated: 'bg-blue-100 text-blue-800',
};

const tagColors: Record<string, string> = {
  '@positive': 'bg-green-100 text-green-700',
  '@negative': 'bg-red-100 text-red-700',
  '@api': 'bg-purple-100 text-purple-700',
  '@e2e': 'bg-blue-100 text-blue-700',
  '@smoke': 'bg-orange-100 text-orange-700',
};

export default function FeaturesPage() {
  const params = useParams();
  const projectId = params.id as string;
  const [features, setFeatures] = useState<Feature[]>([]);

  const load = useCallback(() => {
    getFeatures(projectId).then(setFeatures).catch(console.error);
  }, [projectId]);

  useEffect(() => { load(); }, [load]);

  const handleStatusChange = async (id: string, status: string) => {
    await updateFeatureStatus(id, { status });
    load();
  };

  const handleDelete = async (id: string) => {
    await deleteFeature(id);
    load();
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Test Cases (Features)</h1>
        <Link href={`/projects/${projectId}/generate`}>
          <Button>Generate New</Button>
        </Link>
      </div>

      <div className="space-y-4">
        {features.map((feature) => (
          <Card key={feature.id}>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">{feature.name}</CardTitle>
                <Badge className={statusColors[feature.status] || ''}>
                  {feature.status.replace('_', ' ')}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-1 mb-3">
                {feature.tags?.map((tag) => (
                  <Badge key={tag} variant="secondary" className={tagColors[tag] || ''}>
                    {tag}
                  </Badge>
                ))}
              </div>
              <p className="text-sm text-muted-foreground mb-3">
                {feature.scenarioCount} scenario(s) &middot; v{feature.version}
              </p>
              <div className="flex gap-2">
                <Link href={`/projects/${projectId}/features/${feature.id}`}>
                  <Button variant="outline" size="sm">
                    View / Edit
                  </Button>
                </Link>
                {feature.status === 'draft' && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleStatusChange(feature.id, 'in_review')}
                  >
                    Submit for Review
                  </Button>
                )}
                {feature.status === 'in_review' && (
                  <>
                    <Button
                      size="sm"
                      onClick={() => handleStatusChange(feature.id, 'approved')}
                    >
                      Approve
                    </Button>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => handleStatusChange(feature.id, 'rejected')}
                    >
                      Reject
                    </Button>
                  </>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleDelete(feature.id)}
                >
                  Delete
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
        {features.length === 0 && (
          <p className="text-muted-foreground text-center py-12">
            No test cases generated yet.{' '}
            <Link href={`/projects/${projectId}/generate`} className="underline">
              Generate some
            </Link>
          </p>
        )}
      </div>
    </div>
  );
}
