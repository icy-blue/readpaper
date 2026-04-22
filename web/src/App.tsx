import { Alert, Layout, Spin, Typography } from "antd";
import { startTransition, useEffect, useRef, useState, type CSSProperties } from "react";
import { Route, Routes, useLocation } from "react-router-dom";
import { debugEnabled, loadPayload } from "./lib/paper";
import { HomePage } from "./pages/HomePage";
import { PaperDetailPage } from "./pages/PaperDetailPage";
import type { SiteIndexPayload } from "./types";

const { Header, Content } = Layout;
const { Title, Text } = Typography;

export default function App() {
  const [payload, setPayload] = useState<SiteIndexPayload | null>(null);
  const [error, setError] = useState("");
  const [headerHeight, setHeaderHeight] = useState(72);
  const location = useLocation();
  const headerRef = useRef<HTMLDivElement | null>(null);
  const isHomeConsole = location.pathname === "/";

  useEffect(() => {
    const header = headerRef.current;
    if (!header) {
      return;
    }

    const updateHeaderHeight = () => {
      const nextHeight = Math.round(header.getBoundingClientRect().height);
      if (nextHeight > 0) {
        setHeaderHeight(nextHeight);
      }
    };

    updateHeaderHeight();

    const observer = new ResizeObserver(() => {
      updateHeaderHeight();
    });
    observer.observe(header);

    return () => {
      observer.disconnect();
    };
  }, [isHomeConsole]);

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
    <Layout className={`app-shell${isHomeConsole ? " is-home-console" : ""}`} style={{ "--app-header-height": `${headerHeight}px` } as CSSProperties}>
      <Header ref={headerRef} className={`app-header${isHomeConsole ? " is-home-console" : ""}`}>
        <div className={`app-header-inner${isHomeConsole ? " is-home-console" : ""}`}>
          <div className="brand-lockup">
            <Text className="brand-label">Translate Paper Forest</Text>
            <Title level={4} className="brand-title">
              论文阅读站
            </Title>
          </div>

          {isHomeConsole ? <div id="home-header-slot" className="home-header-slot" /> : null}
        </div>
      </Header>

      <Content className={`app-content${isHomeConsole ? " is-home-console" : ""}`}>
        {!payload && !error ? (
          <div className="loading-state">
            <Spin size="large" />
          </div>
        ) : null}

        {error ? (
          <Alert
            type="error"
            message="站点加载失败"
            description={<span style={{ whiteSpace: "pre-wrap" }}>{error}</span>}
            showIcon
          />
        ) : null}

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
