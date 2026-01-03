'use server'

const KEYS_REQUIRED: readonly string[] = []

export async function getMissingKeys() {
  return KEYS_REQUIRED.map(key => (process.env[key] ? '' : key)).filter(
    key => key !== ''
  )
}
