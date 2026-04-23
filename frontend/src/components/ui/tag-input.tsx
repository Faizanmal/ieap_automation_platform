'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';

export interface Tag {
  id: string;
  name: string;
  color?: string;
}

interface TagInputProps {
  selectedTags: Tag[];
  onChange: (tags: Tag[]) => void;
  className?: string;
}

export function TagInput({ className }: TagInputProps) {
  // Placeholder implementation to satisfy compilation
  return (
    <div className={cn('space-y-2', className)}>
      <div className="flex flex-wrap gap-2">
        <span className="text-sm text-muted-foreground">Tag input disabled</span>
      </div>
    </div>
  );
}
