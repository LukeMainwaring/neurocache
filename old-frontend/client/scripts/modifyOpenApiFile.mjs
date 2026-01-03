import fs from 'fs'

async function downloadOpenAPIFile(url) {
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }
  return await response.json()
}

async function modifyOpenAPIFile(url) {
  try {
    const openapiContent = await downloadOpenAPIFile(url)

    const paths = openapiContent.paths
    for (const pathKey of Object.keys(paths)) {
      const pathData = paths[pathKey]
      for (const method of Object.keys(pathData)) {
        const operation = pathData[method]

        // Remove security requirements from each operation
        delete operation.security

        operation.operationId = operation.operationId.replace(/_route$/, '')
        operation.summary = operation.summary.replace(/ Route$/, '')

        if (operation.tags && operation.tags.length > 0) {
          const tag = operation.tags[0]
          const operationId = operation.operationId
          const toRemove = `${tag}-`
          if (operationId.startsWith(toRemove)) {
            const newOperationId = operationId.substring(toRemove.length)
            operation.operationId = newOperationId
          }
        }
      }
    }

    // Remove global security schemes
    delete openapiContent.components?.securitySchemes
    delete openapiContent.security

    const outputFilePath = './client/scripts/outputs/openapi.json'
    await fs.promises.writeFile(
      outputFilePath,
      JSON.stringify(openapiContent, null, 2) + '\n'
    )
    console.info(`File successfully modified and saved to ${outputFilePath}`)
  } catch (err) {
    console.error('Error:', err)
  }
}

// Default API URL is the local development API URL
const defaultApiUrl = 'http://localhost:8000/api/openapi.json'

// Get the API URL from command-line arguments, e.g. for local dev, or use the default
const apiUrl = process.argv[2] || defaultApiUrl

modifyOpenAPIFile(apiUrl)
