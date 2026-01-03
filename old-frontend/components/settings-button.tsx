'use client'

import { useState } from 'react'
import { cn } from '@/lib/utils/tailwindUtils'
import { Tooltip } from './design-system-components/Tooltip'
import { IconSettings } from './icons'
import { SettingsModal } from './settings-modal'

export function SettingsButton({ className }: { className?: string }) {
  const [open, setOpen] = useState(false)

  return (
    <>
      <Tooltip content="Settings">
        <button
          onClick={() => setOpen(true)}
          className={cn(
            'flex size-[32px] shrink-0 items-center justify-center rounded-[8px] bg-neutral-800 text-text-high-contrast hover:bg-neutral-900',
            className
          )}
        >
          <IconSettings />
          <span className="sr-only">Settings</span>
        </button>
      </Tooltip>
      <SettingsModal open={open} onOpenChange={setOpen} />
    </>
  )
}
