import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8787",
        changeOrigin: true,
      },
      "/missions": {
        target: "http://127.0.0.1:8787",
        changeOrigin: true,
      },
      "/approvals": {
        target: "http://127.0.0.1:8787",
        changeOrigin: true,
      },
      "/integrations": {
        target: "http://127.0.0.1:8787",
        changeOrigin: true,
      },
      "/auth": {
        target: "http://127.0.0.1:8787",
        changeOrigin: true,
        configure(proxy) {
          proxy.on("proxyRes", (proxyRes) => {
            const cookies = proxyRes.headers["set-cookie"];
            if (!cookies) return;
            proxyRes.headers["set-cookie"] = cookies.map((c) =>
              c.replace(/;\s*Domain=[^;]*/gi, "")
            );
          });
        },
      },
    },
  },
});
