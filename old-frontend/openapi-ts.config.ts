export default {
  client: '@hey-api/client-axios',
  experimentalParser: true,
  input: {
    path: 'client/scripts/outputs/openapi.json',
    exclude: '/api/health'
  },
  output: {
    format: 'prettier',
    lint: 'eslint',
    path: 'client',
    clean: false
  },
  plugins: ['@tanstack/react-query']
}
