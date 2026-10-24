import { fileURLToPath, URL } from "node:url";
import path from "node:path";

import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

const rootDir = path.dirname(fileURLToPath(import.meta.url));
const tokenFile = path.resolve(rootDir, "src/styles/tokens.less").replace(/\\/g, "/");
const mixinFile = path.resolve(rootDir, "src/styles/mixins.less").replace(/\\/g, "/");

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  // 构建产物直接交给 Python 的静态服务器托管：
  //   /            -> static/dist/index.html
  //   /assets/*    -> static/dist/assets/*
  build: {
    outDir: "../static/dist",
    emptyOutDir: true,
    sourcemap: false,
    chunkSizeWarningLimit: 900,
  },
  server: {
    port: 5173,
    strictPort: false,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8765",
        changeOrigin: false,
      },
    },
  },
  css: {
    preprocessorOptions: {
      less: {
        // 每个 <style lang="less"> 都可以直接用 @space-4、.panel() 等变量和 mixin
        additionalData: `@import "${tokenFile}";\n@import "${mixinFile}";\n`,
      },
    },
  },
});
