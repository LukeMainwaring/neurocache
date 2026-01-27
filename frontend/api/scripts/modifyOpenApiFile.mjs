import fs from "fs";

const DEFAULT_API_URL = "http://localhost:8000/api/openapi.json";
const OUTPUT_PATH = "./api/scripts/outputs/openapi.json";

async function fetchOpenApiSpec(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch OpenAPI spec: ${response.status}`);
  }
  return response.json();
}

function stripSecuritySchemes(spec) {
  // Remove security from each operation
  for (const path of Object.values(spec.paths)) {
    for (const operation of Object.values(path)) {
      delete operation.security;
    }
  }

  // Remove global security schemes
  delete spec.components?.securitySchemes;
  delete spec.security;

  return spec;
}

async function main() {
  const apiUrl = process.argv[2] || DEFAULT_API_URL;

  try {
    const spec = await fetchOpenApiSpec(apiUrl);
    const modifiedSpec = stripSecuritySchemes(spec);

    await fs.promises.writeFile(
      OUTPUT_PATH,
      JSON.stringify(modifiedSpec, null, 2) + "\n"
    );
    console.info(`OpenAPI spec saved to ${OUTPUT_PATH}`);
  } catch (err) {
    console.error("Error:", err.message);
    process.exit(1);
  }
}

main();
