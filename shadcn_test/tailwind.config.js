/** @type {import('tailwindcss').Config} */
export default {
    darkMode: ["class"],
    content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
  	extend: {
  		fontFamily: {
  			sans: [
  				'IranYekan',
  				'tahoma',
  				'sans-serif'
  			]
  		},
  		borderRadius: {
  			lg: 'var(--radius)',
  			md: 'calc(var(--radius) - 2px)',
  			sm: 'calc(var(--radius) - 4px)'
  		},
  		colors: {
  			background: 'var(--background)',
  			foreground: 'var(--foreground)',
  			card: {
  				DEFAULT: 'var(--card)',
  				foreground: 'var(--card-foreground)'
  			},
  			popover: {
  				DEFAULT: 'var(--popover)',
  				foreground: 'var(--popover-foreground)'
  			},
  			primary: {
  				DEFAULT: ({ opacityValue }) => opacityValue !== undefined ? `oklch(var(--primary-oklch) / ${opacityValue})` : 'var(--primary)',
  				foreground: ({ opacityValue }) => opacityValue !== undefined ? `oklch(var(--primary-foreground-oklch) / ${opacityValue})` : 'var(--primary-foreground)'
  			},
  			secondary: {
  				DEFAULT: ({ opacityValue }) => opacityValue !== undefined ? `oklch(var(--secondary-oklch) / ${opacityValue})` : 'var(--secondary)',
  				foreground: ({ opacityValue }) => opacityValue !== undefined ? `oklch(var(--secondary-foreground-oklch) / ${opacityValue})` : 'var(--secondary-foreground)'
  			},
  			muted: {
  				DEFAULT: 'var(--muted)',
  				foreground: 'var(--muted-foreground)'
  			},
  			accent: {
  				DEFAULT: 'var(--accent)',
  				foreground: 'var(--accent-foreground)'
  			},
  			destructive: {
  				DEFAULT: ({ opacityValue }) => opacityValue !== undefined ? `oklch(var(--destructive-oklch) / ${opacityValue})` : 'var(--destructive)',
  				foreground: 'var(--destructive-foreground)'
  			},
  			border: 'var(--border)',
  			input: ({ opacityValue }) => opacityValue !== undefined ? `oklch(var(--input-oklch) / ${opacityValue})` : 'var(--input)',
  			ring: ({ opacityValue }) => opacityValue !== undefined ? `oklch(var(--ring-oklch) / ${opacityValue})` : 'var(--ring)',
  			chart: {
  				'1': 'var(--chart-1)',
  				'2': 'var(--chart-2)',
  				'3': 'var(--chart-3)',
  				'4': 'var(--chart-4)',
  				'5': 'var(--chart-5)'
  			}
  		}
  	}
  },
  plugins: [],
}
