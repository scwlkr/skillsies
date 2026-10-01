export interface Capacity {
  total_bytes: number;
  used_bytes: number;
  free_bytes: number;
  used_percent: number;
  target_percent: number;
  reclaim_needed_bytes: number;
  measured_at: string;
  source: string;
  warnings?: string[];
}
export interface Item {
  id: string;
  path: string;
  label: string;
  category: string;
  allocated_bytes: number;
  logical_bytes: number;
  action: string;
  risk: string;
  selectable: boolean;
  reason: string;
}
export interface Result {
  state: string;
  preview?: boolean;
  error?: string;
  capacity_after?: Capacity;
  results?: { id: string; path: string; status: string; message?: string }[];
}
export interface Session {
  summary: {
    capacity: Capacity;
    coverage: Record<string, any>;
    limitations: string[];
    assessment: string;
  };
  scan: {
    storage_categories?: { category: string; allocated_bytes: number }[];
    top_directories?: Item[];
    top_files?: Item[];
  };
  items: Item[];
  status: Result;
  preview: boolean;
}
export interface Plan {
  id: string;
  digest: string;
  items: Item[];
  blocked: { path?: string; reason?: string; error?: string }[];
  estimated_bytes: number;
  expires_at: number;
}
declare global {
  interface Window {
    __MACBOOK_REPORT__?: Session;
  }
}
