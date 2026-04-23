'use client';

interface PageHeaderProps {
  title: string;
  description?: string;
}

export function PageHeader({ title, description }: PageHeaderProps) {
  return (
    <div className="space-y-2 rounded-lg border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
      <div className="space-y-1">
        <h1 className="text-3xl font-semibold tracking-tight text-zinc-950 dark:text-zinc-50">
          {title}
        </h1>
        {description ? (
          <p className="max-w-2xl text-sm text-zinc-600 dark:text-zinc-400">
            {description}
          </p>
        ) : null}
      </div>
    </div>
  );
}
