import { useUpdateCustomer } from '@/app/api/customers'
import { type UserSchemaOutput } from '@/client/types.gen'
import { useState } from 'react'
import { Button } from '@/components/design-system-components/Button'
import { TextArea } from '@/components/design-system-components/TextArea'
import { IconLoader } from '@/components/icons'

export function PlaidData({
  currentCustomer
}: {
  currentCustomer: UserSchemaOutput
}) {
  const { updateCustomer } = useUpdateCustomer()
  const initialPlaidData = currentCustomer.plaid_data
  const [isEditing, setIsEditing] = useState(false)
  const [isUpdating, setIsUpdating] = useState(false)
  const [updatedPlaidData, setUpdatedPlaidData] = useState(
    initialPlaidData ?? ''
  )

  const handleUpdatePlaidData = async () => {
    setIsUpdating(true)
    try {
      await updateCustomer({
        ...currentCustomer,
        plaid_data: updatedPlaidData
      })
      setIsEditing(false)
    } catch (error) {
      console.error('Failed to update Plaid data:', error)
    } finally {
      setIsUpdating(false)
    }
  }

  const handleCancel = () => {
    setUpdatedPlaidData(initialPlaidData ?? '')
    setIsEditing(false)
  }

  if (!initialPlaidData && !isEditing) {
    return (
      <div className="space-y-4">
        <div className="text-sm text-muted-foreground">
          No Plaid data available
        </div>
        <Button onClick={() => setIsEditing(true)} variant="secondary">
          Add Plaid Data
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <TextArea
        value={updatedPlaidData}
        onChange={e => setUpdatedPlaidData(e.target.value)}
        size="small"
        variant="monospace"
        surfaceLevel="0"
        minRows={10}
        maxRows={30}
        disabled={!isEditing || isUpdating}
        className="w-full"
      />
      <div className="flex gap-2">
        {!isEditing ? (
          <Button onClick={() => setIsEditing(true)} variant="secondary">
            Edit
          </Button>
        ) : (
          <>
            <Button
              onClick={handleUpdatePlaidData}
              disabled={isUpdating}
              variant="primary"
            >
              {isUpdating ? (
                <span className="flex items-center">
                  <IconLoader className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </span>
              ) : (
                'Save'
              )}
            </Button>
            <Button
              onClick={handleCancel}
              disabled={isUpdating}
              variant="secondary"
            >
              Cancel
            </Button>
          </>
        )}
      </div>
    </div>
  )
}
