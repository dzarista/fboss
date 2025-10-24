// Basic smoke test for App component
// Full component tests are in tests/ directory

describe('App Component', () => {
  test('should be defined and exportable', () => {
    // Simple test to ensure the module loads without React rendering issues
    const App = require('./App').default;
    expect(App).toBeDefined();
    expect(typeof App).toBe('function');
  });
});
