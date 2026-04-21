import { Alert, Layout, Spin, Typography } from "antd";
import { startTransition, useEffect, useState } from "react";
import { Route, Routes } from "react-router-dom";
import { debugEnabled, loadPayload } from "./lib/paper";
import { HomePage } from "./pages/HomePage";
import { PaperDetailPage } from "./pages/PaperDetailPage";
import type { SitePayload } from "./types";

const { Header, Content } = Layout;
const { Title, Text } = Typography;

export default function App() {
  const [payload, setPayload] = useState<SitePayload | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    loadPayload()
      .then((result) => {
        if (cancelled) {
          return;
        }
        startTransition(() => {
          setPayload(result);
          setError("");
        });
      })
      .catch((reason: unknown) => {
        if (cancelled) {
          return;
        }
        setError(reason instanceof Error ? reason.message : "加载站点数据失败。");
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <Layout className="app-shell">
      <Header className="app-header">
        <div className="brand-lockup">
          <Text className="brand-label">Translate Paper Forest</Text>
          <Title level={4} className="brand-title">
            论文阅读站
          </Title>
        </div>
      </Header>

      <Content className="app-content">
        {!payload && !error ? (
          <div className="loading-state">
            <Spin size="large" />
          </div>
        ) : null}

        {error ? <Alert type="error" message="站点加载失败" description={error} showIcon /> : null}

        {payload ? (
          <Routes>
            <Route path="/" element={<HomePage payload={payload} />} />
            <Route path="/paper/:paperId" element={<PaperDetailPage payload={payload} debugMode={debugEnabled()} />} />
            <Route path="*" element={<HomePage payload={payload} />} />
          </Routes>
        ) : null}
      </Content>
    </Layout>
  );
}
