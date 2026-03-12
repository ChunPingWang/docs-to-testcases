'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { getProject } from '@/lib/api-client';
import type { Project } from '@/types';

export default function ProjectDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [project, setProject] = useState<Project | null>(null);

  useEffect(() => {
    getProject(id).then(setProject).catch(console.error);
  }, [id]);

  if (!project) return <div className="text-muted-foreground">Loading...</div>;

  const tabs = [
    { key: 'documents', label: 'Documents', href: `/projects/${id}/documents` },
    { key: 'qa', label: 'Q&A', href: `/projects/${id}/qa` },
    { key: 'features', label: 'Test Cases', href: `/projects/${id}/features` },
    { key: 'generate', label: 'Generate', href: `/projects/${id}/generate` },
    { key: 'finetune', label: 'Fine-tune', href: `/projects/${id}/finetune` },
  ];

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold">{project.name}</h1>
        {project.description && (
          <p className="text-muted-foreground mt-1">{project.description}</p>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Documents</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{project.documents?.length || 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Test Cases</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{project.features?.length || 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Status</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-green-600">Active</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {tabs.map((tab) => (
          <Link key={tab.key} href={tab.href}>
            <Button variant="outline" className="w-full">
              {tab.label}
            </Button>
          </Link>
        ))}
      </div>
    </div>
  );
}
