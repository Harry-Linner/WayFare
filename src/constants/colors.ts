import type { Annotation } from '../types/sharedtypes';

export const PRIORITY_COLORS: Record<Annotation['priority'], string> = {
  critical: 'bg-priority-critical',  // #E9A254 [cite: 27]
  important: 'bg-priority-important', // #EEBF79 [cite: 24]
  normal: 'bg-brand-blue',           // #A3D1CC [cite: 4]
  low: 'bg-gray-300',
};