import { getChatPath } from '@/lib/consts'
import Link from 'next/link'
import { LogoLockup } from './logo-lockup'
import { LogoutButton } from './logout-button'
import { NewChatButton } from './new-chat-button'
import { SettingsButton } from './settings-button'
import { ThemeToggle } from './theme-toggle'

export async function Header() {
  return (
    <header className="flex w-full shrink-0 items-center justify-between overflow-hidden bg-surface-0 px-8 py-5 backdrop-blur-xl">
      <div className="flex" />
      <div className="flex md:hidden">
        <h1 className="type-body-300 flex items-center justify-center gap-4 text-text-strong">
          <LogoLockup className="h-[26px] w-auto" />
        </h1>
      </div>
      <div className="flex items-center gap-4">
        <ThemeToggle />
        <SettingsButton />
        <LogoutButton />
        <NewChatButton className="flex md:hidden" asChild>
          <Link href={getChatPath()} />
        </NewChatButton>
      </div>
    </header>
  )
}
