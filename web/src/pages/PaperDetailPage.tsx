import { Button, Typography } from "antd";
import { ArrowLeftOutlined } from "@ant-design/icons";
import { useNavigate, useParams } from "react-router-dom";
import { PaperDetailWorkspace } from "../components/PaperDetailWorkspace";
import type { SiteIndexPayload } from "../types";

const { Title, Paragraph } = Typography;

export function PaperDetailPage({ payload, debugMode }: { payload: SiteIndexPayload; debugMode: boolean }) {
  const navigate = useNavigate();
  const params = useParams();
  const paperId = params.paperId ?? "";

  if (!paperId) {
    return (
      <div className="detail-state-panel">
        <Title level={4}>缺少论文 ID</Title>
        <Paragraph>当前链接没有提供可加载的论文标识。</Paragraph>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate("/")}>
          返回首页
        </Button>
      </div>
    );
  }

  return (
    <div className="page-stack detail-page-shell">
      <div className="detail-page-topbar">
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate("/")}>
          返回首页
        </Button>
      </div>

      <PaperDetailWorkspace
        paperId={paperId}
        payload={payload}
        debugMode={debugMode}
        className="detail-page-workspace"
      />
    </div>
  );
}
