/** @type {import('tailwindcss').Config} */
// Ported verbatim from the Google Stitch design (the <script id="tailwind-config">
// block). Colours, spacing, fonts, radii, animations and keyframes are kept
// identical so the exact Tailwind class names used in the mockup keep working.
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // Tokens actually used across the UI are driven by CSS variables so
        // they flip between the dark and light palettes defined in index.css.
        // The "<alpha-value>" placeholder keeps Tailwind's /opacity modifiers
        // (e.g. bg-primary-container/20) working.
        'primary-container': 'rgb(var(--c-primary-container) / <alpha-value>)',
        'on-error-container': 'rgb(var(--c-on-error-container) / <alpha-value>)',
        'on-surface-variant': 'rgb(var(--c-on-surface-variant) / <alpha-value>)',
        primary: 'rgb(var(--c-primary) / <alpha-value>)',
        'on-surface': 'rgb(var(--c-on-surface) / <alpha-value>)',
        'outline-variant': 'rgb(var(--c-outline-variant) / <alpha-value>)',
        error: 'rgb(var(--c-error) / <alpha-value>)',
        'surface-container-low': 'rgb(var(--c-surface-container-low) / <alpha-value>)',
        'surface-container-high': 'rgb(var(--c-surface-container-high) / <alpha-value>)',
        'surface-container-highest': 'rgb(var(--c-surface-container-highest) / <alpha-value>)',
        'surface-container-lowest': 'rgb(var(--c-surface-container-lowest) / <alpha-value>)',
        surface: 'rgb(var(--c-surface) / <alpha-value>)',
        'surface-container': 'rgb(var(--c-surface-container) / <alpha-value>)',
        'on-primary-container': 'rgb(var(--c-on-primary-container) / <alpha-value>)',

        // Remaining Material tokens (not currently referenced by components) —
        // kept static so nothing else changes.
        'on-tertiary-fixed': '#1d1b1b',
        'surface-dim': '#131313',
        'surface-tint': '#ffb3b0',
        tertiary: '#cbc5c5',
        'inverse-on-surface': '#313030',
        'on-primary': '#680010',
        'on-secondary-container': '#e1abaf',
        'secondary-container': '#663e42',
        'tertiary-fixed': '#e8e1e1',
        'primary-fixed-dim': '#ffb3b0',
        background: '#131313',
        'on-background': '#e5e2e1',
        'inverse-primary': '#a93539',
        'on-secondary': '#4a262a',
        'surface-bright': '#3a3939',
        'surface-variant': '#353534',
        outline: '#a68a89',
        'on-primary-fixed-variant': '#891c24',
        'secondary-fixed': '#ffdadc',
        'on-secondary-fixed': '#311116',
        secondary: '#f0b8bc',
        'secondary-fixed-dim': '#f0b8bc',
        'inverse-surface': '#e5e2e1',
        'on-tertiary': '#333030',
        'on-error': '#690005',
        'primary-fixed': '#ffdad8',
        'tertiary-container': '#484444',
        'on-tertiary-container': '#b7b1b1',
        'tertiary-fixed-dim': '#cbc5c5',
        'on-tertiary-fixed-variant': '#494646',
        'on-primary-fixed': '#410006',
        'on-secondary-fixed-variant': '#643c3f',
        'error-container': '#93000a',
      },
      borderRadius: {
        DEFAULT: '0.125rem',
        lg: '0.25rem',
        xl: '0.5rem',
        full: '0.75rem',
        chat: '1.75rem',
      },
      spacing: {
        'container-padding-desktop': '40px',
        'section-gap': '80px',
        base: '8px',
        gutter: '24px',
        'container-padding-mobile': '20px',
        xl: '32px',
        lg: '24px',
        md: '16px',
        'sidebar-width': '320px',
        'sidebar-collapsed': '80px',
        'max-content-width': '1200px',
        xs: '4px',
        sm: '8px',
      },
      fontFamily: {
        'label-caps': ['JetBrains Mono'],
        'headline-lg': ['Geist'],
        'headline-lg-mobile': ['Geist'],
        'body-sm': ['Geist'],
        'headline-xl': ['Geist'],
        'body-md': ['Geist'],
        'code-md': ['JetBrains Mono'],
      },
      fontSize: {
        'label-caps': ['12px', { lineHeight: '16px', letterSpacing: '0.05em', fontWeight: '600' }],
        'headline-lg': ['32px', { lineHeight: '40px', letterSpacing: '-0.01em', fontWeight: '600' }],
        'headline-lg-mobile': ['24px', { lineHeight: '32px', fontWeight: '600' }],
        'body-sm': ['14px', { lineHeight: '20px', fontWeight: '400' }],
        'headline-xl': ['40px', { lineHeight: '48px', letterSpacing: '-0.02em', fontWeight: '700' }],
        'body-md': ['16px', { lineHeight: '24px', fontWeight: '400' }],
        'code-md': ['14px', { lineHeight: '22px', fontWeight: '450' }],
      },
      animation: {
        shimmer: 'shimmer 2s infinite linear',
        'slide-up-fade': 'slideUpFade 0.4s ease-out forwards',
        'loading-beam': 'loadingBeam 2.5s infinite',
      },
      keyframes: {
        shimmer: {
          '0%': { 'background-position': '-1000px 0' },
          '100%': { 'background-position': '1000px 0' },
        },
        slideUpFade: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        loadingBeam: {
          '0%': { left: '-100%' },
          '50%': { left: '100%' },
          '100%': { left: '100%' },
        },
      },
    },
  },
  plugins: [],
}
