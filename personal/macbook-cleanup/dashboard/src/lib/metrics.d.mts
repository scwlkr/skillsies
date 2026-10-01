import type {Capacity, Item} from '../types';
export function size(bytes: number): string;
export function projection(capacity: Capacity, items: Item[], selected: Set<string>): {bytes: number; percent: number; gap: number};
export function shortPath(path: string): string;
export function displayName(item: Item): string;
