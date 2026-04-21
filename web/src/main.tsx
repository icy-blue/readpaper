import React from "react";
import ReactDOM from "react-dom/client";
import { HashRouter } from "react-router-dom";
import { ConfigProvider, App as AntApp, theme } from "antd";
import App from "./App";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ConfigProvider
      theme={{
        algorithm: theme.defaultAlgorithm,
        token: {
          colorPrimary: "#24524b",
          colorInfo: "#24524b",
          colorBgBase: "#f4efe4",
          colorTextBase: "#1d2f2b",
          colorBorder: "rgba(36,82,75,0.16)",
          borderRadius: 20,
          fontFamily:
            '"PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif',
          fontFamilyCode: '"SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace',
        },
      }}
    >
      <AntApp>
        <HashRouter>
          <App />
        </HashRouter>
      </AntApp>
    </ConfigProvider>
  </React.StrictMode>
);
