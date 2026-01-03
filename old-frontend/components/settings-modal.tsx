'use client'

import { useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogClose,
  DialogTitle,
  DialogDescription
} from '@/components/ui/dialog'
import { useMyself } from '@/app/api/customers'
import { SurveyResponsesView } from '@/components/customer/survey-responses-view'
import { PlaidData } from '@/components/customer/plaid-data'
import { NotificationsTrigger } from '@/components/customer/notifications-trigger'
import { ResetUserHistory } from '@/components/customer/reset-user-history'
import { IconLoader, IconX } from '@/components/icons'
import { cn } from '@/lib/utils/tailwindUtils'

type SettingsModalProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
}

const tabs = [
  { id: 'survey', label: 'Survey' },
  { id: 'about', label: 'About' },
  { id: 'plaid', label: 'Plaid Data' },
  { id: 'notifications', label: 'Notifications' },
  { id: 'reset', label: 'Reset' }
]

export function SettingsModal({ open, onOpenChange }: SettingsModalProps) {
  const { data: currentCustomer, isLoading, error } = useMyself()
  const [activeTab, setActiveTab] = useState('survey')

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex h-[85vh] w-full max-w-5xl flex-col overflow-hidden p-0">
        {/* Header */}
        <div className="flex shrink-0 items-center justify-between border-b px-6 py-4">
          <div>
            <DialogTitle className="text-xl font-semibold">
              Jamey's Profile
            </DialogTitle>
            <DialogDescription className="sr-only">
              View and manage customer profile information including credit
              report, banking data, and survey responses
            </DialogDescription>
          </div>
          <DialogClose className="rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2">
            <IconX className="h-5 w-5" />
            <span className="sr-only">Close</span>
          </DialogClose>
        </div>

        {/* Content Area */}
        <div className="flex flex-1 overflow-hidden">
          {isLoading && (
            <div className="flex w-full items-center justify-center py-12">
              <div className="flex items-center gap-2">
                <IconLoader className="h-5 w-5 animate-spin" />
                <p className="text-muted-foreground">
                  Loading customer data...
                </p>
              </div>
            </div>
          )}

          {error && (
            <div className="flex w-full items-center justify-center py-12">
              <div className="space-y-4 text-center">
                <p className="text-red-600">Error loading customer data</p>
                <p className="text-sm text-muted-foreground">
                  {error.message || 'An unexpected error occurred'}
                </p>
              </div>
            </div>
          )}

          {!isLoading && !error && currentCustomer && (
            <>
              {/* Left Navigation */}
              <div className="w-64 shrink-0 overflow-y-auto border-r bg-muted/30">
                <nav className="space-y-1 p-4">
                  {tabs.map(tab => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={cn(
                        'rounded-md text-sm w-full px-3 py-2 text-left font-medium transition-colors',
                        activeTab === tab.id
                          ? 'shadow-sm bg-background text-foreground'
                          : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                      )}
                    >
                      {tab.label}
                    </button>
                  ))}
                </nav>
              </div>

              {/* Right Content */}
              <div className="flex-1 overflow-y-auto">
                <div className="p-8">
                  {activeTab === 'survey' && (
                    <>
                      {currentCustomer.intake_survey ? (
                        <SurveyResponsesView
                          intakeSurvey={currentCustomer.intake_survey}
                        />
                      ) : (
                        <p className="text-muted-foreground">
                          No survey data available
                        </p>
                      )}
                    </>
                  )}
                  {activeTab === 'about' && (
                    <div className="space-y-8">
                      <div className="space-y-6">
                        <div>
                          <h4 className="text-base mb-1 font-semibold">
                            Customer Profile for Jamey
                          </h4>
                          <p className="text-sm text-muted-foreground">
                            Jamey is an active investor with many active
                            investment portfolios. He has a regular employment
                            income and a strong savings history. Jamey likes to
                            celebrate his wins and often treats himself to
                            dining out and entertainment.
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                  {activeTab === 'plaid' && (
                    <PlaidData currentCustomer={currentCustomer} />
                  )}

                  {activeTab === 'notifications' && (
                    <NotificationsTrigger
                      currentCustomer={currentCustomer}
                      onClose={() => onOpenChange(false)}
                    />
                  )}

                  {activeTab === 'reset' && (
                    <ResetUserHistory
                      currentCustomer={currentCustomer}
                      onResetComplete={() => onOpenChange(false)}
                    />
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
