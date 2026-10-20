// Makes @testing-library/jest-dom's matcher types (toBeInTheDocument, etc.)
// visible to `tsc --noEmit`, which type-checks every .ts/.tsx file in the
// project but never runs jest.setup.js, so it otherwise never sees the
// import that normally brings these types in at test-run time.
/// <reference types="@testing-library/jest-dom" />
