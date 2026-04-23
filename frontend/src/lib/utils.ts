import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function formatDateTime(date: string | Date): string {
  return new Date(date).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatRelativeTime(date: string | Date): string {
  const now = new Date();
  const then = new Date(date);
  const diffMs = now.getTime() - then.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);

  if (diffSec < 60) {return 'just now';}
  if (diffMin < 60) {return `${diffMin}m ago`;}
  if (diffHour < 24) {return `${diffHour}h ago`;}
  if (diffDay < 7) {return `${diffDay}d ago`;}
  return formatDate(date);
}

export function formatNumber(value: number, decimals = 2): string {
  if (value >= 1000000) {
    return `${(value / 1000000).toFixed(1)}M`;
  }
  if (value >= 1000) {
    return `${(value / 1000).toFixed(1)}K`;
  }
  return value.toFixed(decimals);
}

export function formatCurrency(value: number, currency = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatPercentage(value: number, decimals = 1): string {
  return `${value.toFixed(decimals)}%`;
}

export function formatDuration(seconds: number): string {
  if (seconds < 60) {return `${seconds.toFixed(0)}s`;}
  if (seconds < 3600) {return `${(seconds / 60).toFixed(0)}m`;}
  if (seconds < 86400) {return `${(seconds / 3600).toFixed(1)}h`;}
  return `${(seconds / 86400).toFixed(1)}d`;
}

export function getStatusColor(status: string): string {
  const statusColors: Record<string, string> = {
    healthy: 'text-green-500',
    degraded: 'text-yellow-500',
    unhealthy: 'text-red-500',
    deployed: 'text-green-500',
    ready: 'text-blue-500',
    training: 'text-yellow-500',
    deploying: 'text-blue-500',
    failed: 'text-red-500',
    deprecated: 'text-gray-500',
    running: 'text-blue-500',
    idle: 'text-gray-500',
    paused: 'text-yellow-500',
    completed: 'text-green-500',
    pending: 'text-yellow-500',
    approved: 'text-green-500',
    rejected: 'text-red-500',
    executed: 'text-green-500',
    queued: 'text-blue-500',
    cancelled: 'text-gray-500',
    busy: 'text-blue-500',
    offline: 'text-gray-500',
    active: 'text-green-500',
    inactive: 'text-gray-500',
  };
  return statusColors[status.toLowerCase()] || 'text-gray-500';
}

export function getStatusBgColor(status: string): string {
  const statusColors: Record<string, string> = {
    healthy: 'bg-green-500/10',
    degraded: 'bg-yellow-500/10',
    unhealthy: 'bg-red-500/10',
    deployed: 'bg-green-500/10',
    ready: 'bg-blue-500/10',
    training: 'bg-yellow-500/10',
    deploying: 'bg-blue-500/10',
    failed: 'bg-red-500/10',
    deprecated: 'bg-gray-500/10',
    running: 'bg-blue-500/10',
    idle: 'bg-gray-500/10',
    paused: 'bg-yellow-500/10',
    completed: 'bg-green-500/10',
    pending: 'bg-yellow-500/10',
    approved: 'bg-green-500/10',
    rejected: 'bg-red-500/10',
    executed: 'bg-green-500/10',
    queued: 'bg-blue-500/10',
    cancelled: 'bg-gray-500/10',
    busy: 'bg-blue-500/10',
    offline: 'bg-gray-500/10',
    active: 'bg-green-500/10',
    inactive: 'bg-gray-500/10',
  };
  return statusColors[status.toLowerCase()] || 'bg-gray-500/10';
}

export function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

export function truncate(str: string, maxLength: number): string {
  if (str.length <= maxLength) {return str;}
  return `${str.slice(0, maxLength)}...`;
}