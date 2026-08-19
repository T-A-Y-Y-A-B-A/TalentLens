import '@testing-library/jest-dom';
import { vi } from 'vitest';
(globalThis as unknown as { vi: typeof vi }).vi = vi;
