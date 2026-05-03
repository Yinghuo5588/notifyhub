import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{vue,ts}'],
  theme: {
    extend: {
      colors: {
        bg: 'var(--bg)',
        panel: 'var(--panel)',
        text: 'var(--text)',
        muted: 'var(--muted)',
        brand: 'var(--brand)',
        success: 'var(--success)',
        danger: 'var(--danger)',
        warning: 'var(--warning)',
      },
      borderRadius: {
        app: 'var(--radius)',
      },
      boxShadow: {
        app: 'var(--shadow)',
        soft: 'var(--shadow-soft)',
      },
    },
  },
  plugins: [],
} satisfies Config