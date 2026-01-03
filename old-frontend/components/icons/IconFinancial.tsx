import Image from 'next/image'
import { forwardRef, memo } from 'react'
import { DEFAULT_ICON_SIZE } from './iconConsts'

interface IconFinancialProps {
  size?: number
  className?: string
  style?: React.CSSProperties
}

const IconFinancialBase = (
  { size = DEFAULT_ICON_SIZE, className, style, ...props }: IconFinancialProps,
  ref: React.ForwardedRef<HTMLSpanElement>
) => (
  <span
    ref={ref}
    className={className}
    style={{
      width: size,
      height: size,
      display: 'inline-block',
      ...style
    }}
    role="img"
    {...props}
  >
    <Image
      src="/uppy-logo.png"
      alt="Neurocache Logo"
      width={size}
      height={size}
      style={{ width: '100%', height: '100%', objectFit: 'contain' }}
    />
  </span>
)

export const IconFinancial = memo(forwardRef(IconFinancialBase))
IconFinancial.displayName = 'IconFinancial'
