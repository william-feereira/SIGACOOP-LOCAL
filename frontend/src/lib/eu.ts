import { useQuery } from '@tanstack/react-query';
import { api } from './api';
import type { Eu } from './tipos';

export const useEu = () => useQuery({ queryKey: ['eu'], queryFn: () => api<Eu>('/eu/'), staleTime: 5 * 60_000 });
