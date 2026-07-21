import createClient from 'openapi-fetch';
import type { paths } from './schema';

const apiClient = createClient<paths>({
  baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080',
});

export default apiClient;
