import { usePingNotification } from '@/app/api/ping'
import { type UserSchemaOutput } from '@/client/types.gen'
import { useState } from 'react'
import { Button } from '@/components/design-system-components/Button'
import { Checkbox } from '@/components/design-system-components/Checkbox'
import { IconLoader } from '@/components/icons'
import { useRagAppStore } from '@/providers/rag-app-store-provider'
import { useMessagesStore } from '@/providers/messages-store-provider'
import { toast } from 'sonner'
import { AGILITY_DEFAULT_ASSISTANT_SLUG } from '@/lib/consts'
import { useRouter } from 'next/navigation'
import { nanoid } from '@/lib/utils'

export function NotificationsTrigger({
  currentCustomer,
  onClose
}: {
  currentCustomer: UserSchemaOutput
  onClose?: () => void
}) {
  const { pingNotification } = usePingNotification()
  const [isGenerating, setIsGenerating] = useState(false)
  const [enableEvaluation, setEnableEvaluation] = useState(false)
  const addHistoryThread = useRagAppStore(state => state.addHistoryThread)
  const setCurrentThread = useMessagesStore(state => state.setCurrentThread)
  const router = useRouter()

  const handleGenerateNotification = async () => {
    if (!currentCustomer) return

    setIsGenerating(true)
    try {
      const response = await pingNotification({
        query: { evaluate: enableEvaluation }
      })

      // Add to chat history and set current thread
      if (response) {
        const threadId = response.thread_id
        const shouldSend = response.metadata?.should_send

        if (shouldSend === false) {
          toast.warning('Notification needs improvement')
        } else if (shouldSend === true) {
          toast.success('Notification approved!')
        } else {
          toast.success('Notification generated')
        }

        const assistantMessage = {
          localId: nanoid(),
          id: threadId,
          role: 'assistant' as const,
          content: response.content,
          metadata: {
            ...response.metadata,
            isProactiveNotification: true
          },
          isPending: false,
          isContentPending: false
        }

        // Add to sidebar history (following useStreamMessage pattern at line 591)
        addHistoryThread({
          title: 'Proactive Notification',
          assistantId: AGILITY_DEFAULT_ASSISTANT_SLUG,
          thread: { id: threadId },
          messages: [assistantMessage],
          snapshot: {
            user: {
              content: '[Proactive notification generated]',
              metadata: {}
            },
            assistant: {
              content: response.content,
              metadata: {
                ...response.metadata,
                isProactiveNotification: true
              }
            }
          }
        })

        // Set as current thread for chat display
        setCurrentThread({
          threadId,
          messages: [assistantMessage]
        })

        // Close the modal before navigating
        onClose?.()

        // Navigate to the new thread
        router.push(`/${threadId}`)
      }
    } catch (error) {
      console.error('Failed to generate notification:', error)
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg mb-2 font-semibold">Generate Notification</h2>
        <p className="text-sm mb-4 text-muted-foreground">
          Generate a proactive, personalized notification to the user.
        </p>
      </div>

      <div className="rounded-lg border border-border bg-muted/30 p-6">
        <h3 className="mb-3 font-medium">
          What will be in the proactive outreach:
        </h3>
        <ul className="text-sm mb-6 list-inside list-disc space-y-2 text-muted-foreground">
          <li>System-initiated check-ins</li>
          <li>Budget alerts and reminders</li>
          <li>Progress celebrations</li>
        </ul>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            marginTop: '20px',
            marginBottom: '20px'
          }}
        >
          <Checkbox
            id="enable-evaluation"
            checked={enableEvaluation}
            onCheckedChange={checked => setEnableEvaluation(checked === true)}
          />
          <label htmlFor="enable-evaluation" className="text-sm cursor-pointer">
            Enable evaluation
          </label>
        </div>

        <Button
          onClick={handleGenerateNotification}
          disabled={isGenerating || !currentCustomer}
          variant="primary"
        >
          {isGenerating ? (
            <span className="flex items-center">
              <IconLoader className="mr-2 h-4 w-4 animate-spin" />
              Generating...
            </span>
          ) : (
            'Generate Notification'
          )}
        </Button>
      </div>
    </div>
  )
}
