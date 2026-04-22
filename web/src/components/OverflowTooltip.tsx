import { Tag, Tooltip, Typography } from "antd";
import type { ReactNode } from "react";

const { Paragraph, Text } = Typography;

function truncateValue(value: string, maxChars: number): string {
  return value.length <= maxChars ? value : `${value.slice(0, maxChars - 1).trimEnd()}…`;
}

export function TooltipText({
  text,
  maxChars,
  rows,
  as = "text",
  className,
}: {
  text: string | null | undefined;
  maxChars?: number;
  rows?: number;
  as?: "text" | "paragraph";
  className?: string;
}) {
  const content = (text ?? "").trim();
  if (!content) {
    return null;
  }

  const TypographyComponent = as === "paragraph" ? Paragraph : Text;

  if (typeof maxChars === "number") {
    const truncated = truncateValue(content, maxChars);
    const clipped = truncated !== content;
    const node = (
      <TypographyComponent className={className} style={{ marginBottom: as === "paragraph" ? 0 : undefined }}>
        {truncated}
      </TypographyComponent>
    );

    if (!clipped) {
      return node;
    }

    return (
      <Tooltip title={content} trigger={["hover", "focus"]}>
        <span className="tooltip-trigger" tabIndex={0}>
          {node}
        </span>
      </Tooltip>
    );
  }

  if (as === "paragraph" && rows) {
    return (
      <Paragraph
        className={className}
        ellipsis={{
          rows,
          tooltip: { title: content },
        }}
      >
        {content}
      </Paragraph>
    );
  }

  return (
    <TypographyComponent className={className} style={{ marginBottom: as === "paragraph" ? 0 : undefined }}>
      {content}
    </TypographyComponent>
  );
}

export function TooltipTag({
  label,
  maxChars,
  className,
  icon,
}: {
  label: string | null | undefined;
  maxChars?: number;
  className?: string;
  icon?: ReactNode;
}) {
  const content = (label ?? "").trim();
  if (!content) {
    return null;
  }

  const clipped = typeof maxChars === "number" && content.length > maxChars;
  const display = clipped && maxChars ? truncateValue(content, maxChars) : content;
  const tagNode = (
    <Tag icon={icon} className={className}>
      {display}
    </Tag>
  );

  if (!clipped) {
    return tagNode;
  }

  return (
    <Tooltip title={content} trigger={["hover", "focus"]}>
      <span className="tooltip-trigger tag-tooltip-trigger" tabIndex={0}>
        {tagNode}
      </span>
    </Tooltip>
  );
}

export function OverflowCount({
  items,
  className,
  mode = "text",
  label,
}: {
  items: Array<string | null | undefined>;
  className?: string;
  mode?: "tag" | "text";
  label?: string;
}) {
  const contentItems = items.map((item) => (item ?? "").trim()).filter(Boolean);
  if (!contentItems.length) {
    return null;
  }

  const displayLabel = label ?? `+${contentItems.length}`;
  const node =
    mode === "tag" ? (
      <Tag className={className}>{displayLabel}</Tag>
    ) : (
      <Text className={className}>{displayLabel}</Text>
    );

  return (
    <Tooltip
      title={
        <div className="overflow-tooltip-list">
          {contentItems.map((item, index) => (
            <div key={`${item}-${index}`} className="overflow-tooltip-item">
              {item}
            </div>
          ))}
        </div>
      }
      trigger={["hover", "focus"]}
    >
      <span className="tooltip-trigger" tabIndex={0}>
        {node}
      </span>
    </Tooltip>
  );
}
