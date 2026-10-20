const nextJest = require('next/jest')

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files```
  dir: './',
})

// Add any custom config to be passed to Jest
/** @type {import('jest').Config} */
const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testEnvironment: 'jest-environment-jsdom',
  // e2e/ holds Playwright specs (run via `npm run test:e2e`), not Jest ones --
  // they'd otherwise match Jest's default *.spec.ts pattern and fail to import.
  testPathIgnorePatterns: ['<rootDir>/node_modules/', '<rootDir>/.next/', '<rootDir>/e2e/'],
}

// createJestConfig is exported this way to ensure next/jest can load the Next.js config, which is async
module.exports = createJestConfig(customJestConfig)
