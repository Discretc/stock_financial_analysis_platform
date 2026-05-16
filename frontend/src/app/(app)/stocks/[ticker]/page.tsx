import type { Metadata } from 'next';
import { StockDetailClient } from './StockDetailClient';

interface PageProps {
  params: Promise<{ ticker: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { ticker } = await params;
  return {
    title: ticker.toUpperCase(),
    description: `Financial analysis for ${ticker.toUpperCase()}`,
  };
}

export default async function StockDetailPage({ params }: PageProps) {
  const { ticker } = await params;
  return <StockDetailClient ticker={ticker.toUpperCase()} />;
}
