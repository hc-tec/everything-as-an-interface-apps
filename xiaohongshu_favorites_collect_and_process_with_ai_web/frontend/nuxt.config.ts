import tailwindcss from "@tailwindcss/vite";

export default defineNuxtConfig({
  compatibilityDate: "2025-07-15",
  modules: ['shadcn-nuxt'],
  pages: true,
  shadcn: {
    prefix: '',
    componentDir: './app/components/ui'
  },
  devtools: { enabled: true },
  css: ['~/assets/css/main.css'],
  devServer: {
    port: 3001,
  },
  vite: {
    plugins: [
      tailwindcss(),
    ],
  },
});