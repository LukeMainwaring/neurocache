import { useResetCustomerHistory } from '@/app/api/customers'
import { type UserSchemaOutput } from '@/client/types.gen'
import { useState } from 'react'
import { Button } from '@/components/design-system-components/Button'
import { IconLoader } from '@/components/icons'
import { useClearHistory } from '@/lib/hooks/useClearHistory'

export function ResetUserHistory({
  currentCustomer,
  onResetComplete
}: {
  currentCustomer: UserSchemaOutput
  onResetComplete?: () => void
}) {
  const { resetCustomerHistory } = useResetCustomerHistory()
  const clearHistory = useClearHistory()
  const [isResetting, setIsResetting] = useState(false)

  const handleResetUserData = async () => {
    if (!currentCustomer) return

    setIsResetting(true)
    try {
      // Reset the intake_survey in the customer record
      await resetCustomerHistory()

      // Call the completion callback (e.g., to close the modal)
      if (onResetComplete) {
        onResetComplete()
      }

      // Defer clearing history to allow modal to fully close
      setTimeout(() => {
        clearHistory()
      }, 100)
    } catch (error) {
      console.error('Failed to reset user data:', error)
    } finally {
      setIsResetting(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg mb-2 font-semibold">Reset User Data</h2>
        <p className="text-sm mb-4 text-muted-foreground">
          Clear all chat history and reset the intake survey to start fresh with
          a new user experience.
        </p>
      </div>

      <div className="rounded-lg border border-border bg-muted/30 p-6">
        <h3 className="mb-3 font-medium">What will be reset:</h3>
        <ul className="text-sm mb-6 list-inside list-disc space-y-2 text-muted-foreground">
          <li>All chat history and conversation threads</li>
          <li>Intake survey responses</li>
          <li>Plaid spending and banking data</li>
          <li>Feature metadata</li>
        </ul>

        <Button
          onClick={handleResetUserData}
          disabled={isResetting || !currentCustomer}
          variant="critical"
        >
          {isResetting ? (
            <span className="flex items-center">
              <IconLoader className="mr-2 h-4 w-4 animate-spin" />
              Resetting...
            </span>
          ) : (
            'Clear User History'
          )}
        </Button>
      </div>
    </div>
  )
}
