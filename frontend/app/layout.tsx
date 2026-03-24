import type { Metadata } from "next";
import {
  JetBrains_Mono,
  Plus_Jakarta_Sans,
  Source_Serif_4,
} from "next/font/google";
import { Toaster } from "sonner";
import { AccessTokenProvider } from "@/components/access-token-provider";
import { ActivationGuard } from "@/components/activation-guard";
import { Auth0Provider } from "@/components/auth0-provider";
import { AuthenticationGuard } from "@/components/authentication-guard";
import { QueryProvider } from "@/components/query-provider";
import { ThemeProvider } from "@/components/theme-provider";

import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://neurocache.vercel.app"),
  title: "Neurocache",
  description: "Neurocache is an AI agent institution for your brain",
};

export const viewport = {
  maximumScale: 1, // Disable auto-zoom on mobile Safari
};

const fontSans = Plus_Jakarta_Sans({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-sans",
});

const fontSerif = Source_Serif_4({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-serif",
});

const fontMono = JetBrains_Mono({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-mono",
});

const LIGHT_THEME_COLOR = "oklch(0.9824 0.0013 286.3757)";
const DARK_THEME_COLOR = "oklch(0.2303 0.0125 264.2926)";
const THEME_COLOR_SCRIPT = `\
(function() {
  var html = document.documentElement;
  var meta = document.querySelector('meta[name="theme-color"]');
  if (!meta) {
    meta = document.createElement('meta');
    meta.setAttribute('name', 'theme-color');
    document.head.appendChild(meta);
  }
  function updateThemeColor() {
    var isDark = html.classList.contains('dark');
    meta.setAttribute('content', isDark ? '${DARK_THEME_COLOR}' : '${LIGHT_THEME_COLOR}');
  }
  var observer = new MutationObserver(updateThemeColor);
  observer.observe(html, { attributes: true, attributeFilter: ['class'] });
  updateThemeColor();
})();`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      className={`${fontSans.variable} ${fontSerif.variable} ${fontMono.variable}`}
      // `next-themes` injects an extra classname to the body element to avoid
      // visual flicker before hydration. Hence the `suppressHydrationWarning`
      // prop is necessary to avoid the React hydration mismatch warning.
      // https://github.com/pacocoursey/next-themes?tab=readme-ov-file#with-app
      lang="en"
      suppressHydrationWarning
    >
      <head>
        <script
          // biome-ignore lint/security/noDangerouslySetInnerHtml: "Required"
          dangerouslySetInnerHTML={{
            __html: THEME_COLOR_SCRIPT,
          }}
        />
      </head>
      <body className="antialiased">
        <QueryProvider>
          <ThemeProvider
            attribute="class"
            defaultTheme="system"
            disableTransitionOnChange
            enableSystem
          >
            <Auth0Provider>
              <AccessTokenProvider>
                <AuthenticationGuard>
                  <ActivationGuard>
                    <Toaster position="top-center" />
                    {children}
                  </ActivationGuard>
                </AuthenticationGuard>
              </AccessTokenProvider>
            </Auth0Provider>
          </ThemeProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
